"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Import fixtures
from tests.fixtures.sample_data import (
    sample_html,
    sample_content_item,
    sample_blog_post,
    sample_embedding,
    temp_config,
    memory_system
)

__all__ = [
    "sample_html",
    "sample_content_item",
    "sample_blog_post",
    "sample_embedding",
    "temp_config",
    "memory_system"
]
