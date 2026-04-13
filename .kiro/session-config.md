# Session Configuration for BlogAgent

## Project Information
- **Name**: BlogAgent - Autonomous Blog Content Agent
- **Type**: Multi-agent AI-powered content automation system
- **Primary Language**: Python
- **Framework**: FastAPI + LangGraph + Playwright + FAISS + Ollama/Gemma

## Session Setup

### Load Project Context
At the start of every session, load and reference:
1. `.kiro/specs/project-info.md` - Complete project information
2. `.kiro/specs/autonomous-blog-agent/requirements.md` - Requirements document
3. `.kiro/specs/autonomous-blog-agent/design.md` - Design document
4. `.kiro/specs/autonomous-blog-agent/tasks.md` - Implementation plan

### Key Project Constraints
- **6 Agents**: Crawler, Extractor, Writer, Editor, Reviewer, Publisher
- **20 Correctness Properties**: Must always pass (property-based testing)
- **Test Coverage**: 80%+ required
- **Async/Await**: All I/O operations must be async
- **Security**: API keys in environment variables only, never logged
- **Retry Logic**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **Ollama Retry**: Max 5 attempts when unavailable
- **Regeneration**: Max 2 attempts per content item
- **Publication Rate**: Max 1 post per 24 hours

### Technology Stack
- **Backend**: FastAPI (async HTTP server)
- **Agent Orchestration**: LangChain/LangGraph
- **LLM**: Gemma via Ollama
- **Browser Automation**: Playwright
- **Vector Storage**: FAISS (IndexFlatIP, 384 dimensions)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **HTML Parsing**: BeautifulSoup or trafilatura
- **Testing**: pytest, Hypothesis (property-based testing)
- **Linting**: ruff, mypy, black
- **Security**: bandit

### Directory Structure
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
├── .kiro/                # Project configuration
│   ├── specs/            # Project specs and docs
│   ├── agents/           # Agent configurations
│   ├── hooks/            # Hook configurations
│   ├── skills/           # Skill configurations
│   └── settings/         # MCP and other settings
└── memory/               # FAISS index and metadata
```

### Development Workflow

#### 1. Setup
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install
```

#### 2. Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run property-based tests
pytest tests/test_properties/

# Run specific test file
pytest tests/test_agents/test_extractor.py -v
```

#### 3. Linting & Type Checking
```bash
ruff check src/           # Fast linting
mypy src/                 # Type checking
black --check src/        # Format check
bandit -r src/            # Security scan
```

#### 4. Running the System
```bash
python -m src.main run-server        # Start API server
python -m src.main run-scheduler     # Start scheduler
python -m src.main trigger-pipeline  # Manual pipeline trigger
```

### Pipeline Execution Flow
```
Scheduler → API Server → Crawler → Extractor → Memory (duplicate check)
  → Writer → Editor → Reviewer → (if approved) Publisher → Memory (store)
  → (if rejected) Writer (regenerate, max 2 attempts)
```

### Key Data Models

#### ContentItem
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

#### BlogPost
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

### Agent Interface Pattern
All agents must follow this pattern:
```python
from typing import Protocol

class AgentProtocol(Protocol):
    async def process(self, input_data: Any) -> Any:
        """Process input and return output."""
        ...
```

### Retry Pattern
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

### Code Review Checklist
When reviewing code, check:
- [ ] No API keys hardcoded or logged
- [ ] Async/await used correctly
- [ ] Retry logic with exponential backoff present
- [ ] Type hints on all public functions
- [ ] Protocol interfaces for agents
- [ ] Data models complete with serialization
- [ ] Error handling with specific exceptions
- [ ] Tests written first (TDD)
- [ ] 20 correctness properties still pass
- [ ] Code coverage maintained at 80%+

### Common Tasks

#### Adding a New Agent
1. Create agent class in `src/agents/`
2. Define Protocol interface
3. Implement retry logic
4. Write property tests
5. Add to LangGraph workflow
6. Update project-info.md

#### Modifying Pipeline Flow
1. Update `src/api/workflow.py` StateGraph
2. Add/modify nodes and edges
3. Update conditional edges
4. Test with integration tests
5. Verify all 20 properties still pass

#### Updating Configuration
1. Modify `src/config.py` Pydantic model
2. Update `.env.example`
3. Validate on startup
4. Document changes

### Important Notes
- **Never commit API keys** - use `.env` file
- **Always write tests first** - TDD methodology
- **Maintain 20 correctness properties** - non-negotiable
- **Use async/await** - no blocking I/O
- **Log errors with context** - for debugging
- **Draft-only publishing** - manual review required
- **Respect robots.txt** - ethical crawling

### Resources
- **Project Info**: `.kiro/specs/project-info.md`
- **Requirements**: `.kiro/specs/autonomous-blog-agent/requirements.md`
- **Design**: `.kiro/specs/autonomous-blog-agent/design.md`
- **Tasks**: `.kiro/specs/autonomous-blog-agent/tasks.md`
- **Agents**: `.kiro/agents/` (all agent configurations)
