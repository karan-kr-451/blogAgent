"""Editor Agent for improving blog post quality and readability."""

import re
import logging
from datetime import datetime
from typing import Any

import httpx

from src.config import Config, get_config
from src.logging_config import get_logger
from src.models.data_models import BlogPost, EditedPost
from src.utils.retry import retry_with_backoff, RetryError

logger = get_logger(__name__)


class EditingError(Exception):
    """Raised when blog post editing fails."""
    pass


class EditorAgent:
    """
    Agent that improves readability and quality of blog posts.
    
    Uses LLM via Ollama to check grammar, spelling, punctuation,
    improve sentence structure, and ensure consistent tone.
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize the Editor Agent.
        
        Args:
            config: Application configuration. If None, uses global config.
        """
        self.config = config or get_config()
        self.ollama_endpoint = self.config.ollama_endpoint
        self.model = self.config.ollama_model
        
        # Build headers for API authentication
        headers = {"Content-Type": "application/json"}
        if self.config.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.ollama_endpoint.rstrip('/'),
            timeout=self.config.ollama_timeout,
            headers=headers
        )
        
        logger.info("EditorAgent initialized", extra={"agent": "EditorAgent"})

    async def edit(self, post: BlogPost) -> EditedPost:
        """
        Improve post quality and readability.
        
        Args:
            post: Draft blog post
        
        Returns:
            Edited post with change log
        
        Raises:
            EditingError: If editing fails
        """
        try:
            logger.info(
                f"Editing blog post: {post.title}",
                extra={"agent": "EditorAgent"}
            )
            
            # Call LLM for editing
            response = await retry_with_backoff(
                self._call_ollama_for_edit,
                post,
                max_retries=self.config.max_retry_attempts,
                base_delay=self.config.retry_base_delay,
                max_delay=self.config.retry_max_delay,
                retry_exceptions=(httpx.HTTPError, TimeoutError, ConnectionError)
            )
            
            # Parse the response
            edited_content, changes = self._parse_edit_response(response, post)
            
            # Create edited post
            edited_post = BlogPost(
                title=post.title,
                content=edited_content,
                tags=post.tags,
                word_count=post.word_count,
                source_url=post.source_url,
                generated_at=post.generated_at
            )
            
            logger.info(
                f"Editing complete: {len(changes)} changes made",
                extra={"agent": "EditorAgent"}
            )
            
            return EditedPost(post=edited_post, changes=changes)
            
        except RetryError as e:
            logger.error(f"Editing failed after retries: {e}", extra={"agent": "EditorAgent"})
            raise EditingError(f"Failed to edit blog post: {e}") from e
        except Exception as e:
            logger.error(f"Editing failed: {e}", extra={"agent": "EditorAgent"})
            raise EditingError(f"Failed to edit blog post: {e}") from e

    async def _call_ollama_for_edit(self, post: BlogPost) -> str:
        """
        Call Ollama API for editing.
        
        Args:
            post: Blog post to edit
        
        Returns:
            Edited content with change log
        """
        prompt = self._build_edit_prompt(post)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for conservative edits
                "num_predict": self.config.ollama_max_tokens
            }
        }
        
        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get("response", "")

    def _build_edit_prompt(self, post: BlogPost) -> str:
        """
        Build the editing prompt for Ollama.
        
        Args:
            post: Blog post to edit
        
        Returns:
            Prompt string
        """
        prompt = f"""You are a professional editor. Review and improve this blog post.

EDITING GUIDELINES:
1. Fix grammar, spelling, and punctuation errors
2. Improve sentence structure and paragraph flow
3. Ensure consistent tone and style throughout
4. Maintain technical accuracy - DO NOT change technical facts
5. Preserve all code blocks exactly as they are (don't modify code)
6. Make the content more engaging and readable
7. Keep the same overall structure and meaning

FORMAT YOUR RESPONSE AS:
[EDITED CONTENT]
{{The full edited blog post in markdown format}}

[CHANGES]
- Change 1: Description of what was changed
- Change 2: Description of what was changed
...

BLOG POST TO EDIT:
Title: {post.title}
Content:
{post.content}

Begin editing:"""
        
        return prompt

    def _parse_edit_response(self, response: str, original_post: BlogPost) -> tuple[str, list[str]]:
        """
        Parse editing response into edited content and change log.
        
        Args:
            response: Raw response from LLM
            original_post: Original blog post
        
        Returns:
            Tuple of (edited_content, list_of_changes)
        """
        try:
            # Try to extract edited content and changes
            content = response
            changes = ["Edited for grammar, flow, and readability"]
            
            # Look for [EDITED CONTENT] and [CHANGES] sections
            if "[EDITED CONTENT]" in response and "[CHANGES]" in response:
                parts = response.split("[CHANGES]")
                if len(parts) == 2:
                    content_part = parts[0].replace("[EDITED CONTENT]", "").strip()
                    changes_part = parts[1].strip()
                    
                    # Parse changes (lines starting with -)
                    changes = [
                        line.strip().lstrip('-').strip()
                        for line in changes_part.split('\n')
                        if line.strip().startswith('-')
                    ]
                    
                    content = content_part
            
            # If no structured format, use entire response as edited content
            if not content or content == response:
                content = response
                changes = ["Reviewed for grammar, spelling, and readability"]
            
            # Ensure we have at least one change
            if not changes:
                changes = ["Minor improvements to readability"]
            
            return content, changes
            
        except Exception as e:
            logger.warning(f"Failed to parse edit response, using original: {e}")
            return original_post.content, ["Attempted edit but encountered parsing issues"]

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("EditorAgent client closed")
