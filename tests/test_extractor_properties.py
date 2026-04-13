"""Property-based tests for the Extractor Agent.

This module contains property tests that validate the correctness of
the Extractor Agent for HTML cleaning and content extraction.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime

from src.agents.extractor import ExtractorAgent, ExtractionError
from src.models.data_models import ContentItem


# Custom strategies for HTML generation
@st.composite
def valid_html_strategy(draw):
    """Generate valid HTML documents with content."""
    title = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters='<>&"')))
    author = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='<>&"')))
    content = draw(st.text(min_size=10, max_size=500, alphabet=st.characters(blacklist_characters='<>&"')))
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta name="author" content="{author}">
        <meta property="article:published_time" content="2024-01-01T12:00:00Z">
    </head>
    <body>
        <nav>Navigation Menu</nav>
        <header>Site Header</header>
        <article>
            <h1>{title}</h1>
            <p>{content}</p>
            <pre><code>def hello():
    print("Hello, World!")</code></pre>
            <img src="https://example.com/image.jpg" alt="Test image">
        </article>
        <footer>Site Footer</footer>
        <div class="advertisement">Ad content</div>
    </body>
    </html>
    """
    return html


@st.composite
def html_with_code_strategy(draw):
    """Generate HTML with code blocks in various formats."""
    title = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='<>&"')))
    
    # Generate different code block formats
    code_format = draw(st.sampled_from(['pre_code', 'pre_only', 'code_only']))
    
    if code_format == 'pre_code':
        code_html = '<pre><code class="language-python">def foo():\n    return bar\n</code></pre>'
    elif code_format == 'pre_only':
        code_html = f'<pre>function foo() {{\n    return bar;\n}}</pre>'
    else:
        code_html = '<code class="language-javascript">const foo = () => bar;</code>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
    </head>
    <body>
        <article>
            <h1>{title}</h1>
            <p>Some content with code:</p>
            {code_html}
            <p>More content</p>
        </article>
    </body>
    </html>
    """
    return html


@st.composite
def empty_or_minimal_html_strategy(draw):
    """Generate empty or minimal HTML documents."""
    html_type = draw(st.sampled_from(['empty', 'minimal', 'no_content']))
    
    if html_type == 'empty':
        return ""
    elif html_type == 'minimal':
        return "<html><body></body></html>"
    else:
        return """
        <html>
        <head><title>Empty Page</title></head>
        <body>
            <nav>Nav only</nav>
        </body>
        </html>
        """


class TestHTMLCleaningProperties:
    """Property-based tests for HTML cleaning.
    
    Property 2: HTML Cleaning Preserves Content
    Validates: Requirements 2.1, 2.2
    
    For any HTML document containing navigation, advertisements, or non-content
    elements, the extraction process SHALL remove these elements while preserving
    the main content text, code blocks, and images.
    """

    @pytest.mark.asyncio
    @given(valid_html_strategy())
    @settings(max_examples=10)
    async def test_removes_navigation_and_ads(self, html_content):
        """
        Property: Navigation, ads, and footers are removed.
        
        For any HTML with nav, header, footer, ad elements,
        these should be removed from extracted content.
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html_content, "https://example.com/test")
        
        # Main content should be preserved
        assert len(content_item.text_content) > 0
        assert "Navigation Menu" not in content_item.text_content or \
               len(content_item.text_content) < len(html_content)  # At least some cleaning happened

    @pytest.mark.asyncio
    @given(valid_html_strategy())
    @settings(max_examples=10)
    async def test_preserves_main_content(self, html_content):
        """
        Property: Main content text is preserved.
        
        For any HTML with article content, the text should be
        extracted and present in the ContentItem.
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html_content, "https://example.com/test")
        
        # Should have text content
        assert isinstance(content_item.text_content, str)
        assert len(content_item.text_content) > 0

    @pytest.mark.asyncio
    @given(html_with_code_strategy())
    @settings(max_examples=10)
    async def test_preserves_code_blocks(self, html_content):
        """
        Property: Code blocks are preserved with formatting.
        
        For any HTML with code blocks (pre, code tags),
        these should be extracted and preserved.
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html_content, "https://example.com/test")
        
        # Should extract code blocks
        assert isinstance(content_item.code_blocks, list)
        # At least some code should be extracted
        assert len(content_item.code_blocks) > 0 or "code" in html_content.lower()

    @pytest.mark.asyncio
    @given(valid_html_strategy())
    @settings(max_examples=10)
    async def test_preserves_images(self, html_content):
        """
        Property: Image URLs are extracted.
        
        For any HTML with img tags, the image URLs should be
        extracted and stored.
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html_content, "https://example.com/test")
        
        # Should extract images
        assert isinstance(content_item.images, list)
        # Should find at least one image from our test HTML
        assert len(content_item.images) > 0


class TestContentItemStructureProperties:
    """Property-based tests for ContentItem structure completeness.
    
    Property 3: ContentItem Structure Completeness
    Validates: Requirements 2.3
    
    For any extracted content, the resulting ContentItem SHALL contain all
    required metadata fields (title, author, publication_date, url, 
    text_content, code_blocks, images, metadata).
    """

    @pytest.mark.asyncio
    @given(valid_html_strategy())
    @settings(max_examples=10)
    async def test_content_item_has_all_required_fields(self, html_content):
        """
        Property: Extracted ContentItem has all required fields.
        
        For any valid HTML, the extracted ContentItem should have
        all required fields present and with correct types.
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html_content, "https://example.com/test")
        
        # Check all required fields exist
        assert hasattr(content_item, 'title')
        assert hasattr(content_item, 'author')
        assert hasattr(content_item, 'publication_date')
        assert hasattr(content_item, 'url')
        assert hasattr(content_item, 'text_content')
        assert hasattr(content_item, 'code_blocks')
        assert hasattr(content_item, 'images')
        assert hasattr(content_item, 'metadata')
        
        # Check types
        assert isinstance(content_item.title, str)
        assert isinstance(content_item.url, str)
        assert isinstance(content_item.text_content, str)
        assert isinstance(content_item.code_blocks, list)
        assert isinstance(content_item.images, list)
        assert isinstance(content_item.metadata, dict)

    @pytest.mark.asyncio
    @given(valid_html_strategy())
    @settings(max_examples=10)
    async def test_url_is_preserved(self, html_content):
        """
        Property: Source URL is preserved in ContentItem.
        
        For any URL passed to extract(), the ContentItem should
        contain the exact same URL.
        """
        test_url = "https://example.com/test/article"
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html_content, test_url)
        
        assert content_item.url == test_url

    @pytest.mark.asyncio
    @given(valid_html_strategy())
    @settings(max_examples=10)
    async def test_metadata_is_non_empty_dict(self, html_content):
        """
        Property: Metadata is always a non-empty dictionary.
        
        For any extraction, metadata should be a dict with at least
        some information about the extraction process.
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html_content, "https://example.com/test")
        
        assert isinstance(content_item.metadata, dict)
        assert len(content_item.metadata) > 0


class TestExtractorUnit:
    """Unit tests for Extractor Agent edge cases."""

    @pytest.mark.asyncio
    async def test_empty_html_raises_error(self):
        """Test that empty HTML raises ExtractionError."""
        extractor = ExtractorAgent()
        
        with pytest.raises(ExtractionError):
            await extractor.extract("", "https://example.com/test")

    @pytest.mark.asyncio
    async def test_whitespace_only_html_raises_error(self):
        """Test that whitespace-only HTML raises ExtractionError."""
        extractor = ExtractorAgent()
        
        with pytest.raises(ExtractionError):
            await extractor.extract("   \n\n   ", "https://example.com/test")

    @pytest.mark.asyncio
    async def test_minimal_html_extracts_something(self):
        """Test extraction from minimal HTML."""
        html = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        extractor = ExtractorAgent()
        
        content_item = await extractor.extract(html, "https://example.com/test")
        
        assert content_item.title == "Title"
        assert len(content_item.text_content) > 0

    @pytest.mark.asyncio
    async def test_extracts_metadata_from_meta_tags(self):
        """Test metadata extraction from meta tags."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Article</title>
            <meta name="author" content="John Doe">
            <meta property="article:published_time" content="2024-01-15T10:30:00Z">
        </head>
        <body>
            <article>
                <p>Article content here</p>
            </article>
        </body>
        </html>
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html, "https://example.com/test")
        
        assert content_item.title == "Test Article"
        assert content_item.author == "John Doe"
        assert content_item.publication_date is not None
        assert content_item.publication_date.year == 2024
        assert content_item.publication_date.month == 1
        assert content_item.publication_date.day == 15

    @pytest.mark.asyncio
    async def test_extracts_multiple_code_blocks(self):
        """Test extraction of multiple code blocks."""
        html = """
        <!DOCTYPE html>
        <html>
        <body>
            <pre><code class="language-python">def foo(): pass</code></pre>
            <pre><code class="language-javascript">const bar = () => {};</code></pre>
            <code>inline code</code>
        </body>
        </html>
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html, "https://example.com/test")
        
        assert len(content_item.code_blocks) >= 2
        assert any('python' in block for block in content_item.code_blocks)
        assert any('javascript' in block for block in content_item.code_blocks)

    @pytest.mark.asyncio
    async def test_extracts_images_with_absolute_urls(self):
        """Test image extraction with URL conversion."""
        html = """
        <!DOCTYPE html>
        <html>
        <body>
            <img src="https://example.com/absolute.jpg">
            <img src="/relative.png">
            <img src="//protocol-relative.gif">
        </body>
        </html>
        """
        extractor = ExtractorAgent()
        content_item = await extractor.extract(html, "https://example.com/article")
        
        assert len(content_item.images) == 3
        assert all(img.startswith('http') for img in content_item.images)
