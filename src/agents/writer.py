"""Writer Agent for generating original blog posts from source content."""

import re
import logging
from datetime import datetime
from typing import Any

import httpx

from src.config import Config, get_config
from src.logging_config import get_logger
from src.models.data_models import ContentItem, BlogPost
from src.utils.retry import retry_with_backoff, RetryError
from src.utils.diagram_generator import DiagramGenerator

logger = get_logger(__name__)


class GenerationError(Exception):
    """Raised when blog post generation fails after retries."""
    pass


class WriterAgent:
    """
    Agent that generates original blog posts from source content.
    
    Uses Ollama with Gemma model to generate original text inspired by
    but not copying the source material.
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize the Writer Agent.
        
        Args:
            config: Application configuration. If None, uses global config.
        """
        self.config = config or get_config()
        self.ollama_endpoint = self.config.ollama_endpoint
        self.model = self.config.ollama_model
        self.temperature = self.config.ollama_temperature
        self.max_tokens = self.config.ollama_max_tokens
        self.timeout = self.config.ollama_timeout
        
        # Build headers for API authentication
        headers = {"Content-Type": "application/json"}
        if self.config.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.ollama_endpoint.rstrip('/'),
            timeout=self.timeout,
            headers=headers
        )
        
        logger.info(
            "WriterAgent initialized",
            extra={
                "agent": "WriterAgent",
                "endpoint": self.ollama_endpoint,
                "model": self.model,
                "api_key_configured": bool(self.config.ollama_api_key)
            }
        )

    async def generate(self, content: ContentItem) -> BlogPost:
        """
        Generate original blog post from source content.
        
        Args:
            content: Source material
        
        Returns:
            Generated blog post
        
        Raises:
            GenerationError: If generation fails after retries
        """
        try:
            logger.info(
                f"Generating blog post from: {content.title}",
                extra={"agent": "WriterAgent", "source_url": content.url}
            )
            
            # Generate content with retry logic
            response = await retry_with_backoff(
                self._call_ollama,
                content,
                max_retries=self.config.max_retry_attempts,
                base_delay=self.config.retry_base_delay,
                max_delay=self.config.retry_max_delay,
                retry_exceptions=(httpx.HTTPError, TimeoutError, ConnectionError)
            )
            
            # Parse response into BlogPost (LLM already created diagrams)
            blog_post = self._parse_response(response, content.url)
            
            # Validate word count
            word_count = self._count_words(blog_post.content)
            blog_post.word_count = word_count
            
            logger.info(
                f"Blog post generated: {blog_post.title} ({word_count} words)",
                extra={"agent": "WriterAgent", "word_count": word_count}
            )
            
            return blog_post
            
        except RetryError as e:
            logger.error(f"Generation failed after retries: {e}", extra={"agent": "WriterAgent"})
            raise GenerationError(f"Failed to generate blog post: {e}") from e
        except Exception as e:
            logger.error(f"Generation failed: {e}", extra={"agent": "WriterAgent"})
            raise GenerationError(f"Failed to generate blog post: {e}") from e

    async def _call_ollama(self, content: ContentItem) -> str:
        """
        Call Ollama API to generate content.
        
        Args:
            content: Source ContentItem
        
        Returns:
            Raw response text
        
        Raises:
            httpx.HTTPError: On HTTP errors
        """
        prompt = self._build_generation_prompt(content)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get("response", "")

    def _build_generation_prompt(self, content: ContentItem) -> str:
        """
        Build the generation prompt for Ollama.

        Args:
            content: Source ContentItem

        Returns:
            Prompt string
        """
        prompt = f"""You are a world-class technical writer in the style of ByteByteGo, the best posts on
Medium, and top Substack engineering newsletters. You write posts that engineers
genuinely want to read, bookmark, and share — not dry documentation.

════════════════════════════════════════
VOICE & STYLE  (non-negotiable)
════════════════════════════════════════
• Conversational but authoritative — write like a senior engineer explaining
  something over coffee, not like a textbook or a press release.
• Short sentences. Varied rhythm. No walls of text.
• Use "you" and "we" to pull the reader in.
• Open loops early — make the reader NEED to know what comes next.
• Concrete always beats abstract. Real numbers, real system names, real tradeoffs.
• Analogies for hard concepts: a great analogy is worth 10 paragraphs.
• Zero filler phrases: never write "In this article", "It is worth noting",
  "As we can see", "In conclusion" — cut them all.
• Opinions are welcome. Hedge only when genuinely uncertain.

════════════════════════════════════════
HOOK (first 3 sentences — most important)
════════════════════════════════════════
Pick ONE of these proven hook formulas and execute it well:

  PROBLEM HOOK  — Drop the reader into a painful, relatable situation.
    Example: "Your service is down. Latency spiked to 30 s. You grep the logs
    and find... nothing useful. Here's why that happens and how to fix it."

  SURPRISING FACT HOOK — Lead with a counterintuitive stat or claim.
    Example: "Netflix runs on AWS — the very company it competes with for
    streaming customers. That's not a mistake. It's an intentional architecture
    decision worth understanding."

  PROMISE HOOK — Tell the reader exactly what they will be able to DO after
    reading, with specificity.
    Example (Systems): "By the end of this post you'll be able to design a rate-limiter
    that handles 100k req/s and avoid the three mistakes teams make in production."
    Example (AI): "By the end of this post you'll know how to build a multi-agent 
    RAG pipeline that slashes hallucination rates by 40%."

════════════════════════════════════════
CONTENT & TONE
════════════════════════════════════════
You are a Staff-level AI Architect and Distributed Systems Engineer. Your writing is highly technical, authoritative, yet incredibly clear (think ByteByteGo or pragmatic engineer).

Adapt your focus dynamically based on the topic. You are an expert in BOTH:
  - Agentic AI, Generative AI infrastructure, ML workflows, and LLMs.
  - Scalability, distributed systems, system architecture, and performance.

Structure the post organically based on the given topic. You are not bound to a rigid structure, but generally include:
  - INTRODUCTION — Hook the reader. What hard problem is solved here?
  - THE CHALLENGE — Why is this difficult (e.g., at scale, or due to AI hallucinations)?
  - ARCHITECTURE / ALGORITHM / WORKFLOW — Deep dive into the core concepts, ML/AI logic, or System architecture.
  - TRADE-OFFS & CONSIDERATIONS — Discuss bottlenecks, latency, prompt-costs, pros/cons, or scaling techniques.
  - KEY TAKEAWAYS — 3-5 punchy bullet points. Scannable. Actionable.

════════════════════════════════════════
TARGET LENGTH
════════════════════════════════════════
Write 1,200–1,500 words of prose (not counting Mermaid code blocks or the
JSON wrapper). This is non-negotiable — short posts will be rejected and
regenerated. Every section must be fully developed, not just a sentence or two.

DIAGRAM REQUIREMENTS (AGENT'S DISCRETION)
════════════════════════════════════════
You must INTELLIGENTLY decide how many diagrams to create, what types of diagrams are best suited for the topic, and where to place them organically. 
Aim for at least 1-3 diagrams, but you decide the exact number based on what makes the article most instructive.

Available types — you have the full power of Mermaid.js. Pick whatever fits the content perfectly:
  - Architecture / Systems : graph TB, graph TD (Flowchart)
  - Time & Schedules     : gantt, timeline
  - Brainstorming/Concepts: mindmap (\`\`\`mermaid mindmap...)
  - Proportional Data    : pie (\`\`\`mermaid pie...)
  - Git / Branching      : gitGraph
  - Processes / Flow     : sequenceDiagram, stateDiagram-v2, journey
  - Structure / Classes  : classDiagram, erDiagram

Diagram placement heuristic:
  Let the diagrams carry the load. If you need a diagram to explain a complex workflow, architecture, state-machine, or user journey, place it seamlessly in the text and do not write 3 paragraphs repeating what the diagram already shows.
  You decide entirely which diagram type makes the most pedagogical sense!

════════════════════════════════════════
TITLES — write 3 candidates, pick the strongest
════════════════════════════════════════
Strong title formulas:
  • "How [Company] Solved [Hard Problem]"
  • "Why [Common Belief] Is Wrong (And What to Do Instead)"
  • "[Number] Things Every Engineer Should Know About [Topic]"
  • "The [Topic] Cheat Sheet: From Zero to Production"
  • "[Topic] Explained in Plain English"

The title must be specific, benefit-driven, and under 70 characters.

════════════════════════════════════════
WHAT TO AVOID
════════════════════════════════════════
✗ Copying or closely paraphrasing the source material
✗ Generic intros ("In today's fast-paced world...")
✗ Passive voice overuse
✗ Sections longer than ~200 words without a visual or a break
✗ Jargon without explanation
✗ Ending on a weak, vague note ("Hope this was helpful!")

════════════════════════════════════════
OUTPUT FORMAT — respond ONLY with valid JSON, no markdown fences around it
════════════════════════════════════════
{{
  "title": "Your chosen title (strongest of the 3 you drafted)",
  "content": "Full blog post markdown with embedded ```mermaid blocks inline",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

════════════════════════════════════════
SOURCE MATERIAL (inspiration only — do NOT copy)
════════════════════════════════════════
Title   : {content.title}
URL     : {content.url}
Content :
{content.text_content}

Now write the post. Start with the hook. Make every sentence earn its place."""

        return prompt

    def _parse_response(self, response: str, source_url: str) -> BlogPost:
        """
        Parse Ollama response into a BlogPost.
        
        Args:
            response: Raw response text
            source_url: Source URL for tracking
        
        Returns:
            BlogPost instance
        
        Raises:
            GenerationError: If parsing fails
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            
            if json_match:
                import json
                data = json.loads(json_match.group())
                
                title = data.get("title", "Untitled Post")
                content = data.get("content", response)
                tags = data.get("tags", self._generate_tags(title, content))
            else:
                # Fallback: use entire response as content
                title = "Technical Article"
                content = response
                tags = self._generate_tags(title, content)
            
            # Ensure tags are present
            if not tags:
                tags = self._generate_tags(title, content)
            
            return BlogPost(
                title=title,
                content=content,
                tags=tags,
                word_count=0,  # Will be calculated later
                source_url=source_url,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse JSON response, using fallback: {e}")
            # Fallback: create basic blog post
            return BlogPost(
                title="Technical Article",
                content=response,
                tags=self._generate_tags("Technical Article", response),
                word_count=0,
                source_url=source_url,
                generated_at=datetime.utcnow()
            )

    def _count_words(self, text: str) -> int:
        """
        Count words in text.
        
        Args:
            text: Text to count words in
        
        Returns:
            Word count
        """
        # Simple word count - split by whitespace
        words = text.split()
        return len(words)

    def _generate_tags(self, title: str, content: str) -> list[str]:
        """
        Generate relevant tags from content.
        
        Args:
            title: Blog post title
            content: Blog post content
        
        Returns:
            List of tag strings
        """
        # Simple tag extraction based on common technical terms
        common_tags = [
            "technology", "programming", "software", "architecture",
            "systems", "design", "engineering", "development",
            "backend", "frontend", "devops", "cloud", "machine Learning",
            "Artificial Intelligent", "Generative AI", "Deep Learning",
            "Agentic AI"
        ]
        
        tags = []
        content_lower = content.lower()
        title_lower = title.lower()
        
        for tag in common_tags:
            if tag in content_lower or tag in title_lower:
                tags.append(tag)
        
        # Ensure at least some tags
        if not tags:
            tags = ["technology", "article"]
        
        return tags[:5]  # Limit to 5 tags~~

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("WriterAgent client closed")