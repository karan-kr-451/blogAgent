"""Memory System with FAISS for duplicate detection and content tracking."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from fastembed import TextEmbedding

from src.config import Config, get_config
from src.logging_config import get_logger
from src.models.data_models import ContentItem

logger = get_logger(__name__)


class MemorySystemError(Exception):
    """Base exception for memory system errors."""
    pass


class DuplicateError(MemorySystemError):
    """Raised when content is detected as a duplicate."""
    pass


class MemorySystem:
    """
    FAISS-based vector storage for content tracking and duplicate detection.
    
    This system uses sentence embeddings to detect duplicate content
    by comparing cosine similarity between content items.
    """
    _instance = None
    _model_cache: TextEmbedding | None = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MemorySystem, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Config | None = None):
        """
        Initialize the memory system.
        """
        if self._initialized:
            return
            
        self.config = config or get_config()
        self.embedding_dimension = 384  # paraphrase-MiniLM-L3-v2 dimension
        self.index: faiss.Index | None = None
        self.metadata: dict[str, Any] = {
            "entries": [],
            "stats": {
                "total_processed": 0,
                "duplicates_detected": 0,
                "last_publication": None
            },
            "replied_comment_ids": []
        }
        self.embedding_model: TextEmbedding | None = None
        
        # Paths for persistence
        self.index_path = Path(self.config.memory_index_path)
        self.metadata_path = Path(self.config.memory_metadata_path)
        
        logger.info(
            "MemorySystem instance created",
            extra={
                "agent": "MemorySystem",
                "index_path": str(self.index_path),
                "metadata_path": str(self.metadata_path)
            }
        )
        self._initialized = True

    async def initialize(self) -> None:
        """Initialize FAISS index and embedding model."""
        if self.embedding_model is not None:
            return
            
        # Load or create FAISS index
        await self.load()
        
        # Load embedding model (shared across instances)
        if MemorySystem._model_cache is None:
            import asyncio
            logger.info("Loading lightweight embedding model via fastembed (ONNX)", extra={"agent": "MemorySystem"})
            loop = asyncio.get_event_loop()
            # fastembed loads the model lazily, but we want to trigger it now
            # default model is BAAI/bge-small-en-v1.5 (384 dims, highly efficient)
            MemorySystem._model_cache = await loop.run_in_executor(
                None, lambda: TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            )
            logger.info("Embedding model initialized", extra={"agent": "MemorySystem"})
        
        self.embedding_model = MemorySystem._model_cache

    def _create_empty_index(self) -> faiss.Index:
        """Create a new empty FAISS index."""
        index = faiss.IndexFlatIP(self.embedding_dimension)  # Inner product for cosine similarity
        # Normalize vectors for cosine similarity
        index = faiss.IndexIDMap2(index)
        return index

    async def store(self, content: ContentItem, embedding: np.ndarray) -> None:
        """
        Store content item with its embedding.
        
        Args:
            content: ContentItem to store
            embedding: Embedding vector for the content
        
        Raises:
            MemorySystemError: If storage fails
        """
        try:
            if self.embedding_model is None:
                await self.initialize()
            
            # Generate unique ID for this content
            content_id = str(uuid.uuid4())
            
            # Normalize embedding vector for cosine similarity
            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)
            
            faiss.normalize_L2(embedding)
            
            # Add to FAISS index
            if self.index is None:
                self.index = self._create_empty_index()

            self.index.add_with_ids(
                embedding.astype(np.float32),
                np.array([hash(content_id) % 1000000], dtype=np.int64)
            )
            
            # Store metadata
            entry = {
                "content_id": content_id,
                "metadata": {
                    "title": content.title,
                    "url": content.url,
                    "processed_at": datetime.utcnow().isoformat()
                }
            }
            self.metadata["entries"].append(entry)
            self.metadata["stats"]["total_processed"] += 1
            
            # Persist to disk
            await self.persist()
            
            logger.info(
                f"Stored content: {content.title}",
                extra={
                    "agent": "MemorySystem",
                    "content_id": content_id,
                    "url": content.url
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to store content: {e}", extra={"agent": "MemorySystem"})
            raise MemorySystemError(f"Failed to store content: {e}") from e

    async def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """
        Search for relevant content based on a text query.
        
        Args:
            query: Search query text
            limit: Number of results to return
            
        Returns:
            List of matching metadata entries
        """
        try:
            if self.index is None or self.index.ntotal == 0:
                return []
            
            # Compute query embedding
            embedding = await self.compute_embedding(query)
            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)
            
            faiss.normalize_L2(embedding)
            
            # Search
            k = min(limit, self.index.ntotal)
            scores, indices = self.index.search(embedding.astype(np.float32), k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(self.metadata["entries"]):
                    entry = self.metadata["entries"][int(idx)]
                    results.append({
                        **entry,
                        "similarity_score": float(scores[0][i])
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}", extra={"agent": "MemorySystem"})
            return []

    async def check_duplicate(self, embedding: np.ndarray, threshold: float | None = None) -> bool:
        """
        Check if content is a duplicate based on embedding similarity.
        
        Args:
            embedding: Content embedding vector
            threshold: Similarity threshold (defaults to config value)
        
        Returns:
            True if duplicate found, False otherwise
        
        Raises:
            MemorySystemError: If check fails
        """
        try:
            if self.index is None:
                await self.initialize()
            
            if self.index.ntotal == 0:
                # No items in index, can't be duplicate
                return False
            
            threshold = threshold or self.config.duplicate_threshold
            
            # Normalize embedding
            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)
            
            faiss.normalize_L2(embedding)
            
            # Search for similar vectors
            k = min(5, self.index.ntotal)  # Search top-5 most similar
            scores, indices = self.index.search(embedding.astype(np.float32), k)
            
            # Check if any score exceeds threshold
            max_similarity = float(np.max(scores)) if len(scores) > 0 else 0.0
            
            is_duplicate = max_similarity > threshold
            
            if is_duplicate:
                self.metadata["stats"]["duplicates_detected"] += 1
                logger.info(
                    f"Duplicate detected (similarity: {max_similarity:.3f})",
                    extra={"agent": "MemorySystem", "similarity": max_similarity}
                )
            else:
                logger.debug(
                    f"No duplicate found (max similarity: {max_similarity:.3f})",
                    extra={"agent": "MemorySystem", "similarity": max_similarity}
                )
            
            return is_duplicate
            
        except Exception as e:
            logger.error(f"Failed to check duplicate: {e}", extra={"agent": "MemorySystem"})
            raise MemorySystemError(f"Failed to check duplicate: {e}") from e

    async def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Retrieve processing history.
        
        Args:
            limit: Maximum number of entries to return
        
        Returns:
            List of metadata entries
        """
        return self.metadata["entries"][-limit:]

    async def get_stats(self) -> dict[str, Any]:
        """Get memory system statistics."""
        return {
            **self.metadata["stats"],
            "total_items_in_index": self.index.ntotal if self.index else 0
        }

    async def update_publication_timestamp(self) -> None:
        """Update last publication timestamp."""
        self.metadata["stats"]["last_publication"] = datetime.utcnow().isoformat()
        await self.persist()

    async def can_publish_today(self) -> bool:
        """Check if daily publication limit reached."""
        last_pub = self.metadata["stats"].get("last_publication")
        if last_pub is None:
            return True
        
        last_pub_dt = datetime.fromisoformat(last_pub)
        hours_since = (datetime.utcnow() - last_pub_dt).total_seconds() / 3600
        
        return hours_since >= 24

    async def is_comment_replied(self, comment_id: str) -> bool:
        """Check if a comment has already been replied to."""
        return comment_id in self.metadata.get("replied_comment_ids", [])

    async def mark_comment_replied(self, comment_id: str) -> None:
        """Mark a comment as replied."""
        if "replied_comment_ids" not in self.metadata:
            self.metadata["replied_comment_ids"] = []
        
        if comment_id not in self.metadata["replied_comment_ids"]:
            self.metadata["replied_comment_ids"].append(comment_id)
            await self.persist()

    async def persist(self) -> None:
        """
        Save index and metadata to disk.
        
        Raises:
            MemorySystemError: If persistence fails
        """
        try:
            # Ensure directories exist
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            if self.index is not None:
                faiss.write_index(self.index, str(self.index_path))
                logger.debug(f"FAISS index saved to {self.index_path}")
            
            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.debug(f"Metadata saved to {self.metadata_path}")
            
        except Exception as e:
            logger.error(f"Failed to persist memory system: {e}", extra={"agent": "MemorySystem"})
            raise MemorySystemError(f"Failed to persist memory system: {e}") from e

    async def load(self) -> None:
        """
        Load index and metadata from disk. Handles corruption by rebuilding.
        
        Raises:
            MemorySystemError: If loading fails and cannot recover
        """
        try:
            # Try to load FAISS index
            if self.index_path.exists():
                try:
                    self.index = faiss.read_index(str(self.index_path))
                    logger.info(f"FAISS index loaded from {self.index_path}")
                except Exception as e:
                    logger.warning(f"Failed to load FAISS index, creating new one: {e}")
                    self.index = self._create_empty_index()
            else:
                self.index = self._create_empty_index()
                logger.info("Created new FAISS index")
            
            # Try to load metadata
            if self.metadata_path.exists():
                try:
                    with open(self.metadata_path, 'r', encoding='utf-8') as f:
                        self.metadata = json.load(f)
                    logger.info(f"Metadata loaded from {self.metadata_path}")
                except Exception as e:
                    logger.warning(f"Failed to load metadata, using defaults: {e}")
                    self.metadata = {
                        "entries": [],
                        "stats": {
                            "total_processed": 0,
                            "duplicates_detected": 0,
                            "last_publication": None
                        },
                        "replied_comment_ids": []
                    }
            else:
                logger.info("No metadata file found, using defaults")
                
        except Exception as e:
            logger.error(f"Failed to load memory system: {e}", extra={"agent": "MemorySystem"})
            # Attempt to recover with empty state
            self.index = self._create_empty_index()
            self.metadata = {
                "entries": [],
                "stats": {
                    "total_processed": 0,
                    "duplicates_detected": 0,
                    "last_publication": None
                },
                "replied_comment_ids": []
            }
            logger.info("Recovered with empty memory state")

    async def compute_embedding(self, text: str) -> np.ndarray:
        """
        Compute embedding for text using the embedding model.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        
        Raises:
            MemorySystemError: If embedding fails
        """
        try:
            import asyncio
            if self.embedding_model is None:
                await self.initialize()
            
            if self.embedding_model is None:
                raise MemorySystemError("Embedding model not available")
            
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, lambda: list(self.embedding_model.embed([text]))
            )
            if not embeddings:
                raise MemorySystemError("Embedding failed to generate output")
            
            return np.array(embeddings[0]).astype(np.float32)
            
        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}", extra={"agent": "MemorySystem"})
            raise MemorySystemError(f"Failed to compute embedding: {e}") from e
