# Implementation Plan: Autonomous Blog Agent

## Overview

This implementation plan breaks down the Autonomous Blog Agent into discrete, implementable tasks. The system is a multi-agent content automation pipeline that crawls ByteByteGo, generates original blog posts using Gemma via Ollama, and publishes to Medium with quality assurance.

**Implementation Language**: Python

The implementation follows this sequence:
1. Project structure and core data models (Python dataclasses)
2. Memory system with FAISS
3. Individual agents (Crawler, Extractor, Writer, Editor, Reviewer, Publisher)
4. FastAPI server with LangGraph orchestration
5. Scheduler
6. Optional React dashboard
7. Property-based tests for all 20 correctness properties using Hypothesis

## Tasks

- [x] 1. Set up project structure and core data models
  - Create directory structure: `src/agents/`, `src/models/`, `src/api/`, `src/memory/`, `src/scheduler/`, `tests/`
  - Create `pyproject.toml` or `setup.py` with dependencies: FastAPI, Playwright, LangChain/LangGraph, FAISS, Hypothesis, pytest, sentence-transformers, httpx
  - Define core data models in `src/models/data_models.py`: `ContentItem`, `BlogPost`, `ReviewResult`, `PublicationResult`, `CrawlerAction`, `PageState`
  - Implement serialization methods (`to_json`, `from_json`) for `ContentItem` and `BlogPost`
  - Create configuration model in `src/config.py` with Pydantic validation for Medium API token, Ollama endpoint
  - Set up logging configuration with structured JSON format
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 1.1 Write property test for ContentItem serialization
  - **Property 4: ContentItem Serialization Round-Trip**
  - **Validates: Requirements 2.5**

- [ ] 2. Implement Memory System with FAISS
  - [ ] 2.1 Create `MemorySystem` class in `src/memory/memory_system.py`
    - Initialize FAISS IndexFlatIP with dimension 384
    - Implement `store(content, embedding)` method
    - Implement `check_duplicate(embedding, threshold=0.85)` method using cosine similarity
    - Implement `get_history(limit)` method
    - Implement `persist()` and `load()` methods for disk storage
    - Add corruption recovery logic in `load()` method
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 12.6_

  - [ ]* 2.2 Write property test for cosine similarity
    - **Property 5: Cosine Similarity Properties**
    - **Validates: Requirements 3.3, 6.2**

  - [ ]* 2.3 Write property test for duplicate detection threshold
    - **Property 6: Duplicate Detection Threshold**
    - **Validates: Requirements 3.4**

  - [ ]* 2.4 Write unit tests for Memory System
    - Test storage and retrieval operations
    - Test duplicate detection with various similarity scores
    - Test persistence and recovery from corruption
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 3. Implement Extractor Agent
  - [ ] 3.1 Create `ExtractorAgent` class in `src/agents/extractor.py`
    - Implement `extract(raw_html, url)` method using BeautifulSoup or trafilatura
    - Remove navigation, ads, footers using heuristics
    - Extract text content, code blocks (with language detection), and images
    - Extract metadata from meta tags (title, author, publication date)
    - Return structured `ContentItem` with all required fields
    - Raise `ExtractionError` with diagnostics on failure
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 3.2 Write property test for HTML cleaning
    - **Property 2: HTML Cleaning Preserves Content**
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 3.3 Write property test for ContentItem structure completeness
    - **Property 3: ContentItem Structure Completeness**
    - **Validates: Requirements 2.3**

  - [ ]* 3.4 Write unit tests for Extractor Agent
    - Test extraction with malformed HTML
    - Test extraction with empty HTML
    - Test code block detection and language identification
    - Test metadata extraction edge cases
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Writer Agent
  - [ ] 5.1 Create `WriterAgent` class in `src/agents/writer.py`
    - Initialize Ollama client with configurable endpoint and model
    - Implement `generate(content_item)` method
    - Create prompt template: "Inspired by this content, write an original blog post..."
    - Set generation parameters: temperature=0.7, max_tokens=2000
    - Parse LLM response into `BlogPost` structure (title, content, tags)
    - Calculate word count and validate 800-1500 word range
    - Implement retry logic with exponential backoff (3 attempts, 1s base delay)
    - Raise `GenerationError` after exhausting retries
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 5.2 Write property test for blog post word count validation
    - **Property 7: Blog Post Word Count Validation**
    - **Validates: Requirements 4.4**

  - [ ]* 5.3 Write property test for exponential backoff retry logic
    - **Property 8: Exponential Backoff Retry Logic**
    - **Validates: Requirements 4.5, 7.5, 12.2**

  - [ ]* 5.4 Write property test for blog post structure completeness
    - **Property 9: Blog Post Structure Completeness**
    - **Validates: Requirements 4.6**

  - [ ]* 5.5 Write property test for Ollama retry limit
    - **Property 19: Ollama Retry Limit**
    - **Validates: Requirements 12.5**

  - [ ]* 5.6 Write unit tests for Writer Agent
    - Test generation with mock Ollama responses
    - Test retry behavior on timeout
    - Test word count validation
    - Test structured output parsing
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 6. Implement Editor Agent
  - [ ] 6.1 Create `EditorAgent` class in `src/agents/editor.py`
    - Initialize Ollama client for editing operations
    - Implement `edit(blog_post)` method
    - Create editing prompt: "Improve grammar, spelling, punctuation, and flow while maintaining technical accuracy"
    - Parse edited content and track changes
    - Return `EditedPost` with change log
    - Ensure code blocks are properly formatted
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 6.2 Write property test for code block formatting preservation
    - **Property 10: Code Block Formatting Preservation**
    - **Validates: Requirements 5.4**

  - [ ]* 6.3 Write property test for edited post change tracking
    - **Property 11: Edited Post Change Tracking**
    - **Validates: Requirements 5.6**

  - [ ]* 6.4 Write unit tests for Editor Agent
    - Test grammar and spelling improvements
    - Test code block formatting
    - Test change tracking
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 7. Implement Reviewer Agent
  - [ ] 7.1 Create `ReviewerAgent` class in `src/agents/reviewer.py`
    - Initialize sentence-transformers model for embeddings
    - Implement `review(blog_post, source_content)` method
    - Calculate sentence-level similarity using embeddings
    - Implement n-gram overlap detection for direct copying
    - Apply 0.70 similarity threshold (reject if exceeded)
    - Generate detailed justification for decision
    - Return `ReviewResult` with decision, similarity score, justification, and issues
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 7.2 Write property test for review threshold decision
    - **Property 12: Review Threshold Decision**
    - **Validates: Requirements 6.3**

  - [ ]* 7.3 Write property test for n-gram overlap detection
    - **Property 13: N-gram Overlap Detection**
    - **Validates: Requirements 6.4**

  - [ ]* 7.4 Write property test for review justification presence
    - **Property 14: Review Justification Presence**
    - **Validates: Requirements 6.6**

  - [ ]* 7.5 Write unit tests for Reviewer Agent
    - Test similarity calculation with various content pairs
    - Test n-gram overlap detection
    - Test threshold enforcement
    - Test justification generation
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement Publisher Agent
  - [ ] 9.1 Create `PublisherAgent` class in `src/agents/publisher.py`
    - Initialize Medium API client with token from environment
    - Implement `publish(blog_post)` method
    - Convert blog post to Medium API format (markdown content, tags)
    - Set publishStatus to "draft"
    - Implement retry logic with exponential backoff (3 attempts, 1s base delay)
    - Log publication status with URL and timestamp
    - Return `PublicationResult` with success status and post URL
    - Implement `can_publish_today()` method checking 24-hour rate limit
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [ ]* 9.2 Write property test for tag generation presence
    - **Property 15: Tag Generation Presence**
    - **Validates: Requirements 7.4**

  - [ ]* 9.3 Write property test for publication rate limiting
    - **Property 16: Publication Rate Limiting**
    - **Validates: Requirements 7.7, 13.6**

  - [ ]* 9.4 Write property test for API key leak prevention
    - **Property 18: API Key Leak Prevention**
    - **Validates: Requirements 11.5**

  - [ ]* 9.5 Write unit tests for Publisher Agent
    - Test Medium API integration with mock responses
    - Test retry behavior on API failures
    - Test rate limiting enforcement
    - Test draft status setting
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 10. Implement Crawler Agent with ReAct loop
  - [ ] 10.1 Create `CrawlerAgent` class in `src/agents/crawler.py`
    - Initialize Playwright browser (headless mode)
    - Define `ActionType` enum and `CrawlerAction` dataclass
    - Implement `crawl(start_url, goal)` method with ReAct loop
    - Implement `reason(page_state)` method using LLM to decide next action
    - Implement `execute_action(action)` method for browser control (click, scroll, navigate, extract, wait)
    - Capture page accessibility tree for LLM reasoning (not raw HTML)
    - Maintain action history to avoid loops
    - Implement timeout mechanism (max 50 actions per crawl)
    - Check robots.txt before navigation
    - Return list of raw HTML from discovered articles
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.1.1-1.1.10_

  - [ ]* 10.2 Write property test for robots.txt compliance
    - **Property 1: Robots.txt Compliance**
    - **Validates: Requirements 1.9**

  - [ ]* 10.3 Write unit tests for Crawler Agent
    - Test action decision-making with mock LLM responses
    - Test browser action execution with mock Playwright
    - Test robots.txt checking
    - Test timeout mechanism
    - Test loop prevention
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10_

  - [ ]* 10.4 Write integration test for crawler with mock browser
    - Test full crawl workflow with realistic page structure
    - Test article link discovery
    - Test content extraction
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.10_

- [ ] 11. Implement FastAPI server with LangGraph orchestration
  - [ ] 11.1 Create API server in `src/api/server.py`
    - Initialize FastAPI app
    - Load configuration on startup with validation
    - Implement `/health` endpoint
    - Implement `/pipeline/trigger` endpoint (POST)
    - Implement `/pipeline/status` endpoint (GET)
    - Implement `/history` endpoint (GET)
    - Implement `/stats` endpoint (GET)
    - Add error handling middleware
    - Add logging middleware with correlation IDs
    - _Requirements: 9.1, 9.2, 9.5, 9.6, 9.7, 11.3, 11.4, 11.5_

  - [ ] 11.2 Create LangGraph workflow in `src/api/workflow.py`
    - Define `WorkflowState` TypedDict with all state fields
    - Create StateGraph with workflow nodes: crawl, extract, check_duplicate, write, edit, review, publish
    - Implement node functions for each agent
    - Add conditional edges for duplicate checking and review decisions
    - Implement regeneration logic (max 2 attempts per content item)
    - Add error handling for agent failures
    - Compile workflow graph
    - _Requirements: 9.2, 9.3, 9.4, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [ ]* 11.3 Write property test for concurrent execution prevention
    - **Property 17: Concurrent Execution Prevention**
    - **Validates: Requirements 8.4**

  - [ ]* 11.4 Write property test for regeneration attempt limit
    - **Property 20: Regeneration Attempt Limit**
    - **Validates: Requirements 13.3**

  - [ ]* 11.5 Write integration tests for API endpoints
    - Test pipeline trigger and status endpoints
    - Test history and stats endpoints
    - Test error handling and logging
    - _Requirements: 9.1, 9.2, 9.5, 9.6, 9.7_

  - [ ]* 11.6 Write integration test for LangGraph workflow
    - Test full workflow execution with mock agents
    - Test conditional branching (duplicate detection, review rejection)
    - Test regeneration logic
    - Test error handling and recovery
    - _Requirements: 9.2, 9.3, 9.4, 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement Scheduler
  - [ ] 13.1 Create `PipelineScheduler` class in `src/scheduler/scheduler.py`
    - Initialize with API client
    - Implement `run_pipeline()` method with concurrent execution prevention
    - Implement `start(time)` method using Python `schedule` library
    - Schedule daily execution at specified time (default 09:00)
    - Add logging for execution start, end, and status
    - Handle exceptions and mark failed runs
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 13.2 Write unit tests for Scheduler
    - Test daily scheduling configuration
    - Test concurrent execution prevention
    - Test manual trigger support
    - Test logging behavior
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 14. Create main entry point and CLI
  - Create `src/main.py` with CLI commands: `run-server`, `run-scheduler`, `trigger-pipeline`
  - Use Click or argparse for CLI argument parsing
  - Add `--config` flag for custom configuration file
  - Add `--log-level` flag for logging control
  - Implement graceful shutdown handling
  - _Requirements: 8.6, 9.1, 9.7, 11.1_

- [ ] 15. Add error handling utilities
  - Create `src/utils/retry.py` with `retry_with_backoff` function
  - Create `src/utils/circuit_breaker.py` with `CircuitBreaker` class
  - Create `src/utils/errors.py` with custom exception classes
  - Implement structured error logging with context
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 16. Create test fixtures and mocks
  - Create `tests/fixtures/sample_html.py` with ByteByteGo HTML samples
  - Create `tests/fixtures/sample_content.py` with ContentItem fixtures
  - Create `tests/fixtures/mock_responses.py` with mock LLM and API responses
  - Create `tests/conftest.py` with pytest fixtures for agents and services
  - _Requirements: All testing requirements_

- [ ] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 18. Write end-to-end test for full pipeline
  - Test complete pipeline execution from crawl to publish
  - Verify each stage produces expected output
  - Test error handling and recovery scenarios
  - Validate final publication to test Medium account
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

- [ ]* 19. Optional: Implement React Dashboard
  - [ ]* 19.1 Set up React project with TypeScript and Vite
    - Initialize React app in `dashboard/` directory
    - Install dependencies: React, TanStack Query, Tailwind CSS, React Router
    - Configure Tailwind CSS
    - Set up API client with axios or fetch
    - _Requirements: 10.1_

  - [ ]* 19.2 Create dashboard components
    - Create `PipelineStatus` component showing current execution status
    - Create `ProcessingHistory` component with table and filters
    - Create `ContentApproval` component for manual draft approval
    - Create `ErrorLog` component displaying failed runs
    - Create `SystemStats` component showing memory statistics
    - Create `ManualTrigger` button component
    - _Requirements: 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [ ]* 19.3 Implement API integration
    - Create API service layer communicating with FastAPI backend
    - Implement polling or WebSocket for real-time updates
    - Add error handling and loading states
    - _Requirements: 10.8_

  - [ ]* 19.4 Add dashboard styling and layout
    - Create responsive layout with navigation
    - Style components with Tailwind CSS
    - Add loading spinners and error messages
    - Implement dark mode support (optional)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 20. Create documentation
  - Create `README.md` with setup instructions, configuration guide, and usage examples
  - Create `docs/ARCHITECTURE.md` explaining system design and component interactions
  - Create `docs/DEPLOYMENT.md` with deployment instructions
  - Create `.env.example` with required environment variables
  - Document all API endpoints in OpenAPI/Swagger format
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ] 21. Final checkpoint - Verify complete system
  - Run full test suite (unit, property, integration, E2E)
  - Verify 80%+ code coverage
  - Test complete pipeline with real ByteByteGo content
  - Verify Medium draft publication works
  - Test scheduler with short interval
  - Review all error handling and logging
  - Ensure all 20 correctness properties pass
  - Ask the user if questions arise or if ready for production deployment.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design
- Unit tests validate specific examples and edge cases
- Integration tests validate component interactions
- E2E tests validate complete pipeline execution
- The React dashboard (task 19) is entirely optional
- All agents use async/await for non-blocking I/O
- Configuration is loaded from environment variables for security
- All external service calls include retry logic with exponential backoff
- Memory system persists to disk for recovery after restarts
