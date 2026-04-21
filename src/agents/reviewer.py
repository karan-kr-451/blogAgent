"""Reviewer Agent for validating content originality."""

import re
import logging
from datetime import datetime
from typing import Any
from collections import Counter

import numpy as np
from fastembed import TextEmbedding

from src.config import Config, get_config
from src.logging_config import get_logger
from src.models.data_models import ContentItem, BlogPost, ReviewResult, ReviewDecision
from src.memory.memory_system import MemorySystem

logger = get_logger(__name__)


class ReviewError(Exception):
    """Raised when content review fails."""
    pass


class ReviewerAgent:
    """
    Agent that validates content originality against source material.
    
    Uses sentence embeddings and n-gram overlap detection to identify
    potential plagiarism or excessive similarity to source content.
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize the Reviewer Agent.
        
        Args:
            config: Application configuration. If None, uses global config.
        """
        self.config = config or get_config()
        self.similarity_threshold = self.config.review_similarity_threshold
        self.embedding_model: TextEmbedding | None = None
        self.memory_system = MemorySystem(config=self.config)
        
        logger.info(
            "ReviewerAgent initialized",
            extra={
                "agent": "ReviewerAgent",
                "similarity_threshold": self.similarity_threshold
            }
        )

    async def initialize(self) -> None:
        """Initialize the embedding model."""
        if self.embedding_model is None:
            logger.info("Loading embedding model for review via fastembed")
            self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            logger.info("Embedding model loaded for review")
        
        await self.memory_system.initialize()

    async def review(self, post: BlogPost, source: ContentItem) -> ReviewResult:
        """
        Review post for originality against source.
        
        Args:
            post: Generated blog post
            source: Original source material
        
        Returns:
            Review decision with justification
        
        Raises:
            ReviewError: If review fails
        """
        try:
            if self.embedding_model is None:
                await self.initialize()
            
            logger.info(
                f"Reviewing blog post: {post.title}",
                extra={"agent": "ReviewerAgent"}
            )
            
            # Calculate embedding-based similarity
            embedding_similarity = await self._calculate_embedding_similarity(post, source)
            
            # Calculate n-gram overlap
            ngram_overlap = self._calculate_ngram_overlap(post, source)
            
            # Check for direct sentence copying
            copied_sentences = await self._check_direct_copying(post, source)
            
            # Make decision based on all metrics
            decision, justification, issues = self._make_decision(
                embedding_similarity,
                ngram_overlap,
                copied_sentences
            )
            
            result = ReviewResult(
                decision=decision,
                similarity_score=embedding_similarity,
                justification=justification,
                issues=issues
            )
            
            logger.info(
                f"Review complete: {decision.value} (similarity: {embedding_similarity:.3f})",
                extra={"agent": "ReviewerAgent", "decision": decision.value}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Review failed: {e}", extra={"agent": "ReviewerAgent"})
            raise ReviewError(f"Failed to review content: {e}") from e

    async def _calculate_embedding_similarity(self, post: BlogPost, source: ContentItem) -> float:
        """
        Calculate similarity using sentence embeddings.
        
        Args:
            post: Blog post
            source: Source content
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Encode both texts
            post_embedding = list(self.embedding_model.embed([post.content]))[0]
            source_embedding = list(self.embedding_model.embed([source.text_content]))[0]
            
            # Normalize
            post_embedding = post_embedding / np.linalg.norm(post_embedding)
            source_embedding = source_embedding / np.linalg.norm(source_embedding)
            
            # Calculate cosine similarity
            similarity = float(np.dot(post_embedding, source_embedding))
            
            # Clamp to [0, 1] range
            similarity = max(0.0, min(1.0, similarity))
            
            return similarity
            
        except Exception as e:
            logger.warning(f"Failed to calculate embedding similarity: {e}")
            return 0.0

    def _calculate_ngram_overlap(self, post: BlogPost, source: ContentItem) -> float:
        """
        Calculate n-gram overlap between post and source.
        
        Args:
            post: Blog post
            source: Source content
        
        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        try:
            # Tokenize
            post_tokens = self._tokenize(post.content)
            source_tokens = self._tokenize(source.text_content)
            
            if not post_tokens or not source_tokens:
                return 0.0
            
            # Generate 4-grams
            post_ngrams = self._extract_ngrams(post_tokens, n=4)
            source_ngrams = self._extract_ngrams(source_tokens, n=4)
            
            if not source_ngrams:
                return 0.0
            
            # Calculate overlap
            overlap = len(post_ngrams & source_ngrams)
            overlap_ratio = overlap / len(source_ngrams)
            
            return min(1.0, overlap_ratio)
            
        except Exception as e:
            logger.warning(f"Failed to calculate n-gram overlap: {e}")
            return 0.0

    async def _check_direct_copying(self, post: BlogPost, source: ContentItem) -> list[str]:
        """
        Check for directly copied sentences.
        
        Args:
            post: Blog post
            source: Source content
        
        Returns:
            List of copied sentences
        """
        copied = []
        
        try:
            # Split into sentences
            post_sentences = self._split_sentences(post.content)
            source_sentences = self._split_sentences(source.text_content)
            
            # Normalize for comparison
            source_normalized = [s.lower().strip() for s in source_sentences]
            
            # Check for exact matches
            for sentence in post_sentences:
                sentence_normalized = sentence.lower().strip()
                if sentence_normalized in source_normalized and len(sentence_normalized) > 50:
                    copied.append(sentence)
            
        except Exception as e:
            logger.warning(f"Failed to check for direct copying: {e}")
        
        return copied

    def _make_decision(
        self,
        embedding_similarity: float,
        ngram_overlap: float,
        copied_sentences: list[str]
    ) -> tuple[ReviewDecision, str, list[str]]:
        """
        Make review decision based on all metrics.
        
        Args:
            embedding_similarity: Embedding-based similarity score
            ngram_overlap: N-gram overlap ratio
            copied_sentences: List of directly copied sentences
        
        Returns:
            Tuple of (decision, justification, issues)
        """
        issues = []
        rejection_reasons = []
        
        # Check embedding similarity
        if embedding_similarity > self.similarity_threshold:
            rejection_reasons.append(
                f"Embedding similarity ({embedding_similarity:.3f}) exceeds threshold ({self.similarity_threshold})"
            )
            issues.append(f"High semantic similarity to source: {embedding_similarity:.3f}")
        
        # Check n-gram overlap
        if ngram_overlap > 0.3:  # 30% n-gram overlap is significant
            rejection_reasons.append(
                f"N-gram overlap ({ngram_overlap:.3f}) indicates substantial content reuse"
            )
            issues.append(f"High n-gram overlap: {ngram_overlap:.3f}")
        
        # Check for direct copying
        if copied_sentences:
            rejection_reasons.append(
                f"Found {len(copied_sentences)} directly copied sentence(s)"
            )
            issues.append(f"Direct copying detected: {len(copied_sentences)} sentence(s)")
        
        # Make decision
        if rejection_reasons:
            decision = ReviewDecision.REJECTED
            justification = f"Content rejected: {'; '.join(rejection_reasons)}"
        else:
            decision = ReviewDecision.APPROVED
            justification = (
                f"Content approved. Similarity score: {embedding_similarity:.3f}, "
                f"N-gram overlap: {ngram_overlap:.3f}. "
                f"Content is sufficiently original."
            )
        
        return decision, justification, issues

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Text to tokenize
        
        Returns:
            List of tokens
        """
        # Simple tokenization - lowercase and split
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def _extract_ngrams(self, tokens: list[str], n: int = 4) -> set[tuple[str, ...]]:
        """
        Extract n-grams from tokens.
        
        Args:
            tokens: List of tokens
            n: N-gram size
        
        Returns:
            Set of n-grams
        """
        if len(tokens) < n:
            return set()
        
        ngrams = set()
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i+n])
            ngrams.add(ngram)
        
        return ngrams

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
        
        Returns:
            List of sentences
        """
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        # Filter empty and strip
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
