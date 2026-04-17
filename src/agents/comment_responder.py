"""Comment Responder Agent for replying to blog comments on DEV.to."""

import logging
import asyncio
import re
from datetime import datetime
from typing import Any, List, Optional
import httpx

from src.config import Config, get_config
from src.logging_config import get_logger
from src.models.data_models import Comment, CommentReplyResult
from src.memory.memory_system import MemorySystem
from src.utils.retry import retry_with_backoff

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a knowledgeable, senior software engineer and the author of a technical blog \
on DEV.to. You reply to reader comments personally — as yourself, not as an AI assistant.

YOUR REPLY STYLE:
- Conversational yet technically precise. Match the reader's expertise level.
- Acknowledge their point genuinely before adding your own view.
- If they raised a valid gap in your article, admit it honestly and expand on it.
- If they asked a question, answer it directly and concisely — no fluff.
- If they gave positive feedback, thank them briefly and add one useful extra insight.
- Never be defensive. Treat pushback as valuable engineering dialogue.
- Do NOT use hashtags, emojis, marketing language, or filler phrases like \
  "Great question!" or "Thanks for reaching out!".
- Keep replies to 2–5 sentences unless a technical explanation genuinely requires more.
- Write in plain Markdown (bold/italic/code blocks are fine, no headers).
- Do NOT start with "Hi" or address the person by name unless it feels very natural.
- Do NOT mention that you are an AI.
"""

def _build_user_prompt(
    article_title: str,
    article_excerpt: str,
    comment_text: str,
    commenter_name: str,
    technical_context: str = "",
) -> str:
    """Build the user-turn prompt for Ollama."""
    return f"""\
ARTICLE TITLE:
{article_title}

ARTICLE EXCERPT (first ~2 000 chars):
\"\"\"
{article_excerpt}
\"\"\"

COMMENTER: {commenter_name}

THEIR COMMENT:
\"\"\"
{comment_text}
\"\"\"

TECHNICAL CONTEXT (related info from knowledge base):
\"\"\"
{technical_context or "No specific technical context found in memory."}
\"\"\"

---
Classify the comment (internally) as one of:
  [QUESTION]   — they asked something specific
  [PUSHBACK]   — they disagreed or pointed out a gap
  [PRAISE]     — positive-only, no question
  [BUG_REPORT] — they found a factual/technical error

Then write your reply following the style rules above.
Output ONLY the reply text — no preamble, no classification label.
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class CommentResponderAgent:
    """
    Agent that monitors and replies to comments on DEV.to articles.

    Uses the configured Ollama model to generate helpful, polite,
    and contextually accurate responses to reader comments.
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize the Comment Responder Agent.

        Args:
            config: Application configuration.
        """
        self.config = config or get_config()
        self.devto_api_token = self.config.devto_api_token

        if not self.devto_api_token:
            logger.warning(
                "DEV.to API token not configured. CommentResponderAgent will be inactive.",
                extra={"agent": "CommentResponderAgent"},
            )
            self.client = None
        else:
            self.client = httpx.AsyncClient(
                base_url="https://dev.to/api",
                headers={
                    "api-key": self.devto_api_token,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

        self.memory_system = MemorySystem(config=self.config)
        self.username = None
        self.user_id  = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Initialize memory system and fetch user info."""
        await self.memory_system.initialize()
        if self.client:
            await self._fetch_user_info()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            logger.info(
                "CommentResponderAgent client closed",
                extra={"agent": "CommentResponderAgent"},
            )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self) -> List[CommentReplyResult]:
        """
        Run the comment monitoring and response loop.

        Returns:
            List of results for each reply attempt.
        """
        if not self.client:
            return []

        logger.info(
            "Starting comment response loop...",
            extra={"agent": "CommentResponderAgent"},
        )
        results: List[CommentReplyResult] = []

        try:
            articles = await self._fetch_user_articles()
            logger.info(
                f"Found {len(articles)} articles to check for comments.",
                extra={"agent": "CommentResponderAgent"},
            )

            for article in articles:
                article_id    = str(article.get("id"))
                article_title = article.get("title", "")
                article_body  = article.get("body_markdown", "")

                comments     = await self._fetch_article_comments(article_id)
                flat_comments = self._flatten_comments(comments)

                for comment_data in flat_comments:
                    comment_id = str(comment_data.get("id_code"))

                    if not await self._should_reply(comment_data):
                        continue

                    logger.info(
                        f"Generating reply for comment {comment_id} on '{article_title}'",
                        extra={"agent": "CommentResponderAgent"},
                    )

                    # Fetch full article body if the listing API gave only a snippet
                    if not article_body or len(article_body) < 100:
                        article_full = await self._fetch_article_details(article_id)
                        article_body = article_full.get("body_markdown", "")

                    result = await self._process_single_comment(
                        article_title, article_body, comment_data
                    )
                    results.append(result)

                    if result.success:
                        await self.memory_system.mark_comment_replied(comment_id)
                        logger.info(
                            f"Successfully replied to comment {comment_id}",
                            extra={"agent": "CommentResponderAgent"},
                        )

        except Exception as e:
            logger.error(
                f"Comment response loop failed: {e}",
                extra={"agent": "CommentResponderAgent"},
                exc_info=True,
            )

        return results

    # ------------------------------------------------------------------
    # DEV.to API helpers
    # ------------------------------------------------------------------

    async def _fetch_user_info(self) -> None:
        """Fetch the authenticated user's information from DEV.to."""
        try:
            response = await self.client.get("/users/me")
            response.raise_for_status()
            data = response.json()
            self.username = data.get("username")
            self.user_id  = data.get("id")
            logger.info(
                f"Initialized CommentResponderAgent for user: {self.username} (ID: {self.user_id})",
                extra={"agent": "CommentResponderAgent"},
            )
        except Exception as e:
            logger.error(
                f"Failed to fetch user info from DEV.to: {e}",
                extra={"agent": "CommentResponderAgent"},
            )

    async def _fetch_user_articles(self) -> List[dict]:
        response = await self.client.get("/articles/me")
        response.raise_for_status()
        return response.json()

    async def _fetch_article_details(self, article_id: str) -> dict:
        response = await self.client.get(f"/articles/{article_id}")
        response.raise_for_status()
        return response.json()

    async def _fetch_article_comments(self, article_id: str) -> List[dict]:
        response = await self.client.get("/comments", params={"a_id": article_id})
        response.raise_for_status()
        return response.json()

    def _flatten_comments(self, comments: List[dict]) -> List[dict]:
        """Recursively flatten threaded comments into a single list."""
        flat: List[dict] = []
        for c in comments:
            flat.append(c)
            if c.get("children"):
                flat.extend(self._flatten_comments(c["children"]))
        return flat

    async def _should_reply(self, comment: dict) -> bool:
        """Determine if the agent should reply to this comment."""
        comment_id       = str(comment.get("id_code"))
        comment_username = comment.get("user", {}).get("username")

        if comment_username == self.username:   # never reply to own comments
            return False

        if await self.memory_system.is_comment_replied(comment_id):
            return False

        return True

    async def _post_reply(self, article_id: int, parent_id: str, body: str) -> dict:
        """Post the reply to DEV.to."""
        payload = {
            "comment": {
                "body_markdown": body,
                "commentable_id": article_id,
                "commentable_type": "Article",
                "parent_id": parent_id,
            }
        }
        response = await self.client.post("/comments", json=payload)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Comment processing
    # ------------------------------------------------------------------

    async def _process_single_comment(
        self,
        article_title: str,
        article_body: str,
        comment: dict,
    ) -> CommentReplyResult:
        """Generate and post a reply to a single comment."""
        comment_id   = str(comment.get("id_code"))
        comment_body = comment.get("body_html", "")

        # Strip HTML tags for the LLM
        comment_text = re.sub(r"<[^<]+?>", "", comment_body).strip()

        try:
            reply_text = await self._generate_ollama_reply(
                article_title=article_title,
                article_body=article_body,
                comment_text=comment_text,
                user_info=comment.get("user", {}),
            )

            reply_data = await self._post_reply(
                comment["article_id"], comment_id, reply_text
            )

            return CommentReplyResult(
                success=True,
                comment_id=comment_id,
                reply_id=str(reply_data.get("id_code")),
                error=None,
                replied_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(
                f"Failed to process comment {comment_id}: {e}",
                extra={"agent": "CommentResponderAgent"},
            )
            return CommentReplyResult(
                success=False,
                comment_id=comment_id,
                reply_id=None,
                error=str(e),
                replied_at=datetime.utcnow(),
            )

    # ------------------------------------------------------------------
    # LLM — Ollama
    # ------------------------------------------------------------------

    async def _generate_ollama_reply(
        self,
        article_title: str,
        article_body: str,
        comment_text: str,
        user_info: dict,
    ) -> str:
        """
        Call local Ollama API to generate a reply.
        """
        commenter_name = user_info.get("name") or user_info.get("username") or "Reader"

        # Trim article body to keep the request within a sensible token budget
        article_excerpt = article_body[:2000].strip()

        # 1. Retrieve technical context from the knowledge base (crawled data, past blogs)
        context_entries = await self.memory_system.search(comment_text, limit=3)
        technical_context = ""
        if context_entries:
            context_blocks = []
            for entry in context_entries:
                title = entry.get("content", {}).get("title", "Untitled")
                snippet = entry.get("content", {}).get("summary", "") or entry.get("content", {}).get("body", "")[:500]
                context_blocks.append(f"Source: {title}\nContent: {snippet}")
            technical_context = "\n\n".join(context_blocks)

        # 2. Build the full prompt with retrieved context
        prompt = f"{SYSTEM_PROMPT}\n\n" + _build_user_prompt(
            article_title=article_title,
            article_excerpt=article_excerpt,
            comment_text=comment_text,
            commenter_name=commenter_name,
            technical_context=technical_context
        )

        payload = {
            "model": self.config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "num_predict": 512
            }
        }

        headers = {"Content-Type": "application/json"}
        if self.config.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"
            
        async with httpx.AsyncClient(timeout=self.config.ollama_timeout) as client:
            response = await client.post(
                f"{self.config.ollama_endpoint.rstrip('/')}/api/generate",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            reply = data.get("response", "").strip()

        # Strip surrounding quotes if the model added them
        if reply.startswith('"') and reply.endswith('"'):
            reply = reply[1:-1].strip()

        if not reply:
            raise ValueError("Ollama returned an empty reply.")

        logger.debug(
            f"Ollama reply generated ({len(reply)} chars)",
            extra={"agent": "CommentResponderAgent"},
        )
        return reply