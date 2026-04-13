"""Core data models for the Autonomous Blog Agent."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Literal, Any
import json


class ActionType(Enum):
    """Browser action types for the Crawler Agent."""
    CLICK = "click"
    NEXT = "next"
    PREV = "prev"
    EXTRACT = "extract"
    SCROLL = "scroll"
    WAIT = "wait"
    NAVIGATE = "navigate"


class ReviewDecision(Enum):
    """Review decision outcomes."""
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class CrawlerAction:
    """Represents a browser action for the Crawler Agent."""
    action_type: ActionType
    target: str | None = None  # Element description or URL
    direction: Literal["up", "down"] | None = None  # For scroll
    duration: float | None = None  # For wait (seconds)


@dataclass
class PageState:
    """Represents the current state of a web page during crawling."""
    url: str
    title: str
    text_content: str
    links: list[dict[str, str]]  # [{"text": str, "href": str}]
    action_history: list[CrawlerAction]
    timestamp: datetime


@dataclass
class ContentItem:
    """Structured content extracted from a web page."""
    title: str
    author: str | None
    publication_date: datetime | None
    url: str
    text_content: str
    code_blocks: list[str]
    images: list[str]
    metadata: dict[str, Any]
    
    def to_json(self) -> dict[str, Any]:
        """Serialize ContentItem to JSON-compatible dict."""
        data = asdict(self)
        # Convert datetime to ISO format string
        if self.publication_date:
            data["publication_date"] = self.publication_date.isoformat()
        return data
    
    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ContentItem":
        """Deserialize ContentItem from JSON dict."""
        # Convert ISO format string back to datetime
        if data.get("publication_date"):
            data["publication_date"] = datetime.fromisoformat(data["publication_date"])
        return cls(**data)


@dataclass
class BlogPost:
    """Generated blog post with metadata."""
    title: str
    content: str  # Markdown format
    tags: list[str]
    word_count: int
    source_url: str
    generated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Convert blog post to markdown format for publishing."""
        md_parts = [
            f"# {self.title}\n",
            f"\n{self.content}\n",
            f"\n---\n",
            f"*Tags: {', '.join(self.tags)}*\n",
            f"*Source: {self.source_url}*\n",
        ]
        return "".join(md_parts)
    
    def to_json(self) -> dict[str, Any]:
        """Serialize BlogPost to JSON-compatible dict."""
        data = asdict(self)
        # Convert datetime to ISO format string
        data["generated_at"] = self.generated_at.isoformat()
        return data
    
    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "BlogPost":
        """Deserialize BlogPost from JSON dict."""
        # Convert ISO format string back to datetime
        data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        return cls(**data)


@dataclass
class EditedPost:
    """Blog post after editing with change tracking."""
    post: BlogPost
    changes: list[str]  # Description of edits made


@dataclass
class ReviewResult:
    """Result of content originality review."""
    decision: ReviewDecision
    similarity_score: float
    justification: str
    issues: list[str] = field(default_factory=list)


@dataclass
class PublicationResult:
    """Result of publishing to Medium."""
    success: bool
    post_url: str | None
    error: str | None
    published_at: datetime
