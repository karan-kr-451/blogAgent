"""Publisher Agent for publishing blog posts to Medium and local drafts."""

import re
import logging
import base64
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from src.config import Config, get_config
from src.logging_config import get_logger
from src.models.data_models import BlogPost, PublicationResult
from src.memory.memory_system import MemorySystem
from src.utils.retry import retry_with_backoff, RetryError

logger = get_logger(__name__)


class PublicationError(Exception):
    """Raised when blog publication fails."""
    pass


class PublisherAgent:
    """
    Agent that publishes blog posts to Medium via API or saves locally.
    
    Handles authentication, content formatting, and publication
    with retry logic and rate limiting.
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize the Publisher Agent.
        
        Args:
            config: Application configuration. If None, uses global config.
        """
        self.config = config or get_config()
        self.medium_api_token = self.config.medium_api_token
        self.medium_author_id = self.config.medium_author_id
        
        # Local drafts configuration
        self.publish_to_medium = self.config.publish_to_medium
        self.local_drafts_dir = Path(self.config.local_drafts_dir)
        self.local_drafts_dir.mkdir(parents=True, exist_ok=True)
        
        # Medium API client (only if token is configured)
        if self.medium_api_token and self.medium_api_token != "your_medium_api_token_here":
            self.client = httpx.AsyncClient(
                base_url="https://api.medium.com/v1",
                headers={
                    "Authorization": f"Bearer {self.medium_api_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=30.0
            )
            logger.info("Medium API client initialized", extra={"agent": "PublisherAgent"})
        else:
            self.client = None
            logger.info("Medium API not configured, using local drafts only", extra={"agent": "PublisherAgent"})
        
        self.memory_system = MemorySystem(config=self.config)
        
        logger.info(
            "PublisherAgent initialized",
            extra={
                "agent": "PublisherAgent",
                "publish_to_medium": self.publish_to_medium,
                "local_drafts_dir": str(self.local_drafts_dir),
                "medium_configured": self.client is not None
            }
        )

    async def initialize(self) -> None:
        """Initialize the memory system for rate limiting."""
        await self.memory_system.initialize()

    async def publish(self, post: BlogPost) -> PublicationResult:
        """
        Publish blog post - save locally and optionally to Medium or DEV.to.

        Args:
            post: Approved blog post

        Returns:
            Publication result with URL

        Raises:
            PublicationError: If publication fails after retries
        """
        try:
            logger.info(
                f"Publishing blog post: {post.title}",
                extra={"agent": "PublisherAgent"}
            )

            # Always save local draft first
            local_path = await self._save_local_draft(post)

            # Try DEV.to first (simpler, accepts markdown directly)
            if self.config.publish_to_devto and self.config.devto_api_token:
                logger.info("Publishing to DEV.to...", extra={"agent": "PublisherAgent"})
                
                # Publish to DEV.to with retry logic
                devto_result = await retry_with_backoff(
                    self._call_devto_api,
                    post,
                    max_retries=self.config.max_retry_attempts,
                    base_delay=self.config.retry_base_delay,
                    max_delay=self.config.retry_max_delay,
                    retry_exceptions=(httpx.HTTPError, TimeoutError, ConnectionError)
                )

                # Update publication timestamp
                await self.memory_system.update_publication_timestamp()

                logger.info(
                    f"Published to DEV.to: {devto_result.post_url}",
                    extra={"agent": "PublisherAgent", "url": devto_result.post_url}
                )

                return devto_result

            # Try Medium if DEV.to not configured
            if self.publish_to_medium and self.client is not None:
                # Check if we can publish today (rate limit)
                if not await self.can_publish_today():
                    logger.warning(
                        "Daily Medium publication limit reached, saved as local draft only",
                        extra={"agent": "PublisherAgent"}
                    )
                    return PublicationResult(
                        success=True,
                        post_url=local_path,
                        error=None,
                        published_at=datetime.utcnow()
                    )

                # Get author ID if not set
                if not self.medium_author_id:
                    self.medium_author_id = await self._get_author_id()

                # Publish to Medium with retry logic
                medium_result = await retry_with_backoff(
                    self._call_medium_api,
                    post,
                    max_retries=self.config.max_retry_attempts,
                    base_delay=self.config.retry_base_delay,
                    max_delay=self.config.retry_max_delay,
                    retry_exceptions=(httpx.HTTPError, TimeoutError, ConnectionError)
                )

                # Update publication timestamp
                await self.memory_system.update_publication_timestamp()

                logger.info(
                    f"Published to Medium: {medium_result.post_url}",
                    extra={"agent": "PublisherAgent", "url": medium_result.post_url}
                )

                return medium_result
            else:
                # Local draft only
                logger.info(
                    f"Saved as local draft: {local_path}",
                    extra={"agent": "PublisherAgent", "path": local_path}
                )

                return PublicationResult(
                    success=True,
                    post_url=local_path,
                    error=None,
                    published_at=datetime.utcnow()
                )

        except RetryError as e:
            logger.error(f"Publication failed after retries: {e}", extra={"agent": "PublisherAgent"})
            raise PublicationError(f"Failed to publish blog post: {e}") from e
        except PublicationError:
            raise
        except Exception as e:
            logger.error(f"Publication failed: {e}", extra={"agent": "PublisherAgent"})
            raise PublicationError(f"Failed to publish blog post: {e}") from e

    def _mermaid_to_image_url(self, mermaid_code: str) -> str:
        """
        Convert Mermaid diagram code to a rendered image URL using mermaid.ink.
        
        mermaid.ink is a free service that renders Mermaid diagrams as images.
        Format: https://mermaid.ink/img/{base64_encoded_mermaid_code}
        
        Args:
            mermaid_code: Raw Mermaid diagram code
            
        Returns:
            URL string for the rendered diagram image
        """
        # Prepend a vibrant, colorful theme configuration to the graph code
        vibrant_theme = (
            "%%{init: {'theme': 'base', 'themeVariables': { "
            "'primaryColor': '#ff9f1c', "
            "'secondaryColor': '#2ec4b6', "
            "'tertiaryColor': '#e71d36', "
            "'primaryBorderColor': '#011627', "
            "'lineColor': '#011627', "
            "'fontFamily': 'Inter, sans-serif'}}}%%\n"
        )
        
        # Only inject if a theme isn't already specified
        if "%%{init" not in mermaid_code:
            mermaid_code = vibrant_theme + mermaid_code.strip()

        # Encode the mermaid code to base64
        encoded = base64.urlsafe_b64encode(mermaid_code.strip().encode('utf-8')).decode('utf-8')
        # Add a white background so text remains visible in DEV.to's dark mode
        return f"https://mermaid.ink/img/{encoded}?bgColor=!white"

    def _prepare_devto_body(self, post: BlogPost) -> str:
        """
        Prepare body_markdown for DEV.to.
        
        DEV.to auto-generates h1 from the title field, so we must:
        1. Strip any leading '# Title' heading (avoids duplicate h1)
        2. Strip metadata lines (Source, Generated, Word Count, Tags)
        3. Strip the agent footer
        4. Convert ```mermaid blocks to rendered images (DEV.to doesn't render Mermaid)
        5. Use ## for top-level sections (DEV.to guideline)
        """
        body = post.content

        # First: Convert ```mermaid code blocks to mermaid.ink image URLs
        # DEV.to does NOT render Mermaid natively — it shows raw code
        mermaid_pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)
        
        def replace_mermaid(match):
            mermaid_code = match.group(1)
            image_url = self._mermaid_to_image_url(mermaid_code)
            # Use descriptive alt text from the diagram type
            diagram_type = "diagram"
            if mermaid_code.strip().startswith('graph'):
                diagram_type = "architecture diagram"
            elif mermaid_code.strip().startswith('sequenceDiagram'):
                diagram_type = "sequence diagram"
            elif mermaid_code.strip().startswith('flowchart'):
                diagram_type = "flowchart"
            elif mermaid_code.strip().startswith('classDiagram'):
                diagram_type = "class diagram"
            elif mermaid_code.strip().startswith('stateDiagram'):
                diagram_type = "state diagram"
            return f"![{diagram_type}]({image_url})"
        
        body = mermaid_pattern.sub(replace_mermaid, body)

        # Second: Convert LaTeX math to DEV.to KaTeX Liquid tags
        # Block math: $$ ... $$ -> {% katex %} ... {% endkatex %}
        block_math_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
        body = block_math_pattern.sub(r'{% katex %}\n\1\n{% endkatex %}', body)
        
        # Inline math: $ ... $ -> {% katex inline %} ... {% endkatex %}
        # Use negative lookbehind/lookahead to avoid matching prices like $10
        inline_math_pattern = re.compile(r'(?<!\$)\$([^$\n]+?)\$(?!\$)')
        body = inline_math_pattern.sub(r'{% katex inline %}\1{% endkatex %}', body)

        # Strip leading '# Title' line if it matches the post title
        lines = body.split('\n')
        cleaned_lines = []
        skip_metadata = True  # Skip metadata block at the top
        
        for line in lines:
            stripped = line.strip()
            
            # Skip the duplicate title heading
            if stripped.startswith('# ') and stripped[2:].strip() == post.title.strip():
                continue
            
            # Skip metadata lines at the top (Source, Generated, Word Count, Tags)
            if skip_metadata:
                if stripped.startswith('**Source:**') or \
                   stripped.startswith('**Generated:**') or \
                   stripped.startswith('**Word Count:**') or \
                   stripped.startswith('**Tags:**'):
                    continue
                if stripped == '---' and not cleaned_lines:
                    continue
                if stripped == '':
                    continue
                # Once we hit real content, stop skipping
                skip_metadata = False
            
            # Skip the agent footer
            if stripped == '*This post was generated by the Autonomous Blog Agent*':
                continue
            if stripped == '*Includes architecture diagrams and visual examples*':
                continue
            
            cleaned_lines.append(line)
        
        body = '\n'.join(cleaned_lines).strip()
        
        # Ensure there's no trailing ---
        if body.endswith('---'):
            body = body[:-3].strip()
        
        return body

    async def _call_devto_api(self, post: BlogPost) -> PublicationResult:
        """
        Publish post to DEV.to via API.
        
        DEV.to accepts raw markdown directly — no HTML conversion needed!
        Mermaid diagrams render natively on DEV.to.
        
        Follows DEV.to API docs:
        - Endpoint: POST https://dev.to/api/articles
        - Auth: api-key header
        - Success: 201 Created

        Args:
            post: Blog post to publish

        Returns:
            PublicationResult with success status and URL

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        # DEV.to tags: max 4, lowercase, alphanumeric ONLY (no hyphens!)
        # Official Forem API spec: "tags" is a comma-separated string
        clean_tags = []
        for t in post.tags[:4]:
            # Replace hyphens and underscores with spaces
            tag = re.sub(r'[-_]', ' ', t.lower())
            # Remove all other non-alphanumeric chars
            tag = re.sub(r'[^a-z0-9 ]', '', tag)
            # Remove extra spaces and join words (no separators)
            tag = re.sub(r'\s+', '', tag)
            # Limit to 20 chars
            tag = tag[:20]
            if tag:  # Only add non-empty tags
                clean_tags.append(tag)
        
        # Join as comma-separated string per Forem OpenAPI spec
        tags_string = ", ".join(clean_tags)

        # Prepare clean body (no duplicate h1, no metadata block)
        body_markdown = self._prepare_devto_body(post)
        
        # Generate a short description from the first paragraph (max 150 chars)
        first_para = ""
        for line in body_markdown.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('```'):
                first_para = stripped[:150]
                break

        # Build payload per official Forem API spec:
        # Fields: title, body_markdown, published, series, main_image,
        #         canonical_url, description, tags, organization_id
        payload = {
            "article": {
                "title": post.title,
                "body_markdown": body_markdown,
                "published": False,  # Save as draft first for review
                "description": first_para,
                "tags": tags_string,
            }
        }
        
        # Only include canonical_url if it's a real URL
        if post.source_url and post.source_url.startswith('http'):
            payload["article"]["canonical_url"] = post.source_url
            
        # Add series grouping if present in post metadata
        if hasattr(post, 'metadata') and post.metadata and 'series' in post.metadata:
            payload["article"]["series"] = post.metadata['series']

        logger.info(
            f"DEV.to payload: title='{post.title}', tags='{tags_string}', "
            f"body_length={len(body_markdown)}, published=False",
            extra={"agent": "PublisherAgent"}
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://dev.to/api/articles",
                headers={
                    "api-key": self.config.devto_api_token,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30.0
            )
            
            # DEV.to returns 201 Created on success
            if response.status_code not in (200, 201):
                logger.error(
                    f"DEV.to API error {response.status_code}: {response.text}",
                    extra={"agent": "PublisherAgent"}
                )
                response.raise_for_status()
            
            data = response.json()
            post_url = data.get("url", "")
            
            logger.info(
                f"DEV.to draft created: {post_url} (id={data.get('id')})",
                extra={"agent": "PublisherAgent", "devto_id": data.get("id")}
            )

        return PublicationResult(
            success=True,
            post_url=post_url,
            error=None,
            published_at=datetime.utcnow()
        )

    async def _call_medium_api(self, post: BlogPost) -> PublicationResult:
        """
        Call Medium API to publish post.
        
        Args:
            post: Blog post to publish
        
        Returns:
            PublicationResult with success status and URL
        
        Raises:
            httpx.HTTPError: On HTTP errors
        """
        # Prepare content for Medium
        content_html = self._markdown_to_html(post.content)
        
        payload = {
            "title": post.title,
            "contentFormat": "html",
            "content": content_html,
            "tags": post.tags,
            "publishStatus": "draft",  # Always publish as draft
        }
        
        # Add canonical URL if available
        if post.source_url:
            payload["canonicalUrl"] = post.source_url
        
        # Publish to user's account
        endpoint = f"/users/{self.medium_author_id}/posts"
        
        response = await self.client.post(endpoint, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        return PublicationResult(
            success=True,
            post_url=data.get("data", {}).get("url"),
            error=None,
            published_at=datetime.utcnow()
        )

    async def _get_author_id(self) -> str:
        """
        Get Medium author ID from API.
        
        Returns:
            Author ID string
        
        Raises:
            PublicationError: If author ID cannot be retrieved
        """
        try:
            response = await self.client.get("/me")
            response.raise_for_status()
            
            data = response.json()
            author_id = data.get("data", {}).get("id")
            
            if not author_id:
                raise PublicationError("Failed to retrieve author ID from Medium")
            
            logger.info(f"Retrieved author ID: {author_id}", extra={"agent": "PublisherAgent"})
            return author_id
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get author ID: {e}", extra={"agent": "PublisherAgent"})
            raise PublicationError(f"Failed to get author ID: {e}") from e

    async def _save_local_draft(self, post: BlogPost) -> str:
        """
        Save blog post as local markdown file.
        
        Args:
            post: Blog post to save
        
        Returns:
            Path to saved markdown file
        """
        try:
            # Create filename from title (sanitize)
            filename = re.sub(r'[^\w\s-]', '', post.title.lower())
            filename = re.sub(r'[\s_]+', '-', filename)
            filename = f"{filename}.md"
            
            # Create date-based subdirectory
            date_str = post.generated_at.strftime("%Y-%m-%d")
            draft_dir = self.local_drafts_dir / date_str
            draft_dir.mkdir(parents=True, exist_ok=True)
            
            # Build markdown content
            markdown_content = self._build_markdown_content(post)
            
            # Save file
            file_path = draft_dir / filename
            
            # If file exists, add counter
            counter = 1
            while file_path.exists():
                filename_with_counter = filename.replace('.md', f'-{counter}.md')
                file_path = draft_dir / filename_with_counter
                counter += 1
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(
                f"Local draft saved: {file_path}",
                extra={"agent": "PublisherAgent", "path": str(file_path)}
            )
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save local draft: {e}", extra={"agent": "PublisherAgent"})
            # Don't fail the entire publication for this
            return f"local-draft-error-{datetime.utcnow().isoformat()}"

    def _build_markdown_content(self, post: BlogPost) -> str:
        """
        Build complete markdown content for the blog post.
        
        Args:
            post: Blog post
        
        Returns:
            Complete markdown string with images
        """
        lines = [
            f"# {post.title}",
            "",
            f"**Source:** {post.source_url}",
            f"**Generated:** {post.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Word Count:** {post.word_count}",
            f"**Tags:** {', '.join(post.tags)}",
            "",
            "---",
            "",
            post.content,  # This now includes embedded images!
            "",
            "---",
            "",
            f"*This post was generated by the Autonomous Blog Agent*",
            f"*Includes architecture diagrams and visual examples*",
        ]
        
        return "\n".join(lines)

    def _markdown_to_html(self, markdown: str) -> str:
        """
        Convert markdown to HTML for Medium.
        
        Args:
            markdown: Markdown content string
        
        Returns:
            HTML content string
        """
        import re
        import base64
        
        html = markdown
        
        # 1. Convert mermaid diagrams to images via mermaid.ink
        def replace_mermaid(match):
            original_code = match.group(1).strip()
            
            # Inject beautiful vibrant dark theme config right into the mermaid string
            theme_config = """%%{init: {"theme": "base", "themeVariables": {"background": "#0f172a", "primaryColor": "#8b5cf6", "primaryTextColor": "#ffffff", "primaryBorderColor": "#c4b5fd", "secondaryColor": "#ec4899", "tertiaryColor": "#14b8a6", "nodeBorder": "#c4b5fd", "clusterBkg": "#1e293b", "clusterBorder": "#334155", "lineColor": "#fde047", "textColor": "#e2e8f0"}}}%%
"""
            code = theme_config + original_code
            
            # Encode code to base64
            encoded = base64.urlsafe_b64encode(code.encode('utf-8')).decode('utf-8')
            return f'<img src="https://mermaid.ink/svg/{encoded}" alt="Architecture Diagram" />'
            
        html = re.sub(r'```mermaid\n(.*?)```', replace_mermaid, html, flags=re.DOTALL)
        
        # Convert headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Convert remaining code blocks
        html = re.sub(
            r'```(\w+)?\n(.*?)```',
            r'<pre><code>\2</code></pre>',
            html,
            flags=re.DOTALL
        )
        
        # Convert paragraphs (double newlines)
        html = re.sub(r'\n\n(.+?)\n\n', r'<p>\1</p>', html, flags=re.DOTALL)
        
        return html

    async def can_publish_today(self) -> bool:
        """
        Check if daily publication limit reached.
        
        Returns:
            True if can publish, False if limit reached
        """
        return await self.memory_system.can_publish_today()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client is not None:
            await self.client.aclose()
        logger.info("PublisherAgent client closed")
