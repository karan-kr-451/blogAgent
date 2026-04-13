"""Extractor Agent for cleaning and structuring web content."""

import re
import logging
import os
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup
import trafilatura

from src.logging_config import get_logger
from src.models.data_models import ContentItem

logger = get_logger(__name__)


class ExtractionError(Exception):
    """Raised when content extraction fails."""
    pass


class ExtractorAgent:
    """
    Agent that cleans and structures raw HTML into usable content.
    
    Downloads images, architecture diagrams, and embeds them in markdown.
    """
    
    def __init__(self, images_dir: str = "drafts/images"):
        """
        Initialize the Extractor Agent.
        
        Args:
            images_dir: Directory to save downloaded images
        """
        self.images_dir = Path(images_dir)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.http_client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"ExtractorAgent initialized, images: {images_dir}")

    async def extract(self, raw_html: str, url: str) -> ContentItem:
        """
        Extract and structure content from raw HTML.
        
        Downloads images and architecture diagrams, embeds them in content.
        
        Args:
            raw_html: Raw HTML from crawler
            url: Source URL
        
        Returns:
            Structured ContentItem with embedded images
        
        Raises:
            ExtractionError: If extraction fails
        """
        try:
            if not raw_html or not raw_html.strip():
                raise ExtractionError("Empty HTML provided")
            
            # Try trafilatura first for better content extraction
            content_item = await self._extract_with_trafilatura(raw_html, url)
            
            # Fallback to BeautifulSoup if trafilatura fails
            if content_item is None:
                content_item = await self._extract_with_beautifulsoup(raw_html, url)
            
            if content_item is None:
                raise ExtractionError("Failed to extract content using both methods")
            
            # Download images and create markdown embeds
            if content_item.images:
                local_images = await self._download_images(content_item.images, url)
                
                # Embed images in content as markdown
                if local_images:
                    image_section = "\n\n## Architecture Diagrams & Visual Workflows\n\n"
                    for i, img_path in enumerate(local_images):
                        image_section += f"![Architecture Diagram {i+1}]({img_path})\n\n"
                    
                    content_item.text_content += image_section
                    content_item.metadata['downloaded_images'] = local_images
                    content_item.metadata['image_count'] = len(local_images)
            
            logger.info(
                f"Extracted content: {content_item.title}",
                extra={
                    "agent": "ExtractorAgent",
                    "url": url,
                    "title": content_item.title,
                    "images": len(content_item.images)
                }
            )
            
            return content_item
            
        except ExtractionError:
            raise
        except Exception as e:
            logger.error(f"Extraction failed: {e}", extra={"agent": "ExtractorAgent", "url": url})
            raise ExtractionError(f"Extraction failed: {e}") from e

    async def _extract_with_trafilatura(self, raw_html: str, url: str) -> ContentItem | None:
        """
        Extract content using trafilatura.
        
        Args:
            raw_html: Raw HTML
            url: Source URL
        
        Returns:
            ContentItem or None if extraction fails
        """
        try:
            # Extract main text content
            text_content = trafilatura.extract(raw_html, include_comments=False, include_tables=True)
            
            if not text_content or not text_content.strip():
                return None
            
            # Parse with BeautifulSoup for metadata
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Extract metadata
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            publication_date = self._extract_publication_date(soup)
            
            # Extract code blocks
            code_blocks = self._extract_code_blocks(soup)
            
            # Extract images
            images = self._extract_images(soup, url)
            
            # Build metadata
            metadata = {
                "extraction_method": "trafilatura",
                "original_html_length": len(raw_html),
                "extracted_text_length": len(text_content),
                "images_found": len(images)
            }
            
            return ContentItem(
                title=title,
                author=author,
                publication_date=publication_date,
                url=url,
                text_content=text_content,
                code_blocks=code_blocks,
                images=images,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {e}")
            return None

    async def _download_images(self, images: list[str], url: str) -> list[str]:
        """
        Download images from URLs to local directory concurrently.
        
        Args:
            images: List of image URLs
            url: Source URL (for creating unique directory)
        
        Returns:
            List of local image paths for markdown embedding
        """
        import hashlib
        
        # Create unique directory for this URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        image_dir = self.images_dir / f"{url_hash}"
        image_dir.mkdir(parents=True, exist_ok=True)
        
        candidates = images[:10]  # Cap at 10 images per post
        logger.info(f"Downloading {len(candidates)} images to {image_dir}")
        
        sem = asyncio.Semaphore(5)  # max 5 concurrent downloads
        
        async def _fetch_one(i: int, img_url: str) -> str | None:
            async with sem:
                try:
                    ext = '.png'
                    if any(x in img_url.lower() for x in ['.jpg', '.jpeg']):
                        ext = '.jpg'
                    elif '.gif' in img_url.lower():
                        ext = '.gif'
                    elif '.webp' in img_url.lower():
                        ext = '.webp'
                    
                    local_path = image_dir / f"diagram-{i+1}{ext}"
                    response = await self.http_client.get(img_url, follow_redirects=True, timeout=10.0)
                    response.raise_for_status()
                    
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    relative_path = f"./images/{url_hash}/diagram-{i+1}{ext}"
                    logger.info(f"  ✅ Downloaded: {relative_path}")
                    return relative_path
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to download {img_url}: {e}")
                    return None
        
        results = await asyncio.gather(*[_fetch_one(i, u) for i, u in enumerate(candidates)])
        local_images = [r for r in results if r is not None]
        
        logger.info(f"✅ Downloaded {len(local_images)}/{len(candidates)} images")
        return local_images

    async def _extract_with_beautifulsoup(self, raw_html: str, url: str) -> ContentItem:
        """
        Extract content using BeautifulSoup as fallback.
        
        Args:
            raw_html: Raw HTML
            url: Source URL
        
        Returns:
            ContentItem
        """
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # Remove unwanted elements
        self._remove_unwanted_elements(soup)
        
        # Extract metadata
        title = self._extract_title(soup)
        author = self._extract_author(soup)
        publication_date = self._extract_publication_date(soup)
        
        # Extract text content
        text_content = self._extract_text_content(soup)
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(soup)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        # Build metadata
        metadata = {
            "extraction_method": "beautifulsoup",
            "original_html_length": len(raw_html),
            "extracted_text_length": len(text_content)
        }
        
        return ContentItem(
            title=title,
            author=author,
            publication_date=publication_date,
            url=url,
            text_content=text_content,
            code_blocks=code_blocks,
            images=images,
            metadata=metadata
        )

    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """
        Remove navigation, ads, footers, and other non-content elements.
        
        Args:
            soup: BeautifulSoup object
        """
        # Tags to remove
        unwanted_tags = ['script', 'style', 'nav', 'header', 'footer', 'aside']
        
        # Classes that indicate non-content
        unwanted_classes = [
            'nav', 'navigation', 'menu', 'sidebar', 'header', 'footer',
            'ad', 'advertisement', 'ads', 'banner', 'cookie', 'popup',
            'comments', 'share', 'social', 'related', 'newsletter'
        ]
        
        # Remove unwanted tags
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove elements with unwanted classes
        for element in soup.find_all(True):
            classes = element.get('class', [])
            if any(cls in ' '.join(classes).lower() for cls in unwanted_classes):
                element.decompose()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract page title from HTML.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Title string
        """
        # Try og:title first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']
        
        # Try meta title
        meta_title = soup.find('meta', attrs={'name': 'title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content']
        
        # Try h1
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)
        
        # Try title tag
        if soup.title and soup.title.string:
            return soup.title.string
        
        return "Untitled"

    def _extract_author(self, soup: BeautifulSoup) -> str | None:
        """
        Extract author from HTML.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Author string or None
        """
        # Try meta author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content']
        
        # Try article:author
        article_author = soup.find('meta', property='article:author')
        if article_author and article_author.get('content'):
            return article_author['content']
        
        # Try rel="author"
        author_link = soup.find('a', rel='author')
        if author_link and author_link.get_text(strip=True):
            return author_link.get_text(strip=True)
        
        return None

    def _extract_publication_date(self, soup: BeautifulSoup) -> datetime | None:
        """
        Extract publication date from HTML.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            datetime or None
        """
        # Try article:published_time
        pub_time = soup.find('meta', property='article:published_time')
        if pub_time and pub_time.get('content'):
            try:
                return datetime.fromisoformat(pub_time['content'].rstrip('Z'))
            except (ValueError, AttributeError):
                pass
        
        # Try time tag with datetime attribute
        time_tag = soup.find('time', datetime=True)
        if time_tag:
            try:
                return datetime.fromisoformat(time_tag['datetime'].rstrip('Z'))
            except (ValueError, AttributeError):
                pass
        
        # Try meta date
        meta_date = soup.find('meta', attrs={'name': 'date'})
        if meta_date and meta_date.get('content'):
            try:
                return datetime.fromisoformat(meta_date['content'].rstrip('Z'))
            except (ValueError, AttributeError):
                pass
        
        return None

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract clean text content from HTML.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Clean text string
        """
        # Get text and clean it up
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def _extract_code_blocks(self, soup: BeautifulSoup) -> list[str]:
        """
        Extract code blocks from HTML.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            List of code block strings
        """
        code_blocks = []
        
        # Find all pre and code tags
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                code_text = code.get_text()
                # Try to detect language from class
                lang = self._detect_language_from_class(code)
                if lang:
                    code_blocks.append(f"```{lang}\n{code_text}\n```")
                else:
                    code_blocks.append(f"```\n{code_text}\n```")
            else:
                code_text = pre.get_text()
                code_blocks.append(f"```\n{code_text}\n```")
        
        # Also check standalone code tags
        for code in soup.find_all('code'):
            if code.parent.name not in ['pre', 'code']:
                code_text = code.get_text()
                lang = self._detect_language_from_class(code)
                if lang:
                    code_blocks.append(f"```{lang}\n{code_text}\n```")
                else:
                    code_blocks.append(f"```\n{code_text}\n```")
        
        return code_blocks

    def _detect_language_from_class(self, tag) -> str | None:
        """
        Detect programming language from CSS class.
        
        Args:
            tag: BeautifulSoup tag
        
        Returns:
            Language string or None
        """
        classes = tag.get('class', [])
        language_classes = [
            'language-python', 'language-javascript', 'language-typescript',
            'language-java', 'language-cpp', 'language-c', 'language-go',
            'language-rust', 'language-ruby', 'language-php', 'language-swift',
            'language-kotlin', 'language-scala', 'language-sql', 'language-bash',
            'language-shell', 'language-yaml', 'language-json', 'language-xml',
            'language-html', 'language-css', 'language-dockerfile'
        ]
        
        for cls in classes:
            if cls.startswith('language-'):
                return cls.replace('language-', '')
        
        return None

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """
        Extract image URLs from HTML.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative paths
        
        Returns:
            List of image URLs (architecture diagrams, screenshots, etc.)
        """
        images = []
        
        for img in soup.find_all('img', src=True):
            src = img['src']
            
            # Skip tiny tracking pixels and icons
            if any(skip in src.lower() for skip in ['favicon', 'pixel', 'spacer', 'icon']):
                continue
            
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                # Simple absolute path
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            elif not src.startswith(('http://', 'https://')):
                # Relative path
                if base_url.endswith('/'):
                    src = base_url + src
                else:
                    src = base_url + '/' + src
            
            images.append(src)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        logger.info(f"Extracted {len(unique_images)} unique images from {base_url}")
        return unique_images
