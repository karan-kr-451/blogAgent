# BlogAgent - Project Context

**Load this file at the start of every session**

## Quick Reference

| Item | Value |
|------|-------|
| **Project Name** | BlogAgent - Autonomous Blog Content Agent |
| **Type** | Multi-agent AI-powered content automation system |
| **Language** | Python 3.11+ |
| **Framework** | FastAPI + LangGraph + Playwright + FAISS + Ollama/Gemma |
| **Test Coverage** | 80%+ required |
| **Correctness Properties** | 20 (must always pass) |

## Session Startup Checklist

At the start of every session, ensure you have:
- [ ] Loaded this PROJECT_CONTEXT.md
- [ ] Reviewed `.qwen/specs/project-info.md` for complete project details
- [ ] Checked `.qwen/specs/autonomous-blog-agent/tasks.md` for current progress
- [ ] Verified environment variables are set (MEDIUM_API_TOKEN, OLLAMA_ENDPOINT)
- [ ] Run `pytest` to confirm tests are passing

## Project Overview

An autonomous multi-agent system that:
1. **Crawls** ByteByteGo content using Playwright with LLM-driven ReAct loops
2. **Extracts** and structures content using BeautifulSoup/trafilatura
3. **Generates** original blog posts via Gemma/Ollama (800-1500 words)
4. **Edits** content for grammar, flow, and formatting
5. **Reviews** for originality (0.70 similarity threshold)
6. **Publishes** to Medium as drafts (1 post per 24 hours max)

## 6 Core Agents

| Agent | Responsibility |
|-------|---------------|
| **Crawler_Agent** | Autonomous web navigation with Playwright + ReAct loop |
| **Extractor_Agent** | HTML cleaning and content structuring |
| **Writer_Agent** | Original blog post generation via Gemma/Ollama |
| **Editor_Agent** | Content quality improvement |
| **Reviewer_Agent** | Originality verification against source |
| **Publisher_Agent** | Medium API integration for draft publishing |

## Technology Stack

### Backend
- **FastAPI**: Async HTTP server
- **LangGraph**: Agent orchestration and workflow
- **Playwright**: Browser automation
- **FAISS**: Vector storage (IndexFlatIP, 384 dimensions)
- **sentence-transformers**: Embeddings (all-MiniLM-L6-v2)
- **Ollama/Gemma**: Local LLM

### Development Tools
- **Testing**: pytest + Hypothesis (property-based)
- **Linting**: ruff, mypy, black
- **Security**: bandit

## Key Constraints (NON-NEGOTIABLE)

### Must Always Maintain
- ✅ **20 correctness properties** - property-based testing must pass
- ✅ **80%+ test coverage** - no exceptions
- ✅ **Async/await** for all I/O operations
- ✅ **API keys in environment variables only** - never hardcoded or logged
- ✅ **Retry logic** with exponential backoff (3 attempts: 1s, 2s, 4s)
- ✅ **Ollama retry** max 5 attempts when unavailable
- ✅ **Regeneration** max 2 attempts per content item
- ✅ **Publication rate** max 1 post per 24 hours
- ✅ **Draft-only publishing** - manual review required
- ✅ **Robots.txt compliance** - ethical crawling

### Retry Configuration
```
Standard services: 3 attempts, exponential backoff (1s, 2s, 4s)
Ollama service: 5 attempts when unavailable
Regeneration: 2 attempts per content item
```

## 20 Correctness Properties

These properties must ALWAYS pass:

1. **Robots.txt Compliance**: Crawler respects directives
2. **HTML Cleaning**: Removes nav/ads, preserves content
3. **ContentItem Structure**: All metadata fields present
4. **Serialization Round-Trip**: JSON serialize/deserialize equivalence
5. **Cosine Similarity**: Symmetry, range [0,1], identity
6. **Duplicate Detection**: 0.85 threshold enforcement
7. **Word Count**: 800-1500 words per blog post
8. **Exponential Backoff**: 2^(N-1) delay pattern
9. **Blog Post Structure**: Title, intro, body, conclusion
10. **Code Block Formatting**: Preserve indentation and syntax highlighting
11. **Change Tracking**: Non-empty edit list
12. **Review Threshold**: 0.70 rejection threshold
13. **N-gram Overlap**: Detect copied sentences/paragraphs
14. **Review Justification**: Non-empty justification required
15. **Tag Generation**: Non-empty relevant tags
16. **Publication Rate Limiting**: Max 1 post per 24 hours
17. **Concurrent Execution Prevention**: Single pipeline run
18. **API Key Leak Prevention**: No keys in logs/responses
19. **Ollama Retry Limit**: Max 5 retries
20. **Regeneration Attempt Limit**: Max 2 regenerations per item

## Key Data Models

### ContentItem
```python
@dataclass
class ContentItem:
    title: str
    author: str | None
    publication_date: datetime | None
    url: str
    text_content: str
    code_blocks: list[str]
    images: list[str]
    metadata: dict
```

### BlogPost
```python
@dataclass
class BlogPost:
    title: str
    content: str  # Markdown format
    tags: list[str]
    word_count: int
    source_url: str
    generated_at: datetime
```

## Pipeline Execution Flow

```
Scheduler → API Server → Crawler → Extractor → Memory (duplicate check)
  → Writer → Editor → Reviewer → (if approved) Publisher → Memory (store)
  → (if rejected) Writer (regenerate, max 2 attempts)
```

## Environment Variables

### Required
```bash
MEDIUM_API_TOKEN=your_medium_api_token
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=gemma
```

### Optional
```bash
SCHEDULE_TIME=09:00
MAX_ARTICLES_PER_RUN=10
LOG_LEVEL=INFO
```

## Development Workflow

### Setup
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run property-based tests (20 correctness properties)
pytest tests/test_properties/

# Run specific test
pytest tests/test_agents/test_extractor.py -v
```

### Linting & Type Checking
```bash
ruff check src/           # Fast linting
mypy src/                 # Type checking
black --check src/        # Format check
bandit -r src/            # Security scan
```

### Running the System
```bash
python -m src.main run-server        # Start API server
python -m src.main run-scheduler     # Start scheduler
python -m src.main trigger-pipeline  # Manual pipeline trigger
```

## Quality Gate

Run before commits:
```bash
ruff check src/ && mypy src/ && black --check src/ && pytest --cov=src --cov-report=term-missing -v
```

Or use the quality-gate hook (manual trigger from Agent Hooks panel).

## Agent Interface Pattern

All agents must follow this pattern:
```python
from typing import Protocol

class AgentProtocol(Protocol):
    async def process(self, input_data: Any) -> Any:
        """Process input and return output."""
        ...
```

## Retry Pattern

All external service calls must use:
```python
async def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

## Code Review Checklist

When reviewing code, verify:
- [ ] No API keys hardcoded or logged
- [ ] Async/await used correctly (no blocking I/O)
- [ ] Retry logic with exponential backoff present
- [ ] Type hints on all public functions
- [ ] Protocol interfaces for agents
- [ ] Data models complete with serialization
- [ ] Error handling with specific exceptions
- [ ] Tests written first (TDD methodology)
- [ ] 20 correctness properties still pass
- [ ] Code coverage maintained at 80%+

## When to Use Specialized Agents

| Scenario | Use Agent |
|----------|-----------|
| Designing new feature | `architect` |
| Planning implementation | `planner` |
| Writing new code | `tdd-guide` |
| Reviewing code | `python-reviewer`, `security-reviewer` |
| Fixing build errors | `build-error-resolver` |
| Resolving dependencies | `dependency-resolver` |
| Database/FAISS issues | `database-reviewer` |
| Updating documentation | `doc-updater` |
| E2E testing | `e2e-runner` |
| Dead code cleanup | `refactor-cleaner` |

## Directory Structure

```
blogAgent/
├── src/
│   ├── agents/           # Agent implementations
│   ├── api/              # FastAPI server and workflow
│   ├── memory/           # FAISS vector storage
│   ├── scheduler/        # Pipeline scheduler
│   ├── models/           # Data models
│   ├── utils/            # Utilities (retry, errors, etc.)
│   ├── config.py         # Configuration
│   └── main.py           # CLI entry point
├── tests/                # Test suite
├── .qwen/                # Project configuration (this directory)
│   ├── agents/           # Agent configurations
│   ├── hooks/            # Hook configurations
│   ├── skills/           # Skill configurations
│   ├── steering/         # Steering configurations
│   └── specs/            # Project specifications and docs
├── .kiro/                # Legacy Kiro configuration (reference)
└── memory/               # FAISS index and metadata
```

## Important Notes

⚠️ **CRITICAL RULES**:
- **NEVER commit API keys** - use `.env` file only
- **ALWAYS write tests first** - TDD methodology required
- **MAINTAIN 20 correctness properties** - non-negotiable
- **USE async/await** - no blocking I/O operations
- **LOG errors with context** - for debugging
- **DRAFT-ONLY publishing** - manual review required
- **RESPECT robots.txt** - ethical crawling mandatory

## Resources

- **Complete Project Info**: `.qwen/specs/project-info.md`
- **Requirements**: `.qwen/specs/autonomous-blog-agent/requirements.md`
- **Design Document**: `.qwen/specs/autonomous-blog-agent/design.md`
- **Implementation Tasks**: `.qwen/specs/autonomous-blog-agent/tasks.md`
- **Agent Configs**: `.qwen/agents/`
- **MCP Settings**: `.qwen/settings.json`

---

**Last Updated**: 2026-04-10
**Project**: BlogAgent - Autonomous Blog Content Agent
**Configuration Version**: 1.0.0
