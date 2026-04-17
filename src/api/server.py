"""FastAPI server for the Autonomous Blog Agent."""

import logging
import sys
import asyncio
from typing import Any
from contextlib import asynccontextmanager
from datetime import datetime

# CRITICAL: Set WindowsProactorEventLoopPolicy BEFORE any async operations
# This is required for Playwright to work on Python 3.14+ Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import Config, get_config
from src.logging_config import get_logger, setup_logging
from src.memory.memory_system import MemorySystem
from src.api.workflow import get_workflow
from src.companies_database import get_random_companies, TECH_COMPANIES

logger = get_logger(__name__)


# Request/Response models
class PipelineTriggerRequest(BaseModel):
    """Request to trigger the content pipeline."""
    start_url: str | None = Field(
        default=None,
        description="Starting URL for crawling (overrides config if provided)"
    )


class PipelineStatusResponse(BaseModel):
    """Response with pipeline status."""
    status: str
    current_step: str
    items_processed: int
    errors: list[str]
    last_run: datetime | None = None


class HistoryEntry(BaseModel):
    """Entry in processing history."""
    content_id: str
    title: str
    url: str
    processed_at: str


class SystemStatsResponse(BaseModel):
    """Response with system statistics."""
    total_processed: int
    duplicates_detected: int
    last_publication: str | None
    success_rate: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_ready: bool
    timestamp: datetime
    version: str


# Global state
_pipeline_running = False
_pipeline_status = {
    "status": "idle",
    "current_step": "",
    "items_processed": 0,
    "errors": [],
    "last_run": None
}
_memory_system = None
_memory_system_ready = False


def get_memory_system():
    """Get the global memory system instance (initialized in lifespan)."""
    return _memory_system


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan for startup and shutdown."""
    # Startup
    if sys.platform == 'win32':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info("WindowsProactorEventLoopPolicy set in lifespan", extra={"agent": "API"})
    
    config = get_config()
    setup_logging(
        log_level=config.log_level,
        log_format=config.log_format,
        log_file="logs/agent.log"
    )

    logger.info("Starting Autonomous Blog Agent API", extra={"agent": "API"})

    # Launch memory system initialization in the background
    async def init_memory_background():
        global _memory_system, _memory_system_ready
        try:
            logger.info("Loading memory system in background...", extra={"agent": "API"})
            # Instantiate immediately
            _memory_system = MemorySystem()
            # Initialize (this loads the heavy sentence-transformers model)
            await _memory_system.initialize()
            _memory_system_ready = True
            logger.info("Memory system ready", extra={"agent": "API"})
        except Exception as e:
            logger.error(f"Memory system failed to load: {e}", extra={"agent": "API"})

    # Create background task so lifespan can complete (and port can open) immediately
    asyncio.create_task(init_memory_background())

    yield

    # Shutdown
    logger.info("Shutting down Autonomous Blog Agent API", extra={"agent": "API"})

    # Shutdown
    logger.info("Shutting down Autonomous Blog Agent API", extra={"agent": "API"})


# Create FastAPI app
app = FastAPI(
    title="Autonomous Blog Agent",
    description="Multi-agent system for autonomous blog content generation and publishing",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model_ready=_memory_system_ready,
        timestamp=datetime.utcnow(),
        version="0.1.0"
    )


@app.post("/pipeline/trigger")
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    request: PipelineTriggerRequest | None = None
):
    """
    Manually trigger content pipeline.
    """
    global _pipeline_running
    
    if _pipeline_running:
        raise HTTPException(
            status_code=409,
            detail="Pipeline is already running"
        )
    
    config = get_config()
    
    if request and request.start_url:
        targets = [{"url": request.start_url, "name": "Custom URL", "goal": None}]
    else:
        # Pick 2 random companies from database
        selected = get_random_companies(2)
        targets = [
            {
                "url": c["urls"][0], 
                "name": c["name"], 
                "goal": (
                    f"find recent articles about {c['name']} system designs, architecture patterns, "
                    f"machine learning system design, Artificial Intelligence (AI) system design, "
                    f"Generative AI infrastructure, and Agentic AI system architectures"
                )
            } 
            for c in selected
        ]
        logger.info(f"Triggering pipeline for {len(targets)} random companies: {[t['name'] for t in targets]}")
    
    # Run pipeline in background
    background_tasks.add_task(run_pipeline, targets)
    return {"status": "started", "message": f"Pipeline triggered for {len(targets)} targets"}


@app.post("/comments/respond")
async def trigger_comment_responder(
    background_tasks: BackgroundTasks
):
    """
    Trigger the comment responder agent to reply to new comments.
    """
    background_tasks.add_task(run_comment_responder)
    return {"status": "started", "message": "Comment responder triggered"}


async def run_comment_responder():
    """Run the comment responder agent in the background."""
    from src.agents.comment_responder import CommentResponderAgent
    try:
        agent = CommentResponderAgent()
        await agent.initialize()
        results = await agent.run()
        await agent.close()
        logger.info(f"Comment responder finished. Replied to {len(results)} comments.", extra={"agent": "API"})
    except Exception as e:
        logger.error(f"Comment responder task failed: {e}", extra={"agent": "API"})


async def run_pipeline(targets: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Run the content pipeline for multiple targets.
    """
    global _pipeline_running, _pipeline_status
    
    _pipeline_running = True
    _pipeline_status = {
        "status": "running",
        "current_step": "initializing",
        "items_processed": 0,
        "errors": [],
        "last_run": datetime.utcnow()
    }
    
    total_processed = 0
    all_errors = []
    
    try:
        workflow = get_workflow()
        
        for i, target in enumerate(targets):
            url = target["url"]
            name = target["name"]
            goal = target.get("goal")
            
            logger.info(f"Processing target {i+1}/{len(targets)}: {name} ({url})", extra={"agent": "API"})
            _pipeline_status["current_step"] = f"Processing {name}"
            
            # Initial state for this target
            initial_state = {
                "start_url": url,
                "company_name": name,
                "crawl_goal": goal,
                "raw_html_list": [],
                "content_items": [],
                "current_item": None,
                "is_duplicate": False,
                "draft": None,
                "metadata": {"target_index": i, "total_targets": len(targets)},
                "errors": [],
                "status": "running"
            }
            
            # Execute workflow
            result = await workflow.ainvoke(initial_state)
            
            # Aggregate results
            total_processed += len(result.get("content_items", []))
            if result.get("errors"):
                all_errors.extend(result["errors"])
                
            _pipeline_status["items_processed"] = total_processed
            
        # Update final status
        _pipeline_status["status"] = "completed" if not all_errors else "completed_with_errors"
        _pipeline_status["errors"] = all_errors
        
        return {
            "status": _pipeline_status["status"],
            "items_processed": total_processed,
            "errors": all_errors
        }
        
    except Exception as e:
        logger.error(f"Pipeline loop failed: {e}", extra={"agent": "API"}, exc_info=True)
        _pipeline_status["status"] = "failed"
        _pipeline_status["errors"].append(str(e))
        
        return {
            "status": "failed",
            "items_processed": total_processed,
            "errors": all_errors + [str(e)]
        }
    finally:
        _pipeline_running = False


@app.get("/pipeline/status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """Get current pipeline status."""
    return PipelineStatusResponse(
        status=_pipeline_status["status"],
        current_step=_pipeline_status["current_step"],
        items_processed=_pipeline_status["items_processed"],
        errors=_pipeline_status["errors"],
        last_run=_pipeline_status["last_run"]
    )


@app.get("/history")
async def get_history(limit: int = 50):
    """Get processing history."""
    if not _memory_system_ready:
        return [] # Return empty instead of error for smoother dashboard load
        
    try:
        memory = get_memory_system()
        history = await memory.get_history(limit=limit)
        
        return [
            HistoryEntry(
                content_id=entry["content_id"],
                title=entry["metadata"]["title"],
                url=entry["metadata"]["url"],
                processed_at=entry["metadata"]["processed_at"]
            )
            for entry in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@app.get("/stats", response_model=SystemStatsResponse)
async def get_stats():
    """Get system statistics."""
    if not _memory_system_ready:
        return SystemStatsResponse(
            total_processed=0,
            duplicates_detected=0,
            last_publication=None,
            success_rate=0.0
        )
        
    try:
        memory = get_memory_system()
        stats = await memory.get_stats()
        
        # Calculate success rate
        total = stats["total_processed"]
        duplicates = stats["duplicates_detected"]
        success_rate = ((total - duplicates) / total * 100) if total > 0 else 0.0
        
        return SystemStatsResponse(
            total_processed=stats["total_processed"],
            duplicates_detected=stats["duplicates_detected"],
            last_publication=stats.get("last_publication"),
            success_rate=round(success_rate, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")



@app.get("/drafts")
async def list_drafts():
    """List all generated blog drafts."""
    try:
        from pathlib import Path
        
        drafts_dir = Path("drafts")
        if not drafts_dir.exists():
            return []
        
        drafts = []
        for date_dir in sorted(drafts_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                for md_file in date_dir.glob("*.md"):
                    # Read file content
                    content = md_file.read_text(encoding='utf-8')
                    
                    # Parse frontmatter
                    import re
                    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    tags_match = re.search(r'\*\*Tags:\*\*\s+(.+)$', content, re.MULTILINE)
                    word_count_match = re.search(r'\*\*Word Count:\*\*\s+(\d+)', content)
                    source_match = re.search(r'\*\*Source:\*\*\s+(.+)$', content, re.MULTILINE)
                    
                    # Extract the actual blog body (between the two horizontal rules)
                    body_content = content
                    parts = content.split('\n---\n')
                    if len(parts) >= 3:
                         # parts[0] is the top metadata
                         # parts[-1] is the generated by footer
                         # Everything in between is the actual content
                         body_content = '\n---\n'.join(parts[1:-1]).strip()
                    
                    # Remove redundant `# Title` at the beginning if generated by the LLM
                    body_content = re.sub(r'^#\s+.*?\n+', '', body_content, count=1).strip()
                    
                    draft = {
                        "id": f"{date_dir.name}-{md_file.stem}",
                        "title": title_match.group(1) if title_match else md_file.stem,
                        "content": body_content,
                        "original_content": content,
                        "tags": tags_match.group(1).split(',') if tags_match else [],
                        "word_count": int(word_count_match.group(1)) if word_count_match else 0,
                        "source_url": source_match.group(1) if source_match else "",
                        "generated_at": date_dir.name,
                        "file_path": str(md_file)
                    }
                    drafts.append(draft)
        
        return drafts
    except Exception as e:
        logger.error(f"Failed to list drafts: {e}")
        return []


# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", extra={"agent": "API"})
    
    # Don't expose internal details
    return {
        "status": "error",
        "message": "Internal server error",
        "detail": str(exc) if app.debug else "An internal error occurred"
    }
