# BlogAgent Project Information

## Project Overview

**Project Name**: BlogAgent - Autonomous Blog Content Agent  
**Type**: Multi-agent AI-powered content automation system  
**Primary Language**: Python  
**Architecture**: Multi-agent system with FastAPI backend, LangGraph orchestration, and optional React dashboard  

## Project Purpose

An autonomous multi-agent system that discovers, processes, and publishes original blog content. The system crawls ByteByteGo content, extracts and structures information, generates original blog posts using Gemma via Ollama, improves content quality through editing and review, and publishes to Medium with appropriate safeguards.

## Core Components

### 1. Agents
- **Crawler_Agent**: Autonomous web navigation using Playwright + LLM reasoning (ReAct loop)
- **Extractor_Agent**: HTML cleaning and content structuring
- **Writer_Agent**: Original blog post generation via Gemma/Ollama
- **Editor_Agent**: Content quality improvement (grammar, flow, formatting)
- **Reviewer_Agent**: Originality verification against source material
- **Publisher_Agent**: Medium API integration for draft publishing

### 2. Infrastructure
- **API Server**: FastAPI backend for agent coordination
- **Memory System**: FAISS vector storage for duplicate detection
- **Scheduler**: Daily automated pipeline execution
- **Dashboard** (optional): React monitoring interface

## Technology Stack

### Backend
- **Framework**: FastAPI (async HTTP server)
- **Agent Orchestration**: LangChain/LangGraph
- **LLM**: Gemma via Ollama
- **Browser Automation**: Playwright
- **Vector Storage**: FAISS (IndexFlatIP, 384 dimensions)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Scheduling**: Python `schedule` library or cron
- **HTML Parsing**: BeautifulSoup or trafilatura

### Frontend (Optional)
- **Framework**: React with TypeScript
- **State Management**: TanStack Query
- **Styling**: Tailwind CSS
- **Build Tool**: Vite

### Development Tools
- **Testing**: pytest, Hypothesis (property-based testing)
- **Linting**: ruff, mypy, black
- **Security**: bandit
- **Package Management**: pip, uv, or poetry

## Project Structure

```
blogAgent/
├── src/
│   ├── agents/
│   │   ├── crawler.py          # Crawler_Agent with ReAct loop
│   │   ├── extractor.py        # Extractor_Agent
│   │   ├── writer.py           # Writer_Agent
│   │   ├── editor.py           # Editor_Agent
│   │   ├── reviewer.py         # Reviewer_Agent
│   │   └── publisher.py        # Publisher_Agent
│   ├── api/
│   │   ├── server.py           # FastAPI application
│   │   └── workflow.py         # LangGraph orchestration
│   ├── memory/
│   │   └── memory_system.py    # FAISS vector storage
│   ├── scheduler/
│   │   └── scheduler.py        # Daily pipeline scheduler
│   ├── models/
│   │   └── data_models.py      # Core data structures
│   ├── utils/
│   │   ├── retry.py            # Retry with exponential backoff
│   │   ├── circuit_breaker.py  # Circuit breaker pattern
│   │   └── errors.py           # Custom exceptions
│   ├── config.py               # Configuration management
│   └── main.py                 # CLI entry point
├── tests/
│   ├── fixtures/
│   │   ├── sample_html.py
│   │   ├── sample_content.py
│   │   └── mock_responses.py
│   ├── conftest.py
│   ├── test_agents/
│   ├── test_api/
│   ├── test_memory/
│   └── test_properties/        # 20 correctness properties
├── dashboard/                   # Optional React dashboard
│   ├── src/
│   ├── public/
│   └── package.json
├── memory/                      # FAISS vector storage
│   ├── vectors.index
│   └── metadata.json
├── .kiro/
│   ├── agents/
│   ├── hooks/
│   ├── settings/
│   ├── skills/
│   ├── specs/
│   └── steering/
├── .env.example
├── pyproject.toml / setup.py
├── requirements.txt
└── README.md
```

## Key Requirements

### Functional Requirements
1. **Autonomous Crawling**: Playwright with LLM-driven ReAct loop (no hardcoded selectors)
2. **Content Extraction**: Clean HTML, extract text/code/images with metadata
3. **Memory & Duplicate Prevention**: FAISS vector storage, 0.85 similarity threshold
4. **Blog Post Generation**: Gemma via Ollama, 800-1500 words, original content
5. **Content Quality**: Grammar, flow, and formatting improvements
6. **Originality Verification**: 0.70 similarity threshold, reject if exceeded
7. **Medium Publishing**: Draft posts, API token auth, 1 post/day limit
8. **Automated Scheduling**: Daily execution, skip if already running
9. **API Coordination**: FastAPI + LangGraph workflow orchestration
10. **Monitoring Dashboard**: React UI for status, approval, and manual triggers

### Non-Functional Requirements
- **Security**: API keys in environment variables, never logged or exposed
- **Resilience**: Retry with exponential backoff (3 attempts, 1s base delay)
- **Performance**: Ollama retry limit 5 times, timeout mechanisms
- **Reliability**: Concurrent execution prevention, corruption recovery
- **Maintainability**: 80%+ test coverage, property-based testing (20 properties)

## Configuration Requirements

### Environment Variables
```bash
# Required
MEDIUM_API_TOKEN=your_medium_api_token
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=gemma

# Optional
SCHEDULE_TIME=09:00
MAX_ARTICLES_PER_RUN=10
LOG_LEVEL=INFO
```

### FAISS Memory System
- **Index Type**: IndexFlatIP (inner product for cosine similarity)
- **Dimension**: 384 (all-MiniLM-L6-v2 embeddings)
- **Persistence**: Auto-save after each store operation
- **Recovery**: Rebuild from logs if corrupted

### Retry Configuration
- **Writer Agent**: 3 attempts, exponential backoff (1s, 2s, 4s)
- **Publisher Agent**: 3 attempts, exponential backoff (1s, 2s, 4s)
- **Ollama Service**: 5 attempts when unavailable
- **Network Requests**: 3 attempts with exponential backoff

## Correctness Properties (20 Total)

1. **Robots.txt Compliance**: Crawler respects directives
2. **HTML Cleaning**: Removes nav/ads, preserves content
3. **ContentItem Structure**: All metadata fields present
4. **Serialization Round-Trip**: JSON serialize/deserialize equivalence
5. **Cosine Similarity**: Symmetry, range [0,1], identity
6. **Duplicate Detection**: 0.85 threshold enforcement
7. **Word Count**: 800-1500 words per blog post
8. **Exponential Backoff**: 2^(N-1) delay pattern
9. **Blog Post Structure**: Title, intro, body, conclusion
10. **Code Block Formatting**: Preserve indentation and syntax
11. **Change Tracking**: Non-empty edit list
12. **Review Threshold**: 0.70 rejection threshold
13. **N-gram Overlap**: Detect copied sentences/paragraphs
14. **Review Justification**: Non-empty justification
15. **Tag Generation**: Non-empty relevant tags
16. **Publication Rate Limiting**: Max 1 post per 24 hours
17. **Concurrent Execution Prevention**: Single pipeline run
18. **API Key Leak Prevention**: No keys in logs/responses
19. **Ollama Retry Limit**: Max 5 retries
20. **Regeneration Attempt Limit**: Max 2 regenerations per item

## Development Workflow

### 1. Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run property-based tests
pytest tests/test_properties/

# Run specific test file
pytest tests/test_agents/test_extractor.py
```

### 3. Linting & Type Checking
```bash
# Fast linting
ruff check src/

# Type checking
mypy src/

# Format check
black --check src/

# Security scan
bandit -r src/
```

### 4. Running the System
```bash
# Start API server
python -m src.main run-server

# Start scheduler
python -m src.main run-scheduler

# Manual pipeline trigger
python -m src.main trigger-pipeline
```

## Pipeline Execution Flow

```
Scheduler → API Server → Crawler → Extractor → Memory (duplicate check)
  → Writer → Editor → Reviewer → (if approved) Publisher → Memory (store)
  → (if rejected) Writer (regenerate, max 2 attempts)
```

## Key Design Decisions

1. **ReAct Loop for Crawler**: LLM reasons about page state and decides actions dynamically
2. **No Hardcoded Selectors**: Crawler uses semantic understanding, not brittle CSS selectors
3. **Draft-Only Publishing**: All posts published as drafts for manual review
4. **Vector-Based Deduplication**: FAISS embeddings prevent duplicate content
5. **Multi-Stage Review**: Write → Edit → Review pipeline ensures quality
6. **Async Architecture**: All agents use async/await for non-blocking I/O
7. **Property-Based Testing**: 20 correctness properties validate universal behaviors

## Common Tasks

### Adding a New Agent
1. Create agent class in `src/agents/`
2. Define Protocol interface
3. Implement retry logic
4. Write property tests
5. Add to LangGraph workflow

### Modifying Pipeline Flow
1. Update `src/api/workflow.py` StateGraph
2. Add/modify nodes and edges
3. Update conditional edges
4. Test with integration tests

### Updating Configuration
1. Modify `src/config.py` Pydantic model
2. Update `.env.example`
3. Validate on startup
4. Document changes

## Known Constraints

- **Ollama Dependency**: Requires local Ollama installation with Gemma model
- **Medium API**: Requires valid API token, rate limited to 1 post/day
- **Playwright**: Requires browser installation, headless mode for production
- **FAISS**: CPU-only version for development, GPU version for production scaling
- **Memory Usage**: FAISS index loads into memory, consider disk persistence strategy

## Future Enhancements

- Multi-website crawling (not just ByteByteGo)
- Advanced content scheduling (multiple posts per day)
- A/B testing for blog post titles
- SEO optimization agent
- Social media sharing integration
- Analytics and performance tracking
- Multi-language support
- Advanced plagiarism detection (external APIs)

## Contact & Resources

- **Design Document**: `.kiro/specs/autonomous-blog-agent/design.md`
- **Requirements**: `.kiro/specs/autonomous-blog-agent/requirements.md`
- **Implementation Plan**: `.kiro/specs/autonomous-blog-agent/tasks.md`
- **Architecture**: See design.md for detailed system architecture