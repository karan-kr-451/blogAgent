"""SEO Agent for optimizing blog content for search engines and social media.

Uses LLM (Ollama) for high-impact creative tasks (meta titles, descriptions,
LinkedIn posts, Twitter threads) while keeping structural and scoring logic
rule-based for speed and reliability.
"""

import re
import json
import base64
import logging
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field

import httpx

from src.config import Config, get_config
from src.logging_config import get_logger
from src.models.data_models import BlogPost
from src.utils.retry import retry_with_backoff

logger = get_logger(__name__)


@dataclass
class SEOScore:
    """SEO score breakdown."""
    overall: int = 0
    keyword_optimization: int = 0
    meta_quality: int = 0
    content_structure: int = 0
    readability: int = 0
    social_ready: int = 0
    platform_coverage: int = 0
    recommendations: list[str] = field(default_factory=list)


@dataclass
class SEOMetadata:
    """SEO metadata for a blog post."""
    meta_title: str = ""
    meta_description: str = ""
    canonical_url: str = ""
    keywords: list[str] = field(default_factory=list)
    lsi_keywords: list[str] = field(default_factory=list)
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_type: str = "article"
    twitter_card: str = "summary_large_image"
    twitter_title: str = ""
    twitter_description: str = ""
    schema_markup: str = ""
    reading_time: int = 0
    word_count: int = 0
    table_of_contents: str = ""


@dataclass
class PlatformContent:
    """
    Platform-specific post content for maximum cross-platform reach.
    Each platform gets its own tailored version.
    """
    # LinkedIn — professional tone, hook + insights + CTA
    linkedin_post: str = ""
    linkedin_hashtags: list[str] = field(default_factory=list)

    # Twitter/X — punchy thread (numbered tweets)
    twitter_thread: list[str] = field(default_factory=list)
    twitter_hashtags: list[str] = field(default_factory=list)

    # dev.to — front matter YAML block
    devto_front_matter: str = ""
    devto_tags: list[str] = field(default_factory=list)

    # Hashnode — front matter + publication slug
    hashnode_front_matter: str = ""

    # Medium — import-ready with canonical URL
    medium_canonical_note: str = ""

    # Generic short teaser (email newsletters, etc.)
    short_teaser: str = ""


class SEOAgent:
    """
    Agent that optimizes blog posts for search engines and all major platforms.

    Handles:
    - Keyword research and LSI keyword expansion
    - Meta tags generation (title, description)
    - Open Graph + Twitter Card optimization
    - Schema.org structured data (Article + FAQ + HowTo)
    - Table of Contents injection
    - Content structure improvements
    - Platform-specific content: LinkedIn post, Twitter thread,
      dev.to front matter, Hashnode front matter, Medium canonical note
    - SEO scoring with platform coverage dimension
    """

    def __init__(self, config: Config | None = None):
        self.config = config or get_config()

        # LLM client for enhanced content generation
        self.ollama_endpoint = self.config.ollama_endpoint
        self.model = self.config.ollama_model

        headers = {"Content-Type": "application/json"}
        if self.config.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.ollama_endpoint.rstrip('/'),
            timeout=self.config.ollama_timeout,
            headers=headers
        )

        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its',
            'our', 'their', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when',
            'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'because', 'as', 'until', 'while',
            'about', 'against', 'between', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'here', 'there', 'any'
        }

        # Primary high-value keywords
        self.high_value_keywords = [
            'system design', 'distributed systems', 'microservices', 'architecture',
            'scalability', 'machine learning', 'artificial intelligence', 'generative ai',
            'agentic ai', 'llm', 'mlops', 'devops', 'cloud native', 'kubernetes',
            'api design', 'database', 'caching', 'load balancing', 'event-driven',
            'real-time', 'high availability', 'fault tolerance', 'data engineering',
            'vector database', 'rag', 'fine-tuning', 'inference', 'embeddings',
            'prompt engineering', 'agent', 'workflow', 'orchestration', 'pipeline',
        ]

        # LSI keyword map: primary keyword → related semantic terms
        self.lsi_map = {
            'machine learning': ['neural network', 'model training', 'prediction', 'feature engineering'],
            'system design': ['scalability', 'reliability', 'trade-offs', 'capacity planning'],
            'microservices': ['service mesh', 'api gateway', 'container', 'deployment'],
            'llm': ['large language model', 'transformer', 'token', 'inference'],
            'generative ai': ['foundation model', 'llm', 'prompt', 'hallucination'],
            'agentic ai': ['tool use', 'reasoning', 'orchestrator', 'workflow'],
            'kubernetes': ['container orchestration', 'pod', 'deployment', 'helm'],
            'caching': ['redis', 'memcached', 'ttl', 'cache invalidation'],
            'database': ['sql', 'nosql', 'sharding', 'replication', 'indexing'],
            'api design': ['rest', 'graphql', 'grpc', 'versioning', 'rate limiting'],
            'devops': ['ci/cd', 'infrastructure as code', 'monitoring', 'deployment'],
        }

        logger.info(
            "SEOAgent initialized (LLM-enhanced)",
            extra={"agent": "SEOAgent", "model": self.model}
        )

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────

    async def _call_llm(self, prompt: str, system: str = "", max_tokens: int = 512, temperature: float = 0.6) -> str:
        """
        Call Ollama LLM for SEO content generation.

        Args:
            prompt: User prompt with the task.
            system: System-level instructions.
            max_tokens: Max response tokens.
            temperature: Creativity level (lower = more focused).

        Returns:
            Generated text from LLM.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        return response.json().get("response", "").strip()

    async def optimize(self, post: BlogPost) -> tuple[BlogPost, SEOMetadata, SEOScore, PlatformContent]:
        """
        Optimize blog post for SEO and generate all platform content.
        Uses LLM for meta titles, descriptions, and social media content.

        Returns:
            (optimized_post, seo_metadata, seo_score, platform_content)
        """
        logger.info(f"Optimizing post for SEO (LLM-enhanced): {post.title}", extra={"agent": "SEOAgent"})

        keywords = self._extract_keywords(post.content)
        lsi_keywords = self._expand_lsi_keywords(keywords)

        # LLM-enhanced meta generation with rule-based fallbacks
        meta_title = await self._generate_meta_title(post.title, keywords, post.content)
        meta_description = await self._generate_meta_description(post.content, keywords, post.title)

        optimized_content = self._optimize_content_structure(post.content, keywords)
        toc = self._generate_table_of_contents(optimized_content)

        # Inject TOC after the first paragraph if headings exist
        if toc:
            optimized_content = self._inject_toc(optimized_content, toc)

        schema_markup = self._generate_schema_markup(post, meta_description, keywords)
        reading_time = max(1, post.word_count // 238)  # 238 wpm average
        og_image = self._get_og_image(post.content)

        optimized_post = BlogPost(
            title=post.title,
            content=optimized_content,
            tags=post.tags,
            word_count=post.word_count,
            source_url=post.source_url,
            generated_at=post.generated_at,
            metadata={
                **post.metadata,
                'seo_keywords': keywords[:10],
                'lsi_keywords': lsi_keywords[:10],
                'reading_time': reading_time,
                'optimized': True
            }
        )

        seo_metadata = SEOMetadata(
            meta_title=meta_title,
            meta_description=meta_description,
            canonical_url=post.source_url or "",
            keywords=keywords[:10],
            lsi_keywords=lsi_keywords[:10],
            og_title=meta_title,
            og_description=meta_description,
            og_image=og_image,
            og_type="article",
            twitter_card="summary_large_image",
            twitter_title=meta_title,
            twitter_description=meta_description[:200],
            schema_markup=schema_markup,
            reading_time=reading_time,
            word_count=post.word_count,
            table_of_contents=toc,
        )

        # LLM-enhanced platform content generation
        platform_content = await self._generate_platform_content(post, keywords, lsi_keywords, reading_time, meta_description)
        seo_score = self._calculate_seo_score(optimized_post, seo_metadata, platform_content)

        logger.info(
            f"SEO optimization complete (LLM-enhanced): Score {seo_score.overall}/100",
            extra={
                "agent": "SEOAgent",
                "seo_score": seo_score.overall,
                "keywords_found": len(keywords),
                "lsi_keywords": len(lsi_keywords),
                "platforms_ready": sum([
                    bool(platform_content.linkedin_post),
                    bool(platform_content.twitter_thread),
                    bool(platform_content.devto_front_matter),
                    bool(platform_content.hashnode_front_matter),
                ])
            }
        )

        return optimized_post, seo_metadata, seo_score, platform_content

    # ─────────────────────────────────────────────────────────────
    # Keyword Extraction
    # ─────────────────────────────────────────────────────────────

    def _extract_keywords(self, content: str) -> list[str]:
        """Extract top keywords from content."""
        words = re.findall(r'\b[a-z]{3,}\b', content.lower())

        word_freq = {}
        for word in words:
            if word not in self.stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        key_phrases = self._extract_key_phrases(content)

        keywords = [phrase for phrase, _ in key_phrases[:5]]
        keywords.extend([word for word, _ in sorted_keywords[:10]])

        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen and len(kw) > 2:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:15]

    def _extract_key_phrases(self, content: str) -> list[tuple[str, int]]:
        """Extract important key phrases from content."""
        patterns = [
            r'\b(system design|distributed systems|microservices|machine learning|'
            r'artificial intelligence|generative ai|agentic ai|load balancing|'
            r'event-driven|real-time|high availability|fault tolerance|'
            r'data engineering|cloud native|api design|database sharding|'
            r'message queue|service mesh|container orchestration|vector database|'
            r'rag|retrieval augmented|prompt engineering|fine.tuning|inference engine)\b',
            r'\b(how to|scaling|building|designing|implementing|optimizing) \w+',
            r'\b\w+ (architecture|infrastructure|pipeline|system|platform|framework|workflow)\b'
        ]

        phrase_freq = {}
        for pattern in patterns:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                phrase_freq[match] = phrase_freq.get(match, 0) + 1

        return sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)

    def _expand_lsi_keywords(self, keywords: list[str]) -> list[str]:
        """Expand keywords with LSI (Latent Semantic Indexing) related terms."""
        lsi = []
        for kw in keywords[:5]:
            for seed, related in self.lsi_map.items():
                if seed in kw or kw in seed:
                    lsi.extend(related)

        seen = set(keywords)
        unique_lsi = []
        for term in lsi:
            if term not in seen:
                seen.add(term)
                unique_lsi.append(term)

        return unique_lsi[:10]

    # ─────────────────────────────────────────────────────────────
    # Meta Generation
    # ─────────────────────────────────────────────────────────────

    def _fallback_meta_title(self, title: str, keywords: list[str]) -> str:
        """Rule-based fallback for meta title generation."""
        clean_title = re.sub(r'[^\w\s:\-|]', '', title).strip()

        if 50 <= len(clean_title) <= 60:
            return clean_title

        if len(clean_title) < 50 and keywords:
            suffix = keywords[0].title()
            candidate = f"{clean_title} | {suffix}"
            if len(candidate) <= 60:
                return candidate
            return clean_title

        if len(clean_title) > 60:
            truncated = clean_title[:57]
            last_space = truncated.rfind(' ')
            if last_space > 40:
                return truncated[:last_space] + "..."
            return truncated + "..."

        return clean_title

    async def _generate_meta_title(self, title: str, keywords: list[str], content: str = "") -> str:
        """LLM-enhanced SEO meta title (50-60 characters)."""
        try:
            kw_str = ", ".join(keywords[:5]) if keywords else "technology"
            prompt = (
                f"Write ONE SEO-optimized title for a blog post.\n"
                f"Original title: {title}\n"
                f"Target keywords: {kw_str}\n\n"
                f"Rules:\n"
                f"- MUST be between 50 and 60 characters (this is critical)\n"
                f"- Include the primary keyword naturally\n"
                f"- Use a power word (e.g., Ultimate, Essential, Proven, Deep Dive)\n"
                f"- Make it click-worthy but not clickbait\n"
                f"- Do NOT use quotes around the title\n\n"
                f"Reply with ONLY the title text, nothing else."
            )
            result = await self._call_llm(prompt, max_tokens=80, temperature=0.5)
            # Clean LLM output
            result = result.strip().strip('"').strip("'").split("\n")[0].strip()
            # Validate length constraint
            if 30 <= len(result) <= 70:
                logger.info(f"LLM meta title: '{result}' ({len(result)} chars)", extra={"agent": "SEOAgent"})
                return result[:60]
        except Exception as e:
            logger.warning(f"LLM meta title failed, using fallback: {e}", extra={"agent": "SEOAgent"})

        return self._fallback_meta_title(title, keywords)

    def _fallback_meta_description(self, content: str, keywords: list[str]) -> str:
        """Rule-based fallback for meta description generation."""
        paragraphs = content.split('\n\n')
        first_para = ""
        for para in paragraphs:
            para = para.strip()
            if para and not para.startswith('#') and not para.startswith('```'):
                first_para = para
                break

        clean_para = re.sub(r'#{1,6}\s+', '', first_para)
        clean_para = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_para)
        clean_para = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', clean_para)
        clean_para = re.sub(r'`([^`]+)`', r'\1', clean_para).strip()

        if 120 <= len(clean_para) <= 160:
            return clean_para

        if len(clean_para) > 160:
            truncated = clean_para[:157]
            last_space = truncated.rfind(' ')
            return (truncated[:last_space] + "...") if last_space > 100 else truncated + "..."

        if keywords:
            base = f"Learn {keywords[0]} with practical examples and best practices."
            if len(keywords) > 1:
                base += f" Covers {keywords[1]}, {keywords[2] if len(keywords) > 2 else 'scalability'} and more."
            if len(base) <= 160:
                return base
            return base[:157] + "..."

        return clean_para

    async def _generate_meta_description(self, content: str, keywords: list[str], title: str = "") -> str:
        """LLM-enhanced SEO meta description (150-160 characters)."""
        try:
            kw_str = ", ".join(keywords[:5]) if keywords else "technology"
            # Give the LLM first 500 chars of content for context
            excerpt = re.sub(r'[#*`\[\]()]', '', content[:500]).strip()
            prompt = (
                f"Write ONE meta description for a blog post about: {title}\n"
                f"Content excerpt: {excerpt}\n"
                f"Target keywords: {kw_str}\n\n"
                f"Rules:\n"
                f"- MUST be between 145 and 160 characters (this is critical for SEO)\n"
                f"- Include the primary keyword in the first 60 characters\n"
                f"- Use an action verb (learn, discover, explore, master, build)\n"
                f"- End with a benefit or value proposition\n"
                f"- Do NOT use quotes\n\n"
                f"Reply with ONLY the description text, nothing else."
            )
            result = await self._call_llm(prompt, max_tokens=120, temperature=0.5)
            result = result.strip().strip('"').strip("'").split("\n")[0].strip()
            if 100 <= len(result) <= 180:
                logger.info(f"LLM meta description ({len(result)} chars)", extra={"agent": "SEOAgent"})
                return result[:160]
        except Exception as e:
            logger.warning(f"LLM meta description failed, using fallback: {e}", extra={"agent": "SEOAgent"})

        return self._fallback_meta_description(content, keywords)

    # ─────────────────────────────────────────────────────────────
    # Content Structure
    # ─────────────────────────────────────────────────────────────

    def _optimize_content_structure(self, content: str, keywords: list[str]) -> str:
        """Optimize content structure for SEO."""
        optimized = content

        # Inject primary keyword into first paragraph if missing
        if keywords:
            primary_keyword = keywords[0]
            first_para_match = re.search(r'\n\n([^\n#`][^\n]+)', optimized)
            if first_para_match:
                first_para = first_para_match.group(1)
                if primary_keyword.lower() not in first_para.lower():
                    optimized = optimized.replace(
                        first_para,
                        f"In this guide, we explore {primary_keyword}. {first_para}",
                        1
                    )

        # Enforce heading hierarchy (keep only first h1)
        lines = optimized.split('\n')
        in_code_block = False
        optimized_lines = []
        h1_seen = False

        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block

            if not in_code_block and line.strip().startswith('# ') and not line.strip().startswith('##'):
                if not h1_seen:
                    optimized_lines.append(line)
                    h1_seen = True
                # Skip duplicate h1s
            else:
                optimized_lines.append(line)

        return '\n'.join(optimized_lines)

    def _generate_table_of_contents(self, content: str) -> str:
        """Generate a Markdown table of contents from H2/H3 headings."""
        toc_lines = []
        in_code_block = False

        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            h2 = re.match(r'^## (.+)$', stripped)
            h3 = re.match(r'^### (.+)$', stripped)

            if h2:
                heading = h2.group(1)
                anchor = re.sub(r'[^\w\s-]', '', heading.lower()).strip().replace(' ', '-')
                toc_lines.append(f"- [{heading}](#{anchor})")
            elif h3:
                heading = h3.group(1)
                anchor = re.sub(r'[^\w\s-]', '', heading.lower()).strip().replace(' ', '-')
                toc_lines.append(f"  - [{heading}](#{anchor})")

        if len(toc_lines) < 2:
            return ""

        return "## Table of Contents\n\n" + "\n".join(toc_lines)

    def _inject_toc(self, content: str, toc: str) -> str:
        """Inject table of contents after the first paragraph."""
        paragraphs = content.split('\n\n')
        insert_index = 0

        for i, para in enumerate(paragraphs):
            stripped = para.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('```'):
                insert_index = i + 1
                break

        paragraphs.insert(insert_index, toc)
        return '\n\n'.join(paragraphs)

    # ─────────────────────────────────────────────────────────────
    # Schema Markup (fixed: uses json.dumps)
    # ─────────────────────────────────────────────────────────────

    def _generate_schema_markup(self, post: BlogPost, description: str, keywords: list[str]) -> str:
        """Generate JSON-LD schema markup (Article + FAQ if applicable)."""
        schemas = []

        # Article schema
        article_schema = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": post.title,
            "description": description,
            "author": {
                "@type": "Organization",
                "name": "Autonomous Blog Agent"
            },
            "datePublished": post.generated_at.isoformat(),
            "dateModified": post.generated_at.isoformat(),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": post.source_url or ""
            },
            "keywords": ", ".join(post.tags + keywords[:5]),
            "articleSection": post.tags[0] if post.tags else "Technology",
            "wordCount": post.word_count,
            "proficiencyLevel": "Expert",
        }
        schemas.append(article_schema)

        # FAQ schema — extract headings formatted as questions
        faq_items = self._extract_faq_items(post.content)
        if faq_items:
            faq_schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": a
                        }
                    }
                    for q, a in faq_items
                ]
            }
            schemas.append(faq_schema)

        # HowTo schema — if post title starts with "How to"
        if post.title.lower().startswith("how to"):
            howto_steps = self._extract_howto_steps(post.content)
            if howto_steps:
                howto_schema = {
                    "@context": "https://schema.org",
                    "@type": "HowTo",
                    "name": post.title,
                    "description": description,
                    "step": [
                        {"@type": "HowToStep", "name": step, "text": step}
                        for step in howto_steps
                    ]
                }
                schemas.append(howto_schema)

        result = "\n".join(
            f'<script type="application/ld+json">\n{json.dumps(s, indent=2)}\n</script>'
            for s in schemas
        )
        return result

    def _extract_faq_items(self, content: str) -> list[tuple[str, str]]:
        """Extract question/answer pairs from content headings."""
        faq = []
        lines = content.split('\n')
        in_code = False

        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                in_code = not in_code
            if in_code:
                continue

            # Headings ending with '?' are FAQ candidates
            match = re.match(r'^#{2,3} (.+\?)$', line.strip())
            if match:
                question = match.group(1)
                # Grab the next non-empty, non-heading paragraph as the answer
                answer_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    l = lines[j].strip()
                    if l.startswith('#'):
                        break
                    if l:
                        answer_lines.append(l)
                if answer_lines:
                    faq.append((question, ' '.join(answer_lines)[:300]))

        return faq[:5]

    def _extract_howto_steps(self, content: str) -> list[str]:
        """Extract numbered list items as HowTo steps."""
        steps = re.findall(r'^\d+\.\s+(.+)$', content, re.MULTILINE)
        return steps[:10]

    # ─────────────────────────────────────────────────────────────
    # OG Image (fixed: uses mermaid.ink for diagrams)
    # ─────────────────────────────────────────────────────────────

    def _get_og_image(self, content: str) -> str:
        """Extract or generate Open Graph image URL from content."""
        # 1. Use first explicit image
        image_matches = re.findall(r'!\[.*?\]\((https?://[^)]+)\)', content)
        if image_matches:
            return image_matches[0]

        # 2. Render first Mermaid diagram via mermaid.ink (same logic as publisher.py)
        mermaid_match = re.search(r'```mermaid\n(.*?)```', content, re.DOTALL)
        if mermaid_match:
            code = mermaid_match.group(1).strip()
            encoded = base64.urlsafe_b64encode(code.encode('utf-8')).decode('utf-8')
            return f"https://mermaid.ink/img/{encoded}"

        return ""

    # ─────────────────────────────────────────────────────────────
    # Platform-Specific Content Generation
    # ─────────────────────────────────────────────────────────────

    async def _generate_platform_content(
        self,
        post: BlogPost,
        keywords: list[str],
        lsi_keywords: list[str],
        reading_time: int,
        meta_description: str
    ) -> PlatformContent:
        """Generate tailored content for every publishing platform (LLM-enhanced)."""
        pc = PlatformContent()

        pc.linkedin_post, pc.linkedin_hashtags = await self._generate_linkedin_post(post, keywords, reading_time)
        pc.twitter_thread, pc.twitter_hashtags = await self._generate_twitter_thread(post, keywords)
        pc.devto_front_matter, pc.devto_tags = self._generate_devto_front_matter(post, keywords, meta_description)
        pc.hashnode_front_matter = self._generate_hashnode_front_matter(post, keywords, meta_description)
        pc.medium_canonical_note = self._generate_medium_canonical_note(post)
        pc.short_teaser = await self._generate_short_teaser(post, keywords, reading_time)

        return pc

    def _fallback_linkedin_post(
        self, post: BlogPost, keywords: list[str], reading_time: int
    ) -> tuple[str, list[str]]:
        """Rule-based fallback for LinkedIn post generation."""
        headings = re.findall(r'^#{2,3} (.+)$', post.content, re.MULTILINE)
        insights = [h for h in headings if not h.lower().startswith('table')][:4]

        hook = f"Most engineers get {keywords[0] if keywords else 'system design'} wrong. Here's what actually works. 🧵"

        bullets = ""
        if insights:
            bullets = "\n".join(f"→ {insight}" for insight in insights[:4])
        else:
            bullets = f"→ Why {post.title} matters in production\n→ Key trade-offs you need to know\n→ Step-by-step implementation guide"

        url = post.source_url or ""
        cta = f"\n\n📖 Full deep-dive ({reading_time} min read): {url}" if url else ""

        hashtags = self._generate_hashtags(keywords, platform="linkedin")
        hashtag_str = " ".join(f"#{h}" for h in hashtags[:8])

        post_text = f"""{hook}

{bullets}

What would you add? Drop it in the comments 👇{cta}

{hashtag_str}"""

        return post_text, hashtags

    async def _generate_linkedin_post(
        self, post: BlogPost, keywords: list[str], reading_time: int
    ) -> tuple[str, list[str]]:
        """
        LLM-enhanced LinkedIn post with:
        - Pattern-interrupt hook (first line = stop-the-scroll)
        - 3-5 key takeaways as bullets
        - CTA with article link
        - Hashtags
        """
        hashtags = self._generate_hashtags(keywords, platform="linkedin")

        try:
            url = post.source_url or ""
            excerpt = re.sub(r'[#*`\[\]()]', '', post.content[:1000]).strip()
            kw_str = ", ".join(keywords[:5]) if keywords else "technology"

            system = (
                "You are a LinkedIn content strategist who writes viral tech posts. "
                "Your posts get 10x more engagement than average because you use "
                "pattern-interrupt hooks, concrete insights, and genuine curiosity."
            )
            prompt = (
                f"Write a LinkedIn post promoting this blog article.\n\n"
                f"Title: {post.title}\n"
                f"Keywords: {kw_str}\n"
                f"Content excerpt: {excerpt}\n"
                f"Reading time: {reading_time} min\n"
                f"Article URL: {url}\n\n"
                f"Format:\n"
                f"1. First line: a bold, pattern-interrupt hook (make them stop scrolling)\n"
                f"2. Empty line\n"
                f"3. 3-5 key insights as bullet points using → arrows\n"
                f"4. Empty line\n"
                f"5. Engagement question (ask readers to share their experience)\n"
                f"6. CTA linking to the full article with reading time\n\n"
                f"Rules:\n"
                f"- No emojis in the hook (except one at the end)\n"
                f"- Use metrics or surprising facts when possible\n"
                f"- Keep each bullet to one line, max 15 words\n"
                f"- Do NOT include hashtags — I'll add them separately\n"
                f"- Total post: 800-1300 characters\n\n"
                f"Reply with ONLY the post text."
            )
            result = await self._call_llm(prompt, system=system, max_tokens=400, temperature=0.7)
            result = result.strip()

            if len(result) > 200:
                # Append hashtags
                hashtag_str = " ".join(f"#{h}" for h in hashtags[:8])
                result = f"{result}\n\n{hashtag_str}"
                logger.info(f"LLM LinkedIn post generated ({len(result)} chars)", extra={"agent": "SEOAgent"})
                return result, hashtags

        except Exception as e:
            logger.warning(f"LLM LinkedIn post failed, using fallback: {e}", extra={"agent": "SEOAgent"})

        return self._fallback_linkedin_post(post, keywords, reading_time)

    def _fallback_twitter_thread(
        self, post: BlogPost, keywords: list[str]
    ) -> tuple[list[str], list[str]]:
        """Rule-based fallback for Twitter thread generation."""
        headings = re.findall(r'^#{2,3} (.+)$', post.content, re.MULTILINE)
        clean_headings = [h for h in headings if not h.lower().startswith('table')][:6]

        hashtags = self._generate_hashtags(keywords, platform="twitter")
        hashtag_str = " ".join(f"#{h}" for h in hashtags[:3])

        thread = []
        hook = f"🧵 {post.title}\n\nA thread on what every engineer should know:"
        thread.append(hook[:280])

        for i, heading in enumerate(clean_headings, 2):
            tweet = f"{i}/ {heading}\n\n"
            pattern = re.compile(
                rf'^#{2,3} {re.escape(heading)}\n\n([^\n#`]{{20,200}})',
                re.MULTILINE
            )
            match = pattern.search(post.content)
            if match:
                snippet = match.group(1).strip()[:180]
                tweet += snippet
            thread.append(tweet[:280])

        url = post.source_url or ""
        cta_tweet = f"{len(thread) + 1}/ Full article with code examples + diagrams:"
        if url:
            cta_tweet += f"\n{url}"
        cta_tweet += f"\n\n{hashtag_str}"
        thread.append(cta_tweet[:280])

        return thread, hashtags

    async def _generate_twitter_thread(
        self, post: BlogPost, keywords: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        LLM-enhanced Twitter/X thread:
        - Tweet 1: hook
        - Tweets 2-6: one key insight each (≤280 chars)
        - Last tweet: CTA + hashtags
        """
        hashtags = self._generate_hashtags(keywords, platform="twitter")

        try:
            excerpt = re.sub(r'[#*`\[\]()]', '', post.content[:1500]).strip()
            url = post.source_url or ""
            kw_str = ", ".join(keywords[:5]) if keywords else "technology"
            hashtag_str = " ".join(f"#{h}" for h in hashtags[:3])

            system = (
                "You are a tech Twitter influencer. You write threads that "
                "get massive engagement by distilling complex topics into "
                "sharp, insightful tweets engineers love to retweet."
            )
            prompt = (
                f"Write a Twitter/X thread (5-7 tweets) about this blog post.\n\n"
                f"Title: {post.title}\n"
                f"Keywords: {kw_str}\n"
                f"Content: {excerpt}\n"
                f"Article URL: {url}\n\n"
                f"Format each tweet as:\n"
                f"1/ [hook tweet]\n\n"
                f"2/ [insight]\n\n"
                f"..etc\n\n"
                f"Rules:\n"
                f"- Each tweet MUST be under 280 characters\n"
                f"- Tweet 1 is the hook — start with 🧵 and a bold claim or question\n"
                f"- Tweets 2-5 each share one specific, concrete insight\n"
                f"- Use numbers, metrics, or analogies when possible\n"
                f"- Last tweet is CTA: link to article + hashtags {hashtag_str}\n"
                f"- No filler. Every word earns its place.\n\n"
                f"Reply with ONLY the numbered tweets."
            )
            result = await self._call_llm(prompt, system=system, max_tokens=600, temperature=0.7)

            # Parse numbered tweets from LLM output
            raw_tweets = re.split(r'\n\d+[/.)\s]', "\n" + result.strip())
            thread = []
            for t in raw_tweets:
                t = t.strip()
                if t and len(t) > 20:
                    thread.append(t[:280])

            if len(thread) >= 3:
                logger.info(f"LLM Twitter thread generated ({len(thread)} tweets)", extra={"agent": "SEOAgent"})
                return thread, hashtags

        except Exception as e:
            logger.warning(f"LLM Twitter thread failed, using fallback: {e}", extra={"agent": "SEOAgent"})

        return self._fallback_twitter_thread(post, keywords)

    def _generate_devto_front_matter(
        self, post: BlogPost, keywords: list[str], meta_description: str
    ) -> tuple[str, list[str]]:
        """
        Generate dev.to front matter YAML optimized for views and reach.
        Includes conditional handling of cover_image/canonical_url and series support.
        """
        # Dev.to prefers certain macro tags (e.g., programming, webdev, ai, machinelearning)
        devto_popular_tags = {'ai', 'machinelearning', 'python', 'programming', 'webdev', 'devops', 'opensource'}
        
        # Sanitize tags for dev.to: lowercase, alphanumeric only, max 4
        # Replace spaces with nothing (e.g., "Machine Learning" -> "machinelearning")
        raw_tags = post.tags + keywords
        clean_tags = []
        for t in raw_tags:
            tag = re.sub(r'[^a-z0-9]', '', t.lower())
            if tag and tag not in clean_tags:
                clean_tags.append(tag)
                
        # Ensure we prioritize high-reach tags if they match our content
        final_tags = []
        for ct in clean_tags:
            if ct in devto_popular_tags and ct not in final_tags:
                final_tags.append(ct)
        for ct in clean_tags:
            if ct not in final_tags and len(final_tags) < 4:
                final_tags.append(ct)
                
        final_tags = final_tags[:4]

        og_image = self._get_og_image(post.content)
        canonical = post.source_url or ""
        
        # Build YAML front matter dynamically to avoid empty keys
        clean_title = post.title.replace('"', '\\"')
        lines = [
            "---",
            f'title: "{clean_title}"',
            "published: false",
            f"tags: {', '.join(final_tags)}",
        ]
        
        # Only include cover image if one exists (prevents broken YAML or Dev.to errors)
        if og_image:
            lines.append(f"cover_image: {og_image}")
            
        # Strongly recommended for SEO to prevent duplicate content penalties across platforms
        if canonical:
            lines.append(f"canonical_url: {canonical}")
            
        # Series grouping increases engagement/reach drastically
        if hasattr(post, 'metadata') and post.metadata and 'series' in post.metadata:
            lines.append(f"series: {post.metadata['series']}")
            
        desc = meta_description
        lines.append(f"description: >\n  {desc}")
        lines.append("---")
        
        front_matter = "\n".join(lines)

        return front_matter, final_tags

    def _generate_hashnode_front_matter(self, post: BlogPost, keywords: list[str], meta_description: str) -> str:
        """
        Generate Hashnode front matter for their GraphQL API / import.
        Hashnode accepts tags as slugs.
        """
        tags_yaml = "\n".join(f"  - slug: {t.lower().replace(' ', '-')}" for t in post.tags[:5])
        og_image = self._get_og_image(post.content)
        canonical = post.source_url or ""

        return f"""---
title: {post.title}
subtitle: {meta_description[:100]}
coverImage: {og_image}
canonicalUrl: {canonical}
tags:
{tags_yaml}
publishedAt: {post.generated_at.strftime('%Y-%m-%dT%H:%M:%SZ')}
---"""

    def _generate_medium_canonical_note(self, post: BlogPost) -> str:
        """
        Generate the canonical URL note to append to Medium posts.
        This tells Medium (and Google) where the original content lives.
        """
        if not post.source_url:
            return ""
        return (
            f"\n\n---\n\n"
            f"*Originally published at [{post.source_url}]({post.source_url})*"
        )

    async def _generate_short_teaser(
        self, post: BlogPost, keywords: list[str], reading_time: int
    ) -> str:
        """
        LLM-enhanced short teaser (≤300 chars) for newsletters, Slack, etc.
        """
        try:
            excerpt = re.sub(r'[#*`\[\]()]', '', post.content[:500]).strip()
            url = post.source_url or ""
            prompt = (
                f"Write a one-sentence teaser for this blog post to share in newsletters and Slack.\n\n"
                f"Title: {post.title}\n"
                f"Content preview: {excerpt}\n"
                f"Reading time: {reading_time} min\n\n"
                f"Rules:\n"
                f"- Start with 📝 emoji\n"
                f"- Max 250 characters (before URL)\n"
                f"- Create curiosity — make them click\n"
                f"- Include the reading time at the end like '(X min read)'\n"
                f"- Do NOT include a URL\n\n"
                f"Reply with ONLY the teaser text."
            )
            result = await self._call_llm(prompt, max_tokens=100, temperature=0.6)
            result = result.strip().strip('"').split("\n")[0].strip()
            if len(result) > 50:
                if url:
                    result = f"{result[:250]} {url}"
                return result[:300]
        except Exception as e:
            logger.warning(f"LLM teaser failed, using fallback: {e}", extra={"agent": "SEOAgent"})

        # Fallback
        desc = self._fallback_meta_description(post.content, keywords)
        url = post.source_url or ""
        teaser = f"📝 {post.title} — {desc[:150]}... ({reading_time} min read)"
        if url:
            teaser += f" {url}"
        return teaser[:300]

    def _generate_hashtags(self, keywords: list[str], platform: str = "generic") -> list[str]:
        """Generate platform-appropriate hashtags from keywords."""
        # Map keywords to clean hashtag strings
        raw = []
        for kw in keywords[:8]:
            tag = re.sub(r'[^a-z0-9]', '', kw.lower().replace(' ', '').replace('-', ''))
            if len(tag) > 2:
                raw.append(tag)

        # Add evergreen tags
        evergreen = {
            "linkedin": ["softwareengineering", "programming", "technology", "ai", "machinelearning"],
            "twitter": ["buildinpublic", "devtwitter", "100daysofcode"],
            "generic": ["tech", "engineering"],
        }
        raw.extend(evergreen.get(platform, evergreen["generic"]))

        # Deduplicate
        seen = set()
        result = []
        for tag in raw:
            if tag not in seen:
                seen.add(tag)
                result.append(tag)

        limit = 8 if platform == "linkedin" else 4
        return result[:limit]

    # ─────────────────────────────────────────────────────────────
    # SEO Scoring
    # ─────────────────────────────────────────────────────────────

    def _calculate_seo_score(
        self, post: BlogPost, metadata: SEOMetadata, platform_content: PlatformContent
    ) -> SEOScore:
        """Calculate comprehensive SEO score (0-100)."""
        score = SEOScore()
        recommendations = []

        # ── Keyword optimization (0-20) ──────────────────────────
        keyword_score = 0
        content_lower = post.content.lower()

        if any(kw.lower() in post.title.lower() for kw in metadata.keywords[:3]):
            keyword_score += 8
        else:
            recommendations.append("Add primary keyword to title")

        keyword_occurrences = sum(1 for kw in metadata.keywords[:5] if kw.lower() in content_lower)
        keyword_score += min(8, keyword_occurrences * 2)
        if keyword_occurrences < 3:
            recommendations.append("Increase keyword usage in content body")

        first_para = content_lower[:300]
        if any(kw.lower() in first_para for kw in metadata.keywords[:3]):
            keyword_score += 4
        else:
            recommendations.append("Add primary keyword to first paragraph")

        score.keyword_optimization = min(20, keyword_score)

        # ── Meta quality (0-20) ──────────────────────────────────
        meta_score = 0

        if metadata.meta_title:
            meta_score += 8
            if 50 <= len(metadata.meta_title) <= 60:
                meta_score += 4
            else:
                recommendations.append(f"Meta title: aim for 50-60 chars (now {len(metadata.meta_title)})")

        if metadata.meta_description:
            meta_score += 8
            if 120 <= len(metadata.meta_description) <= 160:
                meta_score += 4
            else:
                recommendations.append(f"Meta description: aim for 120-160 chars (now {len(metadata.meta_description)})")

        score.meta_quality = min(20, meta_score)

        # ── Content structure (0-20) ─────────────────────────────
        structure_score = 0

        has_h1 = bool(re.search(r'^# ', content_lower, re.MULTILINE))
        has_h2 = '## ' in content_lower
        has_h3 = '### ' in content_lower
        has_code = '```' in content_lower
        has_toc = bool(metadata.table_of_contents)
        has_schema = bool(metadata.schema_markup)

        if has_h1: structure_score += 4
        else: recommendations.append("Add H1 heading")
        if has_h2: structure_score += 4
        else: recommendations.append("Add H2 subheadings")
        if has_h3: structure_score += 3
        if has_code: structure_score += 4
        else: recommendations.append("Add code examples")
        if has_toc: structure_score += 3
        if has_schema: structure_score += 2

        score.content_structure = min(20, structure_score)

        # ── Readability (0-15) ───────────────────────────────────
        readability_score = 0
        word_count = post.word_count

        if word_count >= 1500:
            readability_score += 10
        elif word_count >= 800:
            readability_score += 7
        else:
            readability_score += 3
            recommendations.append(f"Content should be 800+ words (currently {word_count})")

        paragraphs = post.content.split('\n\n')
        avg_para_length = sum(len(p.split()) for p in paragraphs) / max(1, len(paragraphs))
        if avg_para_length < 80:
            readability_score += 5
        else:
            recommendations.append("Break long paragraphs into shorter ones")

        score.readability = min(15, readability_score)

        # ── Social ready (0-10) ──────────────────────────────────
        social_score = 0
        if metadata.og_title and metadata.og_description: social_score += 3
        if metadata.og_image: social_score += 3
        if metadata.twitter_card: social_score += 2
        if metadata.schema_markup: social_score += 2

        score.social_ready = min(10, social_score)

        # ── Platform coverage (0-15) — new dimension ────────────
        platform_score = 0
        if platform_content.linkedin_post: platform_score += 4
        if platform_content.twitter_thread: platform_score += 3
        if platform_content.devto_front_matter: platform_score += 3
        if platform_content.hashnode_front_matter: platform_score += 3
        if platform_content.medium_canonical_note: platform_score += 2

        score.platform_coverage = min(15, platform_score)

        # ── Overall ──────────────────────────────────────────────
        score.overall = (
            score.keyword_optimization +
            score.meta_quality +
            score.content_structure +
            score.readability +
            score.social_ready +
            score.platform_coverage
        )

        score.recommendations = recommendations
        return score

    # ─────────────────────────────────────────────────────────────
    # HTML Head Generator
    # ─────────────────────────────────────────────────────────────

    def generate_seo_html_head(self, metadata: SEOMetadata, base_url: str = "") -> str:
        """Generate complete HTML head section with all SEO tags."""
        canonical = metadata.canonical_url or base_url
        og_image_tag = f'<meta property="og:image" content="{metadata.og_image}">' if metadata.og_image else ''
        tw_image_tag = f'<meta name="twitter:image" content="{metadata.og_image}">' if metadata.og_image else ''
        lsi_tag = f'<meta name="keywords" content="{", ".join(metadata.keywords[:5] + metadata.lsi_keywords[:5])}">'

        return f"""<!-- SEO Meta Tags -->
<title>{metadata.meta_title}</title>
<meta name="description" content="{metadata.meta_description}">
{lsi_tag}
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<meta name="author" content="Autonomous Blog Agent">
<meta name="reading-time" content="{metadata.reading_time} min">

<!-- Open Graph -->
<meta property="og:type" content="{metadata.og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{metadata.og_title}">
<meta property="og:description" content="{metadata.og_description}">
{og_image_tag}
<meta property="og:site_name" content="Autonomous Blog Agent">
<meta property="article:published_time" content="{datetime.utcnow().isoformat()}Z">

<!-- Twitter Card -->
<meta name="twitter:card" content="{metadata.twitter_card}">
<meta name="twitter:url" content="{canonical}">
<meta name="twitter:title" content="{metadata.twitter_title}">
<meta name="twitter:description" content="{metadata.twitter_description}">
{tw_image_tag}

<!-- Schema.org Structured Data -->
{metadata.schema_markup}
"""