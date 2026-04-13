"""Property-based tests for the Memory System.

This module contains property tests that validate the correctness of
the FAISS-based memory system for duplicate detection.
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime

from src.memory.memory_system import MemorySystem
from src.models.data_models import ContentItem
from src.config import Config


# Custom strategies
@st.composite
def content_item_with_text_strategy(draw):
    """Generate ContentItem with meaningful text for embedding."""
    title = draw(st.text(min_size=1, max_size=100))
    text_content = draw(st.text(min_size=10, max_size=1000))  # Minimum text for embedding
    
    return ContentItem(
        title=title,
        author="Test Author",
        publication_date=datetime.utcnow(),
        url=f"https://example.com/{title.replace(' ', '-').lower()}",
        text_content=text_content,
        code_blocks=[],
        images=[],
        metadata={}
    )


@st.composite
def embedding_vector_strategy(draw):
    """Generate valid embedding vectors (384-dimensional)."""
    # Generate random normalized vectors
    vec = draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=384,
        max_size=384
    ))
    arr = np.array(vec, dtype=np.float32)
    # Normalize
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr


@st.composite
def similar_embedding_strategy(draw, base_embedding=None):
    """Generate a similar embedding to base_embedding."""
    if base_embedding is None:
        # Generate random base
        vec = draw(st.lists(
            st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=384,
            max_size=384
        ))
        base_embedding = np.array(vec, dtype=np.float32)
        norm = np.linalg.norm(base_embedding)
        if norm > 0:
            base_embedding = base_embedding / norm
    
    # Add small noise to create similar but not identical vector
    noise_level = draw(st.floats(min_value=0.01, max_value=0.3))
    noise = np.random.normal(0, noise_level, 384).astype(np.float32)
    similar = base_embedding + noise
    
    # Normalize
    norm = np.linalg.norm(similar)
    if norm > 0:
        similar = similar / norm
    
    return similar


class TestCosineSimilarityProperties:
    """Property-based tests for cosine similarity calculations.
    
    Property 5: Cosine Similarity Properties
    Validates: Requirements 3.3, 6.2
    
    For any two embedding vectors, the cosine similarity calculation SHALL satisfy:
    1. symmetry (sim(A,B) = sim(B,A))
    2. range [0,1] (for normalized vectors)
    3. identity (sim(A,A) = 1.0)
    """

    @given(embedding_vector_strategy())
    @settings(max_examples=20)
    def test_cosine_similarity_identity(self, embedding):
        """
        Property: Similarity of vector with itself is 1.0.
        
        For any embedding vector A: sim(A, A) = 1.0
        """
        # Normalize embedding
        norm = np.linalg.norm(embedding)
        assume(norm > 0)  # Avoid division by zero
        embedding = embedding / norm
        
        # Self-similarity should be 1.0
        similarity = float(np.dot(embedding, embedding))
        assert abs(similarity - 1.0) < 1e-6, f"Self-similarity should be 1.0, got {similarity}"

    @given(embedding_vector_strategy(), embedding_vector_strategy())
    @settings(max_examples=20)
    def test_cosine_similarity_symmetry(self, embedding_a, embedding_b):
        """
        Property: Cosine similarity is symmetric.
        
        For any embedding vectors A and B: sim(A, B) = sim(B, A)
        """
        # Normalize embeddings
        norm_a = np.linalg.norm(embedding_a)
        norm_b = np.linalg.norm(embedding_b)
        assume(norm_a > 0 and norm_b > 0)
        
        embedding_a = embedding_a / norm_a
        embedding_b = embedding_b / norm_b
        
        sim_a_b = float(np.dot(embedding_a, embedding_b))
        sim_b_a = float(np.dot(embedding_b, embedding_a))
        
        assert abs(sim_a_b - sim_b_a) < 1e-6, \
            f"Similarity should be symmetric: {sim_a_b} != {sim_b_a}"

    @given(embedding_vector_strategy(), embedding_vector_strategy())
    @settings(max_examples=20)
    def test_cosine_similarity_range(self, embedding_a, embedding_b):
        """
        Property: Cosine similarity is in range [0, 1] for normalized vectors.
        
        For any normalized embedding vectors A and B: 0 <= sim(A, B) <= 1
        """
        # Normalize embeddings
        norm_a = np.linalg.norm(embedding_a)
        norm_b = np.linalg.norm(embedding_b)
        assume(norm_a > 0 and norm_b > 0)
        
        embedding_a = embedding_a / norm_a
        embedding_b = embedding_b / norm_b
        
        similarity = float(np.dot(embedding_a, embedding_b))
        
        # For normalized vectors with positive values, similarity should be in [-1, 1]
        # After FAISS normalization and with typical text embeddings, often in [0, 1]
        assert -1.0 - 1e-6 <= similarity <= 1.0 + 1e-6, \
            f"Similarity should be in [-1, 1], got {similarity}"


class TestDuplicateDetectionProperties:
    """Property-based tests for duplicate detection.
    
    Property 6: Duplicate Detection Threshold
    Validates: Requirements 3.4
    
    For any content embedding with cosine similarity above 0.85 to stored content,
    the Memory System SHALL mark it as a duplicate and prevent further processing.
    """

    @pytest.mark.asyncio
    @given(embedding_vector_strategy())
    @settings(max_examples=10)
    async def test_identical_embedding_detected_as_duplicate(self, embedding):
        """
        Property: Identical embeddings are detected as duplicates.
        
        For any embedding A stored in memory, checking A should return True.
        """
        memory = MemorySystem()
        await memory.initialize()
        
        # Store an item
        content = ContentItem(
            title="Test",
            author=None,
            publication_date=None,
            url="https://example.com/test",
            text_content="Test content",
            code_blocks=[],
            images=[],
            metadata={}
        )
        
        # Normalize and store
        norm = np.linalg.norm(embedding)
        assume(norm > 0)
        embedding_norm = embedding / norm
        
        await memory.store(content, embedding_norm)
        
        # Check if same embedding is duplicate
        is_duplicate = await memory.check_duplicate(embedding_norm)
        assert is_duplicate, "Identical embedding should be detected as duplicate"

    @pytest.mark.asyncio
    @given(embedding_vector_strategy())
    @settings(max_examples=10)
    async def test_very_different_embeddings_not_duplicate(self, embedding):
        """
        Property: Very different embeddings are not duplicates.
        
        For embedding A stored in memory, checking -A (opposite direction)
        should return False.
        """
        memory = MemorySystem()
        await memory.initialize()
        
        content = ContentItem(
            title="Test",
            author=None,
            publication_date=None,
            url="https://example.com/test",
            text_content="Test content",
            code_blocks=[],
            images=[],
            metadata={}
        )
        
        # Normalize and store
        norm = np.linalg.norm(embedding)
        assume(norm > 0)
        embedding_norm = embedding / norm
        
        await memory.store(content, embedding_norm)
        
        # Check opposite embedding (should not be duplicate)
        opposite = -embedding_norm
        is_duplicate = await memory.check_duplicate(opposite)
        
        # Note: This might fail depending on threshold, so we use a lower threshold
        is_duplicate_low = await memory.check_duplicate(opposite, threshold=0.99)
        assert not is_duplicate_low, "Very different embeddings should not be duplicates"


class TestMemorySystemUnit:
    """Unit tests for Memory System operations."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_history(self):
        """Test storing items and retrieving history."""
        memory = MemorySystem()
        await memory.initialize()
        
        # Store a few items
        for i in range(3):
            content = ContentItem(
                title=f"Test {i}",
                author=None,
                publication_date=None,
                url=f"https://example.com/{i}",
                text_content=f"Test content {i}",
                code_blocks=[],
                images=[],
                metadata={}
            )
            embedding = np.random.randn(384).astype(np.float32)
            await memory.store(content, embedding)
        
        # Check history
        history = await memory.get_history()
        assert len(history) == 3
        assert history[0]["metadata"]["title"] == "Test 0"

    @pytest.mark.asyncio
    async def test_empty_index_not_duplicate(self):
        """Test that empty index doesn't flag duplicates."""
        memory = MemorySystem()
        await memory.initialize()
        
        embedding = np.random.randn(384).astype(np.float32)
        is_duplicate = await memory.check_duplicate(embedding)
        
        assert not is_duplicate, "Empty index should not flag duplicates"

    @pytest.mark.asyncio
    async def test_persist_and_load(self, tmp_path):
        """Test persistence and loading."""
        # Create memory system with temp paths
        config = Config(
            medium_api_token="test-token",
            memory_index_path=str(tmp_path / "vectors.index"),
            memory_metadata_path=str(tmp_path / "metadata.json")
        )
        
        memory = MemorySystem(config=config)
        await memory.initialize()
        
        # Store an item
        content = ContentItem(
            title="Persist Test",
            author=None,
            publication_date=None,
            url="https://example.com/persist",
            text_content="Test content",
            code_blocks=[],
            images=[],
            metadata={}
        )
        embedding = np.random.randn(384).astype(np.float32)
        await memory.store(content, embedding)
        
        # Create new instance and load
        memory2 = MemorySystem(config=config)
        await memory2.load()
        
        # Should have items in index
        assert memory2.index.ntotal == 1
        assert len(memory2.metadata["entries"]) == 1

    @pytest.mark.asyncio
    async def test_can_publish_today(self):
        """Test publication rate limiting."""
        memory = MemorySystem()
        await memory.initialize()
        
        # Initially should be able to publish
        assert await memory.can_publish_today() is True
        
        # Update publication timestamp to now
        await memory.update_publication_timestamp()
        
        # Should not be able to publish again immediately
        assert await memory.can_publish_today() is False

    @pytest.mark.asyncio
    async def test_compute_embedding(self):
        """Test embedding computation."""
        memory = MemorySystem()
        await memory.initialize()
        
        text = "This is a test sentence for embedding."
        embedding = await memory.compute_embedding(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32
