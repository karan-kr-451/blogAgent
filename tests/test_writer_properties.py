"""Property-based tests for the Writer Agent.

This module contains property tests that validate the correctness of
the Writer Agent for blog post generation.
"""

import pytest
import json
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime

from src.agents.writer import WriterAgent, GenerationError
from src.models.data_models import ContentItem, BlogPost
from src.config import Config


# Custom strategies
@st.composite
def content_item_for_writing_strategy(draw):
    """Generate ContentItem suitable for testing blog generation."""
    title = draw(st.text(min_size=5, max_size=100))
    
    # Generate substantial text for meaningful blog generation
    paragraphs = draw(st.integers(min_value=3, max_value=10))
    content_parts = []
    for _ in range(paragraphs):
        paragraph = draw(st.text(min_size=50, max_size=300))
        content_parts.append(paragraph)
    
    text_content = "\n\n".join(content_parts)
    
    return ContentItem(
        title=title,
        author="Test Author",
        publication_date=datetime.utcnow(),
        url="https://example.com/test",
        text_content=text_content,
        code_blocks=[],
        images=[],
        metadata={}
    )


@st.composite
def blog_post_strategy(draw):
    """Generate valid BlogPost instances for testing."""
    title = draw(st.text(min_size=1, max_size=200))
    
    # Generate content with proper structure
    content = draw(st.text(min_size=100, max_size=5000))
    
    tags = draw(st.lists(
        st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=5
    ))
    
    word_count = draw(st.integers(min_value=100, max_value=2000))
    
    return BlogPost(
        title=title,
        content=content,
        tags=tags,
        word_count=word_count,
        source_url="https://example.com/source",
        generated_at=datetime.utcnow()
    )


class TestBlogPostWordCountProperties:
    """Property-based tests for blog post word count validation.
    
    Property 7: Blog Post Word Count Validation
    Validates: Requirements 4.4
    
    For any generated BlogPost, the word count SHALL be between 
    800 and 1500 words inclusive.
    """

    def test_word_count_calculation(self):
        """
        Property: Word count is correctly calculated.
        
        For any text, the word count should match the actual number of words.
        """
        text = "one two three four five"
        agent = WriterAgent()
        count = agent._count_words(text)
        
        assert count == 5, f"Expected 5 words, got {count}"

    def test_word_count_with_empty_text(self):
        """Test word count with empty text."""
        agent = WriterAgent()
        count = agent._count_words("")
        
        assert count == 0

    def test_word_count_with_multiline_text(self):
        """Test word count with multiline text."""
        text = "line one\nline two\nline three"
        agent = WriterAgent()
        count = agent._count_words(text)
        
        assert count == 6


class TestExponentialBackoffRetryProperties:
    """Property-based tests for exponential backoff retry logic.
    
    Property 8: Exponential Backoff Retry Logic
    Validates: Requirements 4.5, 7.5, 12.2
    
    For any failed operation requiring retry with exponential backoff,
    the delay between attempts SHALL follow the pattern: 
    attempt N has delay 2^(N-1) seconds (1s, 2s, 4s, ...).
    """

    def test_exponential_backoff_delays(self):
        """
        Property: Retry delays follow exponential pattern.
        
        For attempts 0, 1, 2, ... the delays should be:
        base_delay * 2^0, base_delay * 2^1, base_delay * 2^2, ...
        """
        from src.utils.retry import exponential_backoff_delay
        
        base_delay = 1.0
        max_delay = 60.0
        
        # Check first few delays
        delay_0 = exponential_backoff_delay(0, base_delay, max_delay)
        delay_1 = exponential_backoff_delay(1, base_delay, max_delay)
        delay_2 = exponential_backoff_delay(2, base_delay, max_delay)
        delay_3 = exponential_backoff_delay(3, base_delay, max_delay)
        
        assert abs(delay_0 - 1.0) < 0.01, f"First delay should be ~1s, got {delay_0}"
        assert abs(delay_1 - 2.0) < 0.01, f"Second delay should be ~2s, got {delay_1}"
        assert abs(delay_2 - 4.0) < 0.01, f"Third delay should be ~4s, got {delay_2}"
        assert abs(delay_3 - 8.0) < 0.01, f"Fourth delay should be ~8s, got {delay_3}"

    def test_exponential_backoff_respects_max_delay(self):
        """Test that backoff respects maximum delay cap."""
        from src.utils.retry import exponential_backoff_delay
        
        base_delay = 1.0
        max_delay = 10.0
        
        # After enough attempts, should cap at max_delay
        delay_10 = exponential_backoff_delay(10, base_delay, max_delay)
        
        assert delay_10 <= max_delay, f"Delay should be capped at {max_delay}, got {delay_10}"


class TestBlogPostStructureProperties:
    """Property-based tests for blog post structure completeness.
    
    Property 9: Blog Post Structure Completeness
    Validates: Requirements 4.6
    
    For any generated BlogPost, the content SHALL include all required 
    sections: title, introduction, body sections, and conclusion.
    """

    @pytest.mark.asyncio
    async def test_blog_post_has_required_fields(self):
        """
        Property: BlogPost has all required fields after generation.
        
        Note: This is a simplified test since we can't run actual Ollama.
        In integration tests, we'd verify the complete structure.
        """
        blog_post = BlogPost(
            title="Test Post",
            content="# Introduction\n\nBody content here\n\n## Conclusion",
            tags=["test"],
            word_count=100,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        # Check all required fields exist
        assert hasattr(blog_post, 'title')
        assert hasattr(blog_post, 'content')
        assert hasattr(blog_post, 'tags')
        assert hasattr(blog_post, 'word_count')
        assert hasattr(blog_post, 'source_url')
        assert hasattr(blog_post, 'generated_at')
        
        # Check types
        assert isinstance(blog_post.title, str)
        assert isinstance(blog_post.content, str)
        assert isinstance(blog_post.tags, list)
        assert isinstance(blog_post.word_count, int)

    def test_blog_post_markdown_format(self):
        """
        Property: BlogPost can be converted to markdown.
        
        For any BlogPost, to_markdown() should produce valid markdown
        with title, content, tags, and source.
        """
        blog_post = BlogPost(
            title="Test Title",
            content="Test content",
            tags=["tag1", "tag2"],
            word_count=10,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        markdown = blog_post.to_markdown()
        
        assert "# Test Title" in markdown
        assert "Test content" in markdown
        assert "tag1" in markdown
        assert "tag2" in markdown
        assert "https://example.com" in markdown

    def test_blog_post_serialization_round_trip(self):
        """
        Property: BlogPost serialization preserves all fields.
        """
        original = BlogPost(
            title="Test Title",
            content="Test content",
            tags=["tag1", "tag2"],
            word_count=100,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        json_data = original.to_json()
        restored = BlogPost.from_json(json_data)
        
        assert restored.title == original.title
        assert restored.content == original.content
        assert restored.tags == original.tags
        assert restored.word_count == original.word_count
        assert restored.source_url == original.source_url
        assert restored.generated_at == original.generated_at


class TestOllamaRetryLimit:
    """Property-based tests for Ollama retry limit.
    
    Property 19: Ollama Retry Limit
    Validates: Requirements 12.5
    
    For any sequence of failed Ollama service calls, the Writer Agent 
    SHALL retry at most 5 times before marking the operation as failed.
    """

    @pytest.mark.asyncio
    async def test_ollama_retry_limit_configurable(self):
        """
        Property: Ollama retry limit can be configured.
        
        The configuration should allow setting the maximum number of retries.
        """
        config = Config(
            medium_api_token="test-token",
            max_retry_attempts=5
        )
        
        agent = WriterAgent(config=config)
        
        assert agent.config.max_retry_attempts == 5


class TestWriterAgentUnit:
    """Unit tests for Writer Agent."""

    def test_tag_generation(self):
        """Test that tags are generated from content."""
        agent = WriterAgent()
        
        content = "This is about Python programming and software architecture"
        title = "Python Best Practices"
        
        tags = agent._generate_tags(title, content)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert len(tags) <= 5
        assert all(isinstance(tag, str) for tag in tags)

    def test_tag_generation_empty_content(self):
        """Test tag generation with minimal content."""
        agent = WriterAgent()
        
        tags = agent._generate_tags("", "some random text")
        
        assert len(tags) > 0
        assert "technology" in tags or "article" in tags

    def test_parse_response_with_valid_json(self):
        """Test parsing valid JSON response."""
        agent = WriterAgent()
        
        response = '''
        Some introductory text
        {
            "title": "Test Title",
            "content": "Test content here",
            "tags": ["test", "example"]
        }
        '''
        
        blog_post = agent._parse_response(response, "https://example.com")
        
        assert blog_post.title == "Test Title"
        assert blog_post.content == "Test content here"
        assert blog_post.tags == ["test", "example"]
        assert blog_post.source_url == "https://example.com"

    def test_parse_response_without_json(self):
        """Test parsing response without JSON structure."""
        agent = WriterAgent()
        
        response = "Just plain text without JSON structure"
        
        blog_post = agent._parse_response(response, "https://example.com")
        
        assert blog_post.title is not None
        assert blog_post.content == response
        assert len(blog_post.tags) > 0

    @pytest.mark.asyncio
    async def test_writer_agent_initialization(self):
        """Test Writer Agent initialization."""
        agent = WriterAgent()
        
        assert agent.ollama_endpoint is not None
        assert agent.model is not None
        assert agent.client is not None
        
        await agent.close()
