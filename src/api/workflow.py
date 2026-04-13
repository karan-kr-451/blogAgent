"""LangGraph workflow for the Autonomous Blog Agent pipeline."""

import logging
import sys
import asyncio
import json
from typing import TypedDict, Annotated, Sequence, Any
from datetime import datetime

from langgraph.graph import StateGraph, END

# Use process-safe logging if possible, but for now standard logger is fine
logger = logging.getLogger(__name__)

# State definition
class WorkflowState(TypedDict):
    """Pipeline state for LangGraph."""
    start_url: str
    company_name: str | None
    crawl_goal: str | None
    raw_html_list: list[str]
    content_items: list[dict[str, Any]]
    current_item: dict[str, Any] | None
    draft: dict[str, Any] | None
    is_duplicate: bool
    status: str
    errors: list[str]
    metadata: dict[str, Any]

# Agent node functions
async def crawl_node(state: WorkflowState) -> WorkflowState:
    """Crawl articles from start URL."""
    logger.info("Starting crawl node", extra={"agent": "Workflow", "url": state["start_url"]})

    # Determine goal
    crawl_goal = state.get("crawl_goal")
    if not crawl_goal:
        company_name = state.get("company_name", "the tech company")
        crawl_goal = (
            f"find recent articles about {company_name} system designs, architecture patterns, "
            f"machine learning system design, Artificial Intelligence (AI) system design, "
            f"Generative AI infrastructure, and Agentic AI system architectures"
        )

    try:
        # Run crawler directly in the same event loop (more reliable on Windows)
        from src.agents.crawler import CrawlerAgent
        crawler = CrawlerAgent()
        
        try:
            results = await crawler.crawl(
                start_url=state["start_url"],
                goal=crawl_goal
            )

            raw_html_list = results
            
            # If crawler found nothing, create fallback content
            if not raw_html_list:
                company_name = state.get("company_name", "Tech Company")
                logger.info(f"No HTML collected, using fallback for {company_name}", extra={"agent": "Workflow"})
                raw_html_list = [f"""
                <html><head><title>{company_name} Engineering</title></head>
                <body><article>
                <h1>{company_name} System Design and Architecture</h1>
                <p>{company_name} engineers scalable systems using modern architectural patterns.</p>
                <h2>Key Components</h2>
                <p>Microservices, distributed databases, caching, load balancing, and event-driven design.</p>
                </article></body></html>
                """]

            logger.info(f"Crawl complete: {len(raw_html_list)} items", extra={"agent": "Workflow"})

            return {
                **state,
                "raw_html_list": raw_html_list,
                "status": "running"
            }
        finally:
            await crawler.close()

    except Exception as e:
        logger.error(f"Crawl node failed: {e}", extra={"agent": "Workflow"}, exc_info=True)
        return {
            **state,
            "raw_html_list": [],
            "errors": state["errors"] + [f"Crawl failed: {str(e)}"],
            "status": "failed"
        }

async def extract_node(state: WorkflowState) -> WorkflowState:
    """Extract content from raw HTML."""
    try:
        from src.agents.extractor import ExtractorAgent
        # I need to verify imports for other agents too

        logger.info("Starting extract node", extra={"agent": "Workflow"})

        from src.agents.extractor import ExtractorAgent
        extractor = ExtractorAgent()
        content_items = []

        if state["raw_html_list"]:
            # For now process the first one found
            content_item = await extractor.extract(
                raw_html=state["raw_html_list"][0],
                url=state["start_url"]
            )
            content_items.append(content_item)

            # Convert ContentItem to dict for state storage
            content_item_dict = {
                "title": content_item.title,
                "author": content_item.author,
                "publication_date": content_item.publication_date.isoformat() if content_item.publication_date else None,
                "url": content_item.url,
                "text_content": content_item.text_content,
                "code_blocks": content_item.code_blocks,
                "images": content_item.images,
                "metadata": content_item.metadata
            }

            return {
                **state,
                "content_items": content_items,
                "current_item": content_item_dict,
                "status": "running"
            }
        else:
            return {
                **state,
                "status": "skipped",
                "errors": state["errors"] + ["No HTML content to extract"]
            }
    except Exception as e:
        logger.error(f"Extract node failed: {e}", extra={"agent": "Workflow"})
        return {
            **state,
            "errors": state["errors"] + [f"Extraction failed: {str(e)}"],
            "status": "failed"
        }

async def check_duplicate_node(state: WorkflowState) -> WorkflowState:
    """Check if the content is a duplicate using Vector Memory."""
    try:
        if not state["current_item"]:
            return {**state, "is_duplicate": False}

        from src.memory.memory_system import MemorySystem
        memory = MemorySystem()
        await memory.initialize()
            
        # Compute embedding for the content
        text_to_check = f"{state['current_item']['title']} {state['current_item']['text_content'][:1000]}"
        embedding = await memory.compute_embedding(text_to_check)
        
        # Check for duplicates
        is_duplicate = await memory.check_duplicate(embedding)
        
        if is_duplicate:
            logger.info(f"Duplicate content detected: {state['current_item']['title']}", extra={"agent": "Workflow"})
        
        return {
            **state,
            "is_duplicate": is_duplicate
        }
    except Exception as e:
        logger.error(f"Duplicate check failed: {e}", extra={"agent": "Workflow"})
        return {**state, "is_duplicate": False}

async def writer_node(state: WorkflowState) -> WorkflowState:
    """Write blog post draft."""
    try:
        from src.agents.writer import WriterAgent
        from src.models.data_models import ContentItem, BlogPost
        writer = WriterAgent()

        if state["is_duplicate"]:
            return state

        # Convert content_item dict to ContentItem object if needed
        current_item = state["current_item"]
        if isinstance(current_item, dict):
            content_item = ContentItem(
                title=current_item.get("title", "Untitled"),
                author=current_item.get("author", ""),
                publication_date=current_item.get("publication_date"),
                url=current_item.get("url", state["start_url"]),
                text_content=current_item.get("text_content", ""),
                code_blocks=current_item.get("code_blocks", []),
                images=current_item.get("images", []),
                metadata=current_item.get("metadata", {})
            )
        else:
            content_item = current_item

        # Generate blog post (method is called generate, not write)
        blog_post = await writer.generate(content_item)

        # Convert BlogPost to dict for state storage
        draft_dict = {
            "title": blog_post.title,
            "content": blog_post.content,
            "tags": blog_post.tags,
            "word_count": blog_post.word_count,
            "source_url": blog_post.source_url,
            "generated_at": blog_post.generated_at,
            "metadata": {"original_title": content_item.title}
        }

        return {
            **state,
            "draft": draft_dict
        }
    except Exception as e:
        logger.error(f"Writer node failed: {e}", extra={"agent": "Workflow"})
        return {**state, "status": "failed", "errors": state["errors"] + [str(e)]}

async def editor_node(state: WorkflowState) -> WorkflowState:
    """Edit blog post draft."""
    try:
        from src.agents.editor import EditorAgent
        from src.models.data_models import BlogPost
        editor = EditorAgent()

        if not state["draft"]:
            return state

        # Convert draft dict to BlogPost object if needed
        draft_data = state["draft"]
        if isinstance(draft_data, dict):
            blog_post = BlogPost(
                title=draft_data.get("title", "Untitled"),
                content=draft_data.get("content", ""),
                tags=draft_data.get("tags", []),
                word_count=draft_data.get("word_count", 0),
                source_url=draft_data.get("source_url", state.get("start_url", "")),
                generated_at=draft_data.get("generated_at", datetime.utcnow())
            )
        else:
            blog_post = draft_data

        edited = await editor.edit(blog_post)
        
        # Convert back to dict for state storage
        edited_draft = {
            "title": edited.post.title,
            "content": edited.post.content,
            "tags": edited.post.tags,
            "word_count": edited.post.word_count,
            "source_url": edited.post.source_url,
            "generated_at": edited.post.generated_at,
            "metadata": draft_data.get("metadata", {}) if isinstance(draft_data, dict) else {}
        }

        return {
            **state,
            "draft": edited_draft
        }
    except Exception as e:
        logger.error(f"Editor node failed: {e}", extra={"agent": "Workflow"})
        return state

async def reviewer_node(state: WorkflowState) -> WorkflowState:
    """Review blog post draft."""
    try:
        from src.agents.reviewer import ReviewerAgent
        from src.models.data_models import BlogPost, ContentItem
        reviewer = ReviewerAgent()
        await reviewer.initialize()

        if not state["draft"]:
            return state

        # Convert draft dict to BlogPost object if needed
        draft_data = state["draft"]
        if isinstance(draft_data, dict):
            blog_post = BlogPost(
                title=draft_data.get("title", "Untitled"),
                content=draft_data.get("content", ""),
                tags=draft_data.get("tags", []),
                word_count=draft_data.get("word_count", 0),
                source_url=draft_data.get("source_url", state.get("start_url", "")),
                generated_at=draft_data.get("generated_at", datetime.utcnow())
            )
        else:
            blog_post = draft_data

        # Convert current_item dict to ContentItem object if needed
        current_item = state.get("current_item")
        if isinstance(current_item, dict):
            content_item = ContentItem(
                title=current_item.get("title", "Untitled"),
                author=current_item.get("author", ""),
                publication_date=current_item.get("publication_date"),
                url=current_item.get("url", state["start_url"]),
                text_content=current_item.get("text_content", ""),
                code_blocks=current_item.get("code_blocks", []),
                images=current_item.get("images", []),
                metadata=current_item.get("metadata", {})
            )
        else:
            content_item = current_item

        review = await reviewer.review(blog_post, content_item)

        # Merge review into draft dict
        state["draft"]["review"] = {
            "decision": review.decision.value,
            "similarity_score": review.similarity_score,
            "justification": review.justification
        }

        return state
    except Exception as e:
        logger.error(f"Reviewer node failed: {e}", extra={"agent": "Workflow"})
        return state

async def seo_node(state: WorkflowState) -> WorkflowState:
    """Optimize blog post for SEO and social media."""
    try:
        from src.agents.seo import SEOAgent
        from src.models.data_models import BlogPost
        
        if not state["draft"]:
            return state

        # Convert draft dict to BlogPost object
        draft_data = state["draft"]
        if isinstance(draft_data, dict):
            blog_post = BlogPost(
                title=draft_data.get("title", "Untitled"),
                content=draft_data.get("content", ""),
                tags=draft_data.get("tags", []),
                word_count=draft_data.get("word_count", 0),
                source_url=draft_data.get("source_url", state.get("start_url", "")),
                generated_at=draft_data.get("generated_at", datetime.utcnow())
            )
        else:
            blog_post = draft_data

        # Run SEO optimization (now returns 4 values including platform content)
        seo_agent = SEOAgent()
        optimized_post, seo_metadata, seo_score, platform_content = seo_agent.optimize(blog_post)

        # Merge SEO data into draft dict
        state["draft"]["content"] = optimized_post.content
        state["draft"]["seo"] = {
            "meta_title": seo_metadata.meta_title,
            "meta_description": seo_metadata.meta_description,
            "keywords": seo_metadata.keywords[:10],
            "lsi_keywords": seo_metadata.lsi_keywords[:10],
            "reading_time": seo_metadata.reading_time,
            "og_title": seo_metadata.og_title,
            "og_description": seo_metadata.og_description,
            "schema_markup": seo_metadata.schema_markup,
            "table_of_contents": seo_metadata.table_of_contents,
            "seo_score": seo_score.overall,
            "recommendations": seo_score.recommendations,
            # Platform-specific content
            "linkedin_post": platform_content.linkedin_post,
            "linkedin_hashtags": platform_content.linkedin_hashtags,
            "twitter_thread": platform_content.twitter_thread,
            "twitter_hashtags": platform_content.twitter_hashtags,
            "devto_front_matter": platform_content.devto_front_matter,
            "devto_tags": platform_content.devto_tags,
            "hashnode_front_matter": platform_content.hashnode_front_matter,
            "short_teaser": platform_content.short_teaser
        }

        logger.info(
            f"SEO optimization complete: Score {seo_score.overall}/100",
            extra={
                "agent": "Workflow",
                "seo_score": seo_score.overall,
                "keywords": len(seo_metadata.keywords),
                "lsi_keywords": len(seo_metadata.lsi_keywords),
                "platform_content_ready": sum([
                    bool(platform_content.linkedin_post),
                    bool(platform_content.twitter_thread),
                    bool(platform_content.devto_front_matter),
                    bool(platform_content.hashnode_front_matter)
                ])
            }
        )

        return state
    except Exception as e:
        logger.error(f"SEO node failed: {e}", extra={"agent": "Workflow"})
        # Don't fail the pipeline for SEO issues, just continue
        return state

async def publisher_node(state: WorkflowState) -> WorkflowState:
    """Publish blog post draft."""
    try:
        from src.agents.publisher import PublisherAgent
        from src.models.data_models import BlogPost
        publisher = PublisherAgent()
        await publisher.initialize()  # Required for memory system / rate limiting

        if not state["draft"]:
            return state

        # Convert draft dict to BlogPost model if needed
        draft_data = state["draft"]
        if isinstance(draft_data, dict):
            blog_post = BlogPost(
                title=draft_data.get("title", "Untitled"),
                content=draft_data.get("content", ""),
                tags=draft_data.get("tags", []),
                word_count=draft_data.get("word_count", 0),
                source_url=draft_data.get("source_url", state.get("start_url", "")),
                generated_at=draft_data.get("generated_at", datetime.utcnow())
            )
        else:
            blog_post = draft_data

        result = await publisher.publish(blog_post)

        # result is a PublicationResult dataclass — use attribute access, not .get()
        if result.success:
            # Add to memory if publication succeeded
            from src.memory.memory_system import MemorySystem
            from src.models.data_models import ContentItem

            memory = MemorySystem()
            await memory.initialize()

            # Create a ContentItem for storage from the draft
            content_for_memory = ContentItem(
                title=state["draft"]["title"],
                text_content=state["draft"]["content"],
                url=state["draft"].get("source_url", state["start_url"]),
                metadata=state["draft"].get("metadata", {})
            )

            embedding = await memory.compute_embedding(content_for_memory.text_content)
            await memory.store(content_for_memory, embedding)

            logger.info(
                f"Published successfully: {result.post_url}",
                extra={"agent": "Workflow", "url": result.post_url}
            )

            return {
                **state,
                "status": "completed",
                "metadata": {
                    **state["metadata"],
                    "publish_result": {
                        "success": result.success,
                        "post_url": result.post_url,
                        "error": result.error,
                        "published_at": result.published_at.isoformat() if result.published_at else None
                    }
                }
            }
        else:
            return {
                **state,
                "status": "failed",
                "errors": state["errors"] + [f"Publishing failed: {result.error}"]
            }
    except Exception as e:
        logger.error(f"Publisher node failed: {e}", extra={"agent": "Workflow"})
        return {**state, "status": "failed", "errors": state["errors"] + [str(e)]}

def should_continue(state: WorkflowState):
    """Router for conditional edges."""
    if not state["raw_html_list"] or state["status"] == "failed":
        return "end"
    if state["is_duplicate"]:
        return "end"
    return "continue"

# Graph construction
def create_pipeline_graph():
    """Create the LangGraph workflow."""
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("crawl", crawl_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("check_duplicate", check_duplicate_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("editor", editor_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("seo", seo_node)
    workflow.add_node("publisher", publisher_node)

    # Set entry point
    workflow.set_entry_point("crawl")

    # Add simple edges
    workflow.add_edge("extract", "check_duplicate")

    # Add conditional edges
    workflow.add_conditional_edges(
        "crawl",
        should_continue,
        {
            "continue": "extract",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "check_duplicate",
        should_continue,
        {
            "continue": "writer",
            "end": END
        }
    )

    # Full linear path after check_duplicate with SEO optimization before publishing
    workflow.add_edge("writer", "editor")
    workflow.add_edge("editor", "reviewer")
    workflow.add_edge("reviewer", "seo")
    workflow.add_edge("seo", "publisher")
    workflow.add_edge("publisher", END)
    
    return workflow.compile()

# Singleton instance of the graph
pipeline_app = create_pipeline_graph()

def get_workflow():
    """Get the compiled pipeline graph."""
    return pipeline_app
