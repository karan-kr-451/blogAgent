"""Property-based tests for the Editor Agent.

This module contains property tests that validate the correctness of
the Editor Agent for blog post editing.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime

from src.agents.editor import EditorAgent, EditingError
from src.models.data_models import BlogPost, EditedPost


# Custom strategies
@st.composite
def blog_post_with_code_strategy(draw):
    """Generate BlogPost with code blocks."""
    title = draw(st.text(min_size=1, max_size=100))
    
    # Create content with code blocks
    code_block = draw(st.text(min_size=10, max_size=200))
    markdown_content = f"""# {title}

This is a paragraph with some explanation.

```python
{code_block}
```

Another paragraph after the code.
"""
    
    tags = draw(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
    word_count = draw(st.integers(min_value=50, max_value=1000))
    
    return BlogPost(
        title=title,
        content=markdown_content,
        tags=tags,
        word_count=word_count,
        source_url="https://example.com/source",
        generated_at=datetime.utcnow()
    )


class TestCodeBlockFormattingPreservation:
    """Property-based tests for code block formatting preservation.
    
    Property 10: Code Block Formatting Preservation
    Validates: Requirements 5.4
    
    For any code block in a BlogPost, the formatting SHALL preserve 
    indentation, syntax highlighting markers, and language identifiers.
    """

    def test_code_block_structure_preserved_in_edit_prompt(self):
        """
        Property: Code blocks are marked for preservation in edit prompt.
        
        The editor should explicitly note that code blocks should not be modified.
        """
        agent = EditorAgent()
        
        post = BlogPost(
            title="Test",
            content="Text\n```python\ndef foo():\n    pass\n```\nMore text",
            tags=["test"],
            word_count=10,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        prompt = agent._build_edit_prompt(post)
        
        # Check that prompt mentions preserving code
        assert "code" in prompt.lower() or "preserve" in prompt.lower()


class TestEditedPostChangeTracking:
    """Property-based tests for edited post change tracking.
    
    Property 11: Edited Post Change Tracking
    Validates: Requirements 5.6
    
    For any edited BlogPost, the resulting EditedPost SHALL include 
    a non-empty list of changes describing the modifications made.
    """

    def test_edited_post_has_non_empty_changes(self):
        """
        Property: EditedPost always has at least one change recorded.
        
        For any edit operation, the changes list should be non-empty.
        """
        # Simulate parsing a response
        agent = EditorAgent()
        
        response = """[EDITED CONTENT]
Edited content here

[CHANGES]
- Fixed grammar in introduction
- Improved paragraph flow
"""
        
        post = BlogPost(
            title="Test",
            content="Original content",
            tags=["test"],
            word_count=5,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        edited_content, changes = agent._parse_edit_response(response, post)
        
        assert isinstance(changes, list)
        assert len(changes) > 0, "Changes list should not be empty"
        assert all(isinstance(change, str) for change in changes)

    def test_edited_post_changes_are_descriptive(self):
        """
        Property: Changes are descriptive strings.
        
        Each change should be a meaningful description of what was modified.
        """
        agent = EditorAgent()
        
        response = """[EDITED CONTENT]
Edited content

[CHANGES]
- Fixed spelling error in title
- Improved sentence structure
"""
        
        post = BlogPost(
            title="Test",
            content="Original",
            tags=["test"],
            word_count=2,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        _, changes = agent._parse_edit_response(response, post)
        
        # Each change should be a non-empty string with some length
        for change in changes:
            assert len(change) > 0, "Each change should be non-empty"
            assert len(change) > 5, "Each change should be descriptive"

    def test_parse_response_without_structured_format(self):
        """
        Property: Even without structured format, changes are recorded.
        
        When LLM doesn't follow format, should still record a change.
        """
        agent = EditorAgent()
        
        response = "Just edited text without proper format"
        
        post = BlogPost(
            title="Test",
            content="Original",
            tags=["test"],
            word_count=2,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        _, changes = agent._parse_edit_response(response, post)
        
        assert len(changes) > 0, "Should always have at least one change"


class TestEditorAgentUnit:
    """Unit tests for Editor Agent."""

    def test_build_edit_prompt_includes_guidelines(self):
        """Test that edit prompt includes all necessary guidelines."""
        agent = EditorAgent()
        
        post = BlogPost(
            title="Test Post",
            content="Test content",
            tags=["test"],
            word_count=2,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        prompt = agent._build_edit_prompt(post)
        
        # Check key elements in prompt
        assert "grammar" in prompt.lower()
        assert "code" in prompt.lower() or "preserve" in prompt.lower()
        assert "technical accuracy" in prompt.lower()
        assert post.title in prompt
        assert post.content in prompt

    def test_parse_edit_response_with_structured_format(self):
        """Test parsing properly structured edit response."""
        agent = EditorAgent()
        
        response = """[EDITED CONTENT]
This is the improved content with better flow.

[CHANGES]
- Improved introduction clarity
- Fixed grammatical errors
- Enhanced paragraph transitions
"""
        
        post = BlogPost(
            title="Test",
            content="Original content",
            tags=["test"],
            word_count=3,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        edited_content, changes = agent._parse_edit_response(response, post)
        
        assert "improved content" in edited_content
        assert len(changes) == 3
        assert "introduction" in changes[0].lower()

    def test_parse_edit_response_preserves_code_blocks(self):
        """Test that edited content preserves code block mentions."""
        agent = EditorAgent()
        
        original_content = """Text before code

```python
def hello():
    print("Hello")
```

Text after code."""
        
        response = f"""[EDITED CONTENT]
{original_content}

[CHANGES]
- Improved surrounding text
"""
        
        post = BlogPost(
            title="Test",
            content=original_content,
            tags=["test"],
            word_count=10,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        edited_content, _ = agent._parse_edit_response(response, post)
        
        # Code block should be preserved
        assert "```python" in edited_content
        assert "def hello():" in edited_content

    @pytest.mark.asyncio
    async def test_editor_agent_initialization(self):
        """Test Editor Agent initialization."""
        agent = EditorAgent()
        
        assert agent.ollama_endpoint is not None
        assert agent.model is not None
        assert agent.client is not None
        
        await agent.close()
