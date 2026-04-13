# .kiro Configuration for BlogAgent

This directory contains all Qwen Code (formerly Kiro) configuration for the **BlogAgent - Autonomous Blog Content Agent** project.

## Overview

The `.kiro` directory is organized into several components that configure Qwen Code agents, hooks, skills, MCP servers, and project specifications for every session.

```
.kiro/
├── agents/           # Agent configurations (17 specialized agents)
├── hooks/            # Automated hooks for code quality and review
├── settings/         # MCP server configurations
├── skills/           # Specialized skill configurations
├── specs/            # Project specifications and documentation
├── steering/         # Steering configurations (if any)
└── README.md         # This file
```

## 📋 Directory Structure

### 1. `agents/` - Agent Configurations

Contains 17 specialized agent configurations. Key agents updated for BlogAgent:

| Agent | Purpose | BlogAgent Customization |
|-------|---------|------------------------|
| **architect.md** | System architecture and design | Multi-agent systems, FastAPI, LangGraph, FAISS patterns |
| **planner.md** | Implementation planning | BlogAgent-specific planning with 20 correctness properties |
| **python-reviewer.md** | Python code review | BlogAgent security, async/await, agent interfaces, data models |
| **tdd-guide.md** | Test-driven development | 20 correctness properties, pytest, Hypothesis, 80%+ coverage |
| **code-reviewer.md** | General code review | Plan alignment, quality assessment |
| **build-error-resolver.md** | Build error resolution | Python build errors, dependency issues |
| **database-reviewer.md** | Database optimization | FAISS vector storage, metadata management |
| **dependency-resolver.md** | Dependency conflicts | Python package management, version conflicts |
| **doc-updater.md** | Documentation updates | Project docs, architecture maps, README updates |
| **e2e-runner.md** | End-to-end testing | Full pipeline testing, Playwright integration |
| **security-reviewer.md** | Security vulnerabilities | API key protection, input validation, robots.txt |
| **refactor-cleaner.md** | Dead code cleanup | Remove unused agents, utilities, duplicates |

**Key Files**:
- See `agents/architect.md` for architecture decisions
- See `agents/planner.md` for implementation planning
- See `agents/python-reviewer.md` for code review standards
- See `agents/tdd-guide.md` for testing requirements

### 2. `hooks/` - Automated Hooks

Hooks trigger automated actions based on file changes or manual triggers.

| Hook | Trigger | Action |
|------|---------|--------|
| **quality-gate.kiro.hook** | Manual trigger | Runs ruff, mypy, black, pytest with coverage |
| **code-review-on-write.kiro.hook** | After write/edit | Quick code review for security, async, errors |
| **run-tests-on-change.kiro.hook** | After Python file changes | Runs relevant tests automatically |

**Enabled Hooks**:
- ✅ `quality-gate.kiro.hook` - Full quality check
- ✅ `code-review-on-write.kiro.hook` - Post-write review
- ✅ `run-tests-on-change.kiro.hook` - Auto-test on changes

### 3. `settings/` - MCP Server Configurations

Configures Model Context Protocol (MCP) servers for extended capabilities.

| MCP Server | Status | Purpose |
|------------|--------|---------|
| **context7** | ✅ Enabled | Library documentation (FastAPI, LangGraph, etc.) |
| **sequential-thinking** | ✅ Enabled | Structured reasoning for complex problems |
| **playwright** | ✅ Enabled | Browser automation for crawler testing |
| **memory** | ✅ Enabled | Persistent knowledge graph across sessions |
| **filesystem** | ✅ Enabled | File access to `e:\blogAgent` directory |
| **duckduckgo** | ✅ Enabled | Web search for research and docs |
| **fetch** | ✅ Enabled | URL to markdown conversion |
| **github** | ❌ Disabled | Requires PAT token |
| **docker** | ❌ Disabled | Enable for containerization |
| **postgres** | ❌ Disabled | Enable for pgvector alternative |
| **sqlite** | ❌ Disabled | Enable for metadata storage |

**Configuration File**: `settings/mcp.json`

### 4. `skills/` - Specialized Skills

Skills provide for domain-specific expertise.

| Skill | Purpose |
|-------|---------|
| **dependency-management/** | Python package management, version resolution, conflict resolution |

**Key Files**:
- See `skills/dependency-management/SKILL.md` for Python dependency management

### 5. `specs/` - Project Specifications

Contains all project documentation and specifications.

| File/Directory | Purpose |
|----------------|---------|
| **project-info.md** | Complete project information, architecture, workflow |
| **autonomous-blog-agent/** | Original specification documents |
| └─ `.config.kiro` | Spec configuration |
| └─ `requirements.md` | Detailed requirements (13 main requirements) |
| └─ `design.md` | System design document (1294 lines) |
| └─ `tasks.md` | Implementation plan (21 tasks) |

**Key Files**:
- 📖 **Start here**: `specs/project-info.md` - Complete project overview
- 📋 Requirements: `specs/autonomous-blog-agent/requirements.md`
- 🏗️ Design: `specs/autonomous-blog-agent/design.md`
- 📝 Tasks: `specs/autonomous-blog-agent/tasks.md`

### 6. `session-config.md` - Session Configuration

**Location**: `.kiro/session-config.md` (at root of .kiro)

This file contains session setup information that should be loaded at the start of every session:
- Project context and constraints
- Technology stack
- Development workflow
- Key data models
- Environment variables
- Code review checklist

## 🚀 Quick Start

### For New Sessions

1. **Load Project Context**:
   - Read `.kiro/specs/project-info.md`
   - Review `.kiro/session-config.md`
   - Check `.kiro/specs/autonomous-blog-agent/tasks.md` for current progress

2. **Verify Environment**:
   ```bash
   # Check Python version
   python --version  # Should be 3.11+
   
   # Check dependencies
   pip check
   
   # Run tests
   pytest
   ```

3. **Start Development**:
   - Follow TDD methodology (see `agents/tdd-guide.md`)
   - Use agents as needed (architect for design, planner for implementation)
   - Hooks will automatically run quality checks

### Common Workflows

#### Adding a New Feature
1. Use `architect` agent for design (if complex)
2. Use `planner` agent for implementation plan
3. Follow `tdd-guide` agent for test-first development
4. `python-reviewer` agent will review code automatically
5. Run quality gate hook manually

#### Fixing a Bug
1. Use `sequential-thinking` MCP for root cause analysis
2. Follow `tdd-guide` agent to write failing test first
3. Implement fix (minimal code to pass test)
4. Verify all 20 correctness properties still pass

#### Code Review
1. `code-review-on-write` hook triggers automatically
2. Use `python-reviewer` agent for detailed review
3. Use `security-reviewer` agent for security-focused review
4. Address all CRITICAL and HIGH issues before merging

## 📊 Project Constraints

### Must-Have Requirements
- ✅ 6 agents: Crawler, Extractor, Writer, Editor, Reviewer, Publisher
- ✅ 20 correctness properties (property-based testing)
- ✅ 80%+ test coverage
- ✅ Async/await for all I/O
- ✅ API keys in environment variables only
- ✅ Retry logic with exponential backoff
- ✅ Draft-only publishing

### Technology Stack
- **Backend**: FastAPI + LangGraph
- **LLM**: Gemma via Ollama
- **Browser**: Playwright
- **Vector DB**: FAISS (384 dimensions)
- **Testing**: pytest + Hypothesis
- **Quality**: ruff, mypy, black, bandit

## 🔧 Configuration Files

### Key Configuration Files

| File | Purpose |
|------|---------|
| `.kiro/settings/mcp.json` | MCP server configurations |
| `.kiro/session-config.md` | Session setup information |
| `.kiro/specs/project-info.md` | Complete project information |
| `.kiro/agents/*.md` | Agent configurations |
| `.kiro/hooks/*.kiro.hook` | Hook configurations |
| `.kiro/skills/*/SKILL.md` | Skill configurations |

### Environment Variables

Required environment variables (set in `.env` file):
```bash
MEDIUM_API_TOKEN=your_medium_api_token
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=gemma
```

## 📚 Documentation

### Primary Documentation
1. **Project Info**: `specs/project-info.md` - Start here for overview
2. **Requirements**: `specs/autonomous-blog-agent/requirements.md` - What to build
3. **Design**: `specs/autonomous-blog-agent/design.md` - How it's designed
4. **Tasks**: `specs/autonomous-blog-agent/tasks.md` - Implementation plan

### Agent Documentation
- **Architect**: `agents/architect.md` - Architecture patterns and decisions
- **Planner**: `agents/planner.md` - Implementation planning
- **Python Reviewer**: `agents/python-reviewer.md` - Code review standards
- **TDD Guide**: `agents/tdd-guide.md` - Testing methodology

## 🎯 Best Practices

### Development Workflow
1. **Test-First**: Always write tests before implementation (TDD)
2. **Use Agents**: Leverage specialized agents for design, planning, review
3. **Follow Patterns**: Use established patterns (Protocol interfaces, dataclasses, async/await)
4. **Maintain Coverage**: Keep test coverage at 80%+
5. **Property Tests**: Ensure all 20 correctness properties pass
6. **Security First**: Never hardcode or log API keys

### When to Use Agents

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

### Quality Gates

Run quality gate before commits:
```bash
ruff check src/
mypy src/
black --check src/
pytest --cov=src --cov-report=term-missing
bandit -r src/
```

Or use the `quality-gate` hook (manual trigger).

## 🔍 Troubleshooting

### Common Issues

**Issue**: Tests failing after changes
- **Fix**: Run `pytest tests/test_properties/` to check 20 correctness properties

**Issue**: Import errors
- **Fix**: Check `pip check` for dependency conflicts

**Issue**: Async/await errors
- **Fix**: Ensure all I/O operations use async/await, no blocking calls

**Issue**: FAISS index corruption
- **Fix**: Delete `memory/vectors.index` and rebuild from metadata.json

## 📝 Contributing

When contributing to this project:

1. Read `.kiro/specs/project-info.md` for project context
2. Follow TDD methodology from `agents/tdd-guide.md`
3. Use agents for design and review
4. Ensure all 20 correctness properties pass
5. Maintain 80%+ test coverage
6. Update this README if adding new configurations

## 📞 Support

- **Project Specs**: See `specs/` directory
- **Agent Configs**: See `agents/` directory
- **MCP Settings**: See `settings/mcp.json`
- **Session Setup**: See `session-config.md`

---

**Last Updated**: 2026-04-10  
**Project**: BlogAgent - Autonomous Blog Content Agent  
**Configuration Version**: 1.0.0
