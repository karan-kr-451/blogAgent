"""Property-based tests for the Reviewer Agent.

This module contains property tests that validate the correctness of
the Reviewer Agent for content originality validation.
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime

from src.agents.reviewer import ReviewerAgent, ReviewError
from src.models.data_models import ContentItem, BlogPost, ReviewResult, ReviewDecision


# Custom strategies
@st.composite
def similar_content_strategy(draw):
    """Generate blog post and source with high similarity."""
    # Generate base text
    base_text = draw(st.text(min_size=100, max_size=500))
    
    # Create source with this text
    source = ContentItem(
        title="Source Article",
        author="Author",
        publication_date=datetime.utcnow(),
        url="https://example.com/source",
        text_content=base_text,
        code_blocks=[],
        images=[],
        metadata={}
    )
    
    # Create post with very similar content (high similarity)
    post = BlogPost(
        title="Derived Post",
        content=base_text,  # Exact same content - should be rejected
        tags=["test"],
        word_count=len(base_text.split()),
        source_url="https://example.com/source",
        generated_at=datetime.utcnow()
    )
    
    return post, source


@st.composite
def original_content_strategy(draw):
    """Generate blog post and source with low similarity."""
    source_text = draw(st.text(min_size=100, max_value=500))
    post_text = draw(st.text(min_size=100, max_size=500))
    
    # Ensure they're different
    assume(source_text.lower() != post_text.lower())
    
    source = ContentItem(
        title="Source Article",
        author="Author",
        publication_date=datetime.utcnow(),
        url="https://example.com/source",
        text_content=source_text,
        code_blocks=[],
        images=[],
        metadata={}
    )
    
    post = BlogPost(
        title="Original Post",
        content=post_text,
        tags=["test"],
        word_count=len(post_text.split()),
        source_url="https://example.com/source",
        generated_at=datetime.utcnow()
    )
    
    return post, source


class TestReviewThresholdDecision:
    """Property-based tests for review threshold decision.
    
    Property 12: Review Threshold Decision
    Validates: Requirements 6.3
    
    For any BlogPost with similarity score above 0.70 to the source 
    ContentItem, the Reviewer SHALL reject the post with decision = REJECTED.
    """

    @pytest.mark.asyncio
    @given(similar_content_strategy())
    @settings(max_examples=5)
    async def test_high_similarity_rejected(self, content_pair):
        """
        Property: Posts with high similarity are rejected.
        
        For any post with similarity > 0.70 to source, decision should be REJECTED.
        """
        post, source = content_pair
        
        reviewer = ReviewerAgent()
        await reviewer.initialize()
        
        result = await reviewer.review(post, source)
        
        # Exact same content should be rejected
        assert result.decision == ReviewDecision.REJECTED
        assert result.similarity_score > 0.70 or len(result.issues) > 0

    @pytest.mark.asyncio
    @given(original_content_strategy())
    @settings(max_examples=5)
    async def test_low_similarity_approved(self, content_pair):
        """
        Property: Posts with low similarity are approved.
        
        For any post with similarity < 0.70 to source, decision should be APPROVED.
        """
        post, source = content_pair
        
        reviewer = ReviewerAgent()
        await reviewer.initialize()
        
        result = await reviewer.review(post, source)
        
        # Different content should likely be approved
        # (Note: embedding similarity might vary, so we check the logic)
        if result.similarity_score < 0.70:
            assert result.decision == ReviewDecision.APPROVED


class TestNgramOverlapDetection:
    """Property-based tests for n-gram overlap detection.
    
    Property 13: N-gram Overlap Detection
    Validates: Requirements 6.4
    
    For any text pair with identical sentences or paragraphs (n-gram overlap 
    above threshold), the plagiarism detection SHALL identify and report 
    the copied segments.
    """

    def test_ngram_overlap_with_identical_text(self):
        """
        Property: Identical text produces high n-gram overlap.
        """
        reviewer = ReviewerAgent()
        
        text1 = "This is a test sentence with some words"
        text2 = "This is a test sentence with some words"
        
        tokens1 = reviewer._tokenize(text1)
        tokens2 = reviewer._tokenize(text2)
        
        ngrams1 = reviewer._extract_ngrams(tokens1, n=4)
        ngrams2 = reviewer._extract_ngrams(tokens2, n=4)
        
        # Should have complete overlap
        overlap = len(ngrams1 & ngrams2)
        assert overlap == len(ngrams1)
        assert overlap > 0

    def test_ngram_overlap_with_different_text(self):
        """
        Property: Different text produces low n-gram overlap.
        """
        reviewer = ReviewerAgent()
        
        text1 = "Python programming language is great"
        text2 = "Java development framework is popular"
        
        tokens1 = reviewer._tokenize(text1)
        tokens2 = reviewer._tokenize(text2)
        
        ngrams1 = reviewer._extract_ngrams(tokens1, n=4)
        ngrams2 = reviewer._extract_ngrams(tokens2, n=4)
        
        overlap = len(ngrams1 & ngrams2)
        # Should have little to no overlap
        assert overlap < min(len(ngrams1), len(ngrams2))


class TestReviewJustificationPresence:
    """Property-based tests for review justification presence.
    
    Property 14: Review Justification Presence
    Validates: Requirements 6.6
    
    For any ReviewResult, the justification field SHALL be non-empty 
    and provide reasoning for the approval or rejection decision.
    """

    @pytest.mark.asyncio
    @given(similar_content_strategy())
    @settings(max_examples=5)
    async def test_rejected_post_has_justification(self, content_pair):
        """
        Property: Rejected posts have detailed justification.
        """
        post, source = content_pair
        
        reviewer = ReviewerAgent()
        await reviewer.initialize()
        
        result = await reviewer.review(post, source)
        
        if result.decision == ReviewDecision.REJECTED:
            assert isinstance(result.justification, str)
            assert len(result.justification) > 0
            assert len(result.justification) > 20  # Should be meaningful
            # Should mention why it was rejected
            assert any(keyword in result.justification.lower() 
                      for keyword in ['similarity', 'overlap', 'copied', 'reject'])

    @pytest.mark.asyncio
    @given(original_content_strategy())
    @settings(max_examples=5)
    async def test_approved_post_has_justification(self, content_pair):
        """
        Property: Approved posts have justification.
        """
        post, source = content_pair
        
        reviewer = ReviewerAgent()
        await reviewer.initialize()
        
        result = await reviewer.review(post, source)
        
        if result.decision == ReviewDecision.APPROVED:
            assert isinstance(result.justification, str)
            assert len(result.justification) > 0
            assert len(result.justification) > 20  # Should be meaningful


class TestReviewerAgentUnit:
    """Unit tests for Reviewer Agent."""

    def test_tokenization(self):
        """Test text tokenization."""
        reviewer = ReviewerAgent()
        
        text = "Hello, World! This is a test."
        tokens = reviewer._tokenize(text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(token, str) for token in tokens)
        # Should not include punctuation
        assert "," not in tokens
        assert "!" not in tokens

    def test_ngram_extraction(self):
        """Test n-gram extraction."""
        reviewer = ReviewerAgent()
        
        tokens = ["the", "quick", "brown", "fox", "jumps"]
        ngrams = reviewer._extract_ngrams(tokens, n=3)
        
        assert isinstance(ngrams, set)
        assert len(ngrams) > 0
        # Should have 3 3-grams from 5 tokens
        assert len(ngrams) == 3
        # Check one n-gram
        assert ("the", "quick", "brown") in ngrams

    def test_sentence_splitting(self):
        """Test sentence splitting."""
        reviewer = ReviewerAgent()
        
        text = "First sentence. Second sentence! Third sentence?"
        sentences = reviewer._split_sentences(text)
        
        assert isinstance(sentences, list)
        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]

    def test_direct_copying_detection(self):
        """Test detection of directly copied sentences."""
        reviewer = ReviewerAgent()
        
        post = BlogPost(
            title="Post",
            content="This is a unique sentence. This is copied exactly. Another unique one.",
            tags=["test"],
            word_count=10,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        source = ContentItem(
            title="Source",
            author=None,
            publication_date=None,
            url="https://example.com/source",
            text_content="Source text. This is copied exactly. Different ending.",
            code_blocks=[],
            images=[],
            metadata={}
        )
        
        copied = reviewer._check_direct_copying(post, source)
        
        assert isinstance(copied, list)
        # Should detect the copied sentence
        assert any("copied" in sentence.lower() for sentence in copied)

    @pytest.mark.asyncio
    async def test_reviewer_initialization(self):
        """Test Reviewer Agent initialization."""
        reviewer = ReviewerAgent()
        
        await reviewer.initialize()
        
        assert reviewer.embedding_model is not None
        assert reviewer.similarity_threshold > 0

    @pytest.mark.asyncio
    async def test_review_result_structure(self):
        """Test that review result has all required fields."""
        reviewer = ReviewerAgent()
        await reviewer.initialize()
        
        post = BlogPost(
            title="Test Post",
            content="Unique content that is different from source",
            tags=["test"],
            word_count=7,
            source_url="https://example.com",
            generated_at=datetime.utcnow()
        )
        
        source = ContentItem(
            title="Source",
            author=None,
            publication_date=None,
            url="https://example.com/source",
            text_content="Source material with different content",
            code_blocks=[],
            images=[],
            metadata={}
        )
        
        result = await reviewer.review(post, source)
        
        assert isinstance(result, ReviewResult)
        assert hasattr(result, 'decision')
        assert hasattr(result, 'similarity_score')
        assert hasattr(result, 'justification')
        assert hasattr(result, 'issues')
        
        assert isinstance(result.decision, ReviewDecision)
        assert isinstance(result.similarity_score, float)
        assert isinstance(result.justification, str)
        assert isinstance(result.issues, list)
