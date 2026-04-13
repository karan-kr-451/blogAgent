---
name: dependency-management
description: >
  Use when adding, upgrading, or troubleshooting any package dependency for BlogAgent.
  Ensures you always install the latest compatible version and never get
  version conflicts or peer dependency errors. Triggers before any install command.
  Primary focus: Python packages (FastAPI, LangGraph, Playwright, FAISS, etc.)
---

# Dependency Management for BlogAgent

Always verify before you install. Never guess versions.

## BlogAgent Core Dependencies

The project uses these key Python packages:
- **FastAPI**: Async web framework
- **LangGraph/LangChain**: Agent orchestration and workflow
- **Playwright**: Browser automation
- **FAISS**: Vector similarity search (facebook-research/faiss)
- **sentence-transformers**: Text embeddings
- **httpx**: Async HTTP client
- **Pydantic**: Data validation and settings
- **pytest + Hypothesis**: Testing framework
- **ruff, mypy, black**: Code quality tools
- **bandit**: Security scanning

## When to Use

- Before installing any new Python package
- When seeing dependency conflicts or version errors
- When upgrading packages
- When build/tests fail due to incompatible versions

## The Golden Rule

Use context7 MCP to look up the current version and compatibility info for any package before installing it.

Steps:
1. Call resolve-library-id with the package name
2. Call get-library-docs with the resolved ID to get version info and peer requirements
3. Cross-check against current BlogAgent stack
4. Install the verified version

## Pre-Install Checklist (Python)

Before running any install command:
- What is the latest stable version? (check via `pip index versions <package>` or context7)
- What are the Python version requirements?
- Does it conflict with anything already installed?
- Is the package actively maintained? (last publish date, download count)
- Are there known security advisories? (check `pip-audit`)

## Conflict Resolution Decision Tree

Conflict detected
  Is there a version that satisfies all constraints?
    YES: Install that version, document why not latest
    NO: Can you upgrade the conflicting package?
      YES: Upgrade it first, then install
      NO: Is there a maintained alternative?
        YES: Use the alternative
        NO: Use pip --no-deps and manually manage (last resort, document why)

## Python Package Manager Commands

### Check before installing
```bash
pip index versions <package>
pip show <package>
pip check
pip-audit
```

### Install with confidence
```bash
# Using pip
pip install <package>==<verified-version>

# Using uv (faster, recommended)
uv add <package>
uv pip install <package>

# Using poetry
poetry add <package>@<verified-version>
```

### Verify after installing
```bash
pip check  # Check for dependency conflicts
pip list --outdated  # See what's outdated
pip-audit  # Check for security vulnerabilities
```

### Update existing dependencies
```bash
# Check outdated
pip list --outdated

# Update one package at a time (never bulk update)
pip install --upgrade <package>

# Run tests after each update
pytest

# Update requirements.txt or pyproject.toml
pip freeze > requirements.txt
```

## BlogAgent requirements.txt Template

```txt
# Core Framework
fastapi>=0.109.0,<1.0.0
uvicorn>=0.27.0,<1.0.0
pydantic>=2.6.0,<3.0.0
pydantic-settings>=2.1.0,<3.0.0

# Agent Orchestration
langgraph>=0.0.20,<1.0.0
langchain>=0.1.0,<1.0.0

# Browser Automation
playwright>=1.41.0,<2.0.0

# Vector Storage
faiss-cpu>=1.7.4,<2.0.0  # Use faiss-gpu for production with CUDA

# Embeddings
sentence-transformers>=2.3.0,<3.0.0
numpy>=1.26.0,<2.0.0

# HTTP Client
httpx>=0.26.0,<1.0.0

# HTML Parsing
beautifulsoup4>=4.12.0,<5.0.0
trafilatura>=1.8.0,<2.0.0
lxml>=5.1.0,<6.0.0

# Scheduling
schedule>=1.2.0,<2.0.0

# Testing
pytest>=8.0.0,<9.0.0
pytest-asyncio>=0.23.0,<1.0.0
pytest-cov>=4.1.0,<5.0.0
hypothesis>=6.98.0,<7.0.0
pytest-mock>=3.12.0,<4.0.0

# Code Quality
ruff>=0.2.0,<1.0.0
mypy>=1.8.0,<2.0.0
black>=24.1.0,<25.0.0
bandit>=1.7.0,<2.0.0

# Utilities
python-dotenv>=1.0.0,<2.0.0
structlog>=24.1.0,<25.0.0
```

## Common Python Dependency Issues

### FAISS Installation Failure
**Symptom**: `faiss` package not found or build errors
**Fix**: 
```bash
# CPU version (development)
pip install faiss-cpu

# GPU version (production, requires CUDA)
pip install faiss-gpu
```

### Playwright Browser Missing
**Symptom**: Playwright can't find browser binaries
**Fix**:
```bash
playwright install
playwright install-deps  # Linux only
```

### LangGraph Version Mismatch
**Symptom**: Import errors or missing features
**Fix**: Check LangGraph documentation via context7 for latest stable version
```bash
pip install --upgrade langgraph langchain
```

### Pydantic v1 vs v2
**Symptom**: Validation errors after upgrade
**Fix**: BlogAgent uses Pydantic v2. Ensure all code uses v2 syntax:
```python
# Pydantic v2 (correct)
from pydantic import BaseModel, Field

# Pydantic v1 (deprecated)
# from pydantic import BaseModel, Field
```

### Async/Sync Library Conflicts
**Symptom**: Blocking calls in async context
**Fix**: Use async versions of libraries:
```python
# Correct - async HTTP
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# Wrong - blocking HTTP in async
import requests  # Don't use in async context
response = requests.get(url)
```

## Lock Files

- Always commit `requirements.txt` or `uv.lock` or `poetry.lock`
- Never manually edit lock files
- Use `pip install -r requirements.txt` for reproducible installs
- Prefer `uv sync` for faster, deterministic installs

## Security Best Practices

```bash
# Audit dependencies for vulnerabilities
pip-audit

# Check for known issues
safety check

# Review dependency tree
pipdeptree
```

## Adding New Dependencies

1. **Justify**: Why is this package needed?
2. **Research**: Check via context7 for latest version and docs
3. **Verify**: Check for security issues (`pip-audit`)
4. **Install**: Add to `requirements.txt` with version constraint
5. **Test**: Run full test suite to ensure compatibility
6. **Document**: Update project-info.md if it's a core dependency

## Removing Dependencies

1. **Verify**: Is it truly unused? (grep for imports)
2. **Test**: Remove and run tests to confirm nothing breaks
3. **Clean**: Remove from `requirements.txt`
4. **Reinstall**: `pip install -r requirements.txt` to ensure clean state
5. **Document**: Update project-info.md if it was a core dependency
