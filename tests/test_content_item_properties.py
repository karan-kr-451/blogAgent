"""Property-based tests for ContentItem serialization.

This module contains property tests that validate the correctness of
ContentItem serialization and deserialization operations.
"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime, timezone
from src.models.data_models import ContentItem


# Custom strategies for generating test data
@st.composite
def datetime_strategy(draw):
    """Generate valid datetime objects."""
    # Generate datetime with timezone awareness to avoid issues
    year = draw(st.integers(min_value=2000, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    microsecond = draw(st.integers(min_value=0, max_value=999999))
    
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)


@st.composite
def content_item_strategy(draw):
    """Generate valid ContentItem instances for property testing."""
    title = draw(st.text(min_size=1, max_size=200))
    author = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    publication_date = draw(st.one_of(st.none(), datetime_strategy()))
    url = draw(st.text(min_size=1, max_size=500))
    text_content = draw(st.text(min_size=0, max_size=5000))
    code_blocks = draw(st.lists(st.text(min_size=0, max_size=500), max_size=10))
    images = draw(st.lists(st.text(min_size=0, max_size=500), max_size=10))
    
    # Generate metadata dict with various types
    metadata = draw(st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(
            st.text(max_size=200),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none()
        ),
        max_size=10
    ))
    
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


class TestContentItemSerializationProperties:
    """Property-based tests for ContentItem serialization.
    
    Property 4: ContentItem Serialization Round-Trip
    Validates: Requirements 2.5
    
    For any valid ContentItem, serializing to JSON and then deserializing
    SHALL produce an equivalent ContentItem with all fields preserved.
    """
    
    @given(content_item_strategy())
    def test_serialization_round_trip_preserves_all_fields(self, content_item: ContentItem):
        """
        Property: Serialization round-trip preserves all fields.
        
        For any ContentItem, the following should hold:
        from_json(to_json(item)) == item
        
        This validates that:
        1. All fields are correctly serialized to JSON
        2. All fields are correctly deserialized from JSON
        3. No data is lost or corrupted in the process
        """
        # Serialize to JSON
        json_data = content_item.to_json()
        
        # Deserialize back to ContentItem
        restored_item = ContentItem.from_json(json_data)
        
        # Assert all fields are preserved
        assert restored_item.title == content_item.title
        assert restored_item.author == content_item.author
        assert restored_item.url == content_item.url
        assert restored_item.text_content == content_item.text_content
        assert restored_item.code_blocks == content_item.code_blocks
        assert restored_item.images == content_item.images
        assert restored_item.metadata == content_item.metadata
        
        # Special handling for datetime comparison
        if content_item.publication_date is None:
            assert restored_item.publication_date is None
        else:
            # Compare datetime values (may need to handle timezone/precision)
            assert restored_item.publication_date == content_item.publication_date
    
    @given(content_item_strategy())
    def test_serialization_produces_json_compatible_dict(self, content_item: ContentItem):
        """
        Property: Serialization produces JSON-compatible dictionary.
        
        The to_json() method should produce a dictionary that:
        1. Contains all required fields
        2. Has JSON-serializable values (no datetime objects)
        3. Can be converted to JSON string without errors
        """
        import json
        
        json_data = content_item.to_json()
        
        # Verify it's a dictionary
        assert isinstance(json_data, dict)
        
        # Verify all required fields are present
        required_fields = [
            "title", "author", "publication_date", "url",
            "text_content", "code_blocks", "images", "metadata"
        ]
        for field in required_fields:
            assert field in json_data
        
        # Verify it can be serialized to JSON string
        json_string = json.dumps(json_data)
        assert isinstance(json_string, str)
        
        # Verify it can be deserialized back
        parsed_data = json.loads(json_string)
        assert parsed_data == json_data
    
    @given(content_item_strategy())
    def test_datetime_serialization_format(self, content_item: ContentItem):
        """
        Property: DateTime fields are serialized to ISO format strings.
        
        When publication_date is not None, it should be serialized
        to an ISO format string that can be parsed back.
        """
        json_data = content_item.to_json()
        
        if content_item.publication_date is not None:
            # Should be serialized as string
            assert isinstance(json_data["publication_date"], str)
            
            # Should be parseable back to datetime
            parsed_date = datetime.fromisoformat(json_data["publication_date"])
            assert isinstance(parsed_date, datetime)
            
            # Should match original (accounting for precision)
            assert parsed_date == content_item.publication_date
        else:
            assert json_data["publication_date"] is None
    
    @given(content_item_strategy())
    def test_serialization_idempotency(self, content_item: ContentItem):
        """
        Property: Multiple serialization round-trips produce identical results.
        
        Serializing and deserializing multiple times should produce
        the same result as doing it once.
        """
        # First round-trip
        json_data_1 = content_item.to_json()
        restored_1 = ContentItem.from_json(json_data_1)
        
        # Second round-trip
        json_data_2 = restored_1.to_json()
        restored_2 = ContentItem.from_json(json_data_2)
        
        # Both should be identical
        assert restored_1.title == restored_2.title
        assert restored_1.author == restored_2.author
        assert restored_1.publication_date == restored_2.publication_date
        assert restored_1.url == restored_2.url
        assert restored_1.text_content == restored_2.text_content
        assert restored_1.code_blocks == restored_2.code_blocks
        assert restored_1.images == restored_2.images
        assert restored_1.metadata == restored_2.metadata
    
    @given(content_item_strategy())
    def test_metadata_dict_preservation(self, content_item: ContentItem):
        """
        Property: Metadata dictionary structure is preserved.
        
        The metadata field should maintain its dictionary structure
        and all key-value pairs through serialization.
        """
        json_data = content_item.to_json()
        restored_item = ContentItem.from_json(json_data)
        
        # Metadata should be a dict
        assert isinstance(restored_item.metadata, dict)
        
        # All keys should be preserved
        assert set(restored_item.metadata.keys()) == set(content_item.metadata.keys())
        
        # All values should be preserved
        for key in content_item.metadata:
            assert restored_item.metadata[key] == content_item.metadata[key]
    
    @given(content_item_strategy())
    def test_list_fields_preservation(self, content_item: ContentItem):
        """
        Property: List fields (code_blocks, images) are preserved.
        
        List fields should maintain their order and content through
        serialization and deserialization.
        """
        json_data = content_item.to_json()
        restored_item = ContentItem.from_json(json_data)
        
        # Code blocks should be preserved
        assert isinstance(restored_item.code_blocks, list)
        assert len(restored_item.code_blocks) == len(content_item.code_blocks)
        assert restored_item.code_blocks == content_item.code_blocks
        
        # Images should be preserved
        assert isinstance(restored_item.images, list)
        assert len(restored_item.images) == len(content_item.images)
        assert restored_item.images == content_item.images


# Edge case tests for specific scenarios
class TestContentItemSerializationEdgeCases:
    """Edge case tests for ContentItem serialization."""
    
    def test_empty_content_item_serialization(self):
        """Test serialization of ContentItem with minimal/empty fields."""
        content_item = ContentItem(
            title="",
            author=None,
            publication_date=None,
            url="",
            text_content="",
            code_blocks=[],
            images=[],
            metadata={}
        )
        
        json_data = content_item.to_json()
        restored_item = ContentItem.from_json(json_data)
        
        assert restored_item.title == ""
        assert restored_item.author is None
        assert restored_item.publication_date is None
        assert restored_item.url == ""
        assert restored_item.text_content == ""
        assert restored_item.code_blocks == []
        assert restored_item.images == []
        assert restored_item.metadata == {}
    
    def test_content_item_with_special_characters(self):
        """Test serialization with special characters in text fields."""
        content_item = ContentItem(
            title='Test "Title" with \'quotes\' and \n newlines',
            author="Author with émojis 🎉",
            publication_date=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            url="https://example.com/path?param=value&other=123",
            text_content="Content with\ttabs\nand\nnewlines\rand unicode: 你好",
            code_blocks=['def foo():\n    return "bar"'],
            images=["https://example.com/image.png?size=large"],
            metadata={"key": "value with spaces", "unicode": "测试"}
        )
        
        json_data = content_item.to_json()
        restored_item = ContentItem.from_json(json_data)
        
        assert restored_item.title == content_item.title
        assert restored_item.author == content_item.author
        assert restored_item.text_content == content_item.text_content
        assert restored_item.metadata == content_item.metadata
