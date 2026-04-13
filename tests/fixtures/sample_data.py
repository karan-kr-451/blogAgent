"""Test fixtures for the Autonomous Blog Agent."""

import pytest
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Generator

from src.config import Config
from src.models.data_models import ContentItem, BlogPost
from src.memory.memory_system import MemorySystem


@pytest.fixture
def sample_html() -> str:
    """Sample ByteByteGo-like HTML for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Design: Load Balancing</title>
        <meta name="author" content="ByteByteGo">
        <meta property="article:published_time" content="2024-01-15T10:00:00Z">
    </head>
    <body>
        <nav>Navigation Menu</nav>
        <header>ByteByteGo</header>
        
        <article>
            <h1>System Design: Load Balancing</h1>
            <p>Load balancing is a critical component in distributed systems...</p>
            
            <h2>What is Load Balancing?</h2>
            <p>A load balancer distributes incoming network traffic across multiple servers...</p>
            
            <h2>Load Balancing Algorithms</h2>
            <p>There are several algorithms for load balancing:</p>
            <ul>
                <li>Round Robin</li>
                <li>Least Connections</li>
                <li>IP Hash</li>
            </ul>
            
            <pre><code class="language-python">def load_balance(requests, servers):
    for request in requests:
        server = select_server(servers)
        forward(request, server)
</code></pre>
            
            <img src="https://example.com/load-balancer-diagram.png" alt="Load Balancer Diagram">
        </article>
        
        <footer>Copyright 2024</footer>
        <div class="advertisement">Ad content here</div>
    </body>
    </html>
    """


@pytest.fixture
def sample_content_item() -> ContentItem:
    """Sample ContentItem for testing."""
    return ContentItem(
        title="System Design: Load Balancing",
        author="ByteByteGo",
        publication_date=datetime(2024, 1, 15, 10, 0, 0),
        url="https://blog.bytebytego.com/load-balancing",
        text_content="Load balancing is a critical component in distributed systems. A load balancer distributes incoming network traffic across multiple servers. There are several algorithms for load balancing including Round Robin, Least Connections, and IP Hash.",
        code_blocks=[
            "```python\ndef load_balance(requests, servers):\n    for request in requests:\n        server = select_server(servers)\n        forward(request, server)\n```"
        ],
        images=["https://example.com/load-balancer-diagram.png"],
        metadata={
            "extraction_method": "test",
            "topic": "system-design"
        }
    )


@pytest.fixture
def sample_blog_post() -> BlogPost:
    """Sample BlogPost for testing."""
    return BlogPost(
        title="Understanding Load Balancing in Modern Systems",
        content="""# Understanding Load Balancing in Modern Systems

## Introduction

In today's distributed systems architecture, load balancing plays a crucial role...

## How Load Balancers Work

A load balancer acts as a reverse proxy that distributes network traffic...

## Common Algorithms

1. Round Robin - distributes requests in a circular manner
2. Least Connections - sends to server with fewest active connections
3. IP Hash - uses client IP to determine server

## Conclusion

Load balancing is essential for scalability and reliability.
""",
        tags=["system-design", "load-balancing", "distributed-systems", "architecture"],
        word_count=120,
        source_url="https://blog.bytebytego.com/load-balancing",
        generated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_embedding() -> np.ndarray:
    """Sample embedding vector for testing."""
    np.random.seed(42)
    embedding = np.random.randn(384).astype(np.float32)
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


@pytest.fixture
def temp_config(tmp_path) -> Config:
    """Create a temporary configuration for testing."""
    return Config(
        medium_api_token="test-token-for-testing",
        medium_author_id="test-author-id",
        ollama_endpoint="http://localhost:11434",
        ollama_model="gemma:7b",
        memory_index_path=str(tmp_path / "vectors.index"),
        memory_metadata_path=str(tmp_path / "metadata.json"),
        crawler_start_url="https://blog.bytebytego.com",
        api_host="127.0.0.1",
        api_port=8001,
        log_level="DEBUG",
        log_format="text"
    )


@pytest.fixture
async def memory_system(temp_config: Config) -> Generator[MemorySystem, None, None]:
    """Create an initialized MemorySystem for testing."""
    memory = MemorySystem(config=temp_config)
    await memory.initialize()
    
    yield memory
    
    # Cleanup
    try:
        index_path = Path(temp_config.memory_index_path)
        metadata_path = Path(temp_config.memory_metadata_path)
        
        if index_path.exists():
            index_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()
    except Exception:
        pass
