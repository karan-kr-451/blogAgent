"""Crawler Agent with ReAct loop for autonomous web navigation."""

import re
import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import httpx
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from src.config import Config, get_config
from src.logging_config import get_logger
from src.models.data_models import CrawlerAction, PageState, ActionType
from src.utils.retry import retry_with_backoff, RetryError

logger = get_logger(__name__)


class CrawlerError(Exception):
    """Raised when crawling fails."""
    pass


class CrawlerAgent:
    """
    Agent that autonomously crawls web pages using LLM-driven decision making.
    
    Uses ReAct loop (Reason → Act → Observe) to analyze page state and
    decide which browser action to take next.
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize the Crawler Agent.
        
        Args:
            config: Application configuration. If None, uses global config.
        """
        self.config = config or get_config()
        self.max_actions = self.config.crawler_max_actions
        self.headless = self.config.crawler_headless
        
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.playwright = None
        
        self.action_history: list[CrawlerAction] = []
        self.robots_parser: RobotFileParser | None = None
        self.current_robots_url: str | None = None  # Track current robots URL
        
        # HTTP client for LLM calls
        self.llm_client = httpx.AsyncClient(
            base_url=self.config.ollama_endpoint.rstrip('/'),
            timeout=self.config.ollama_timeout,
            headers={
                "Content-Type": "application/json",
            }
        )
        
        # Add API key if configured
        if self.config.ollama_api_key:
            self.llm_client.headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"
        
        logger.info(
            "CrawlerAgent initialized",
            extra={
                "agent": "CrawlerAgent",
                "max_actions": self.max_actions,
                "headless": self.headless,
                "llm_model": self.config.ollama_model
            }
        )

    async def initialize(self) -> None:
        """Initialize Playwright browser."""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--js-flags=--max-old-space-size=250",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process"
                ]
            )
            # Use a realistic user agent
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1280, "height": 720}
            )
            self.page = await self.context.new_page()
            
            # Intercept and abort heavy assets to save memory
            async def block_resources(route):
                if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                    await route.abort()
                else:
                    await route.continue_()
            
            await self.page.route("**/*", block_resources)
            
            # Set default timeout to 30s
            self.page.set_default_timeout(30000)
            
            logger.info("Browser initialized with memory-saving stealth settings", extra={"agent": "CrawlerAgent"})

    async def crawl(self, start_url: str, goal: str = "find recent articles") -> list[str]:
        """
        Autonomously crawl from start_url to achieve goal.
        
        Args:
            start_url: Starting URL (e.g., ByteByteGo homepage)
            goal: High-level objective (e.g., "find recent articles")
        
        Returns:
            List of raw HTML content from discovered articles
        
        Raises:
            CrawlerError: If crawling fails
        """
        try:
            await self.initialize()
            
            logger.info(
                f"Starting crawl: {start_url}",
                extra={"agent": "CrawlerAgent", "url": start_url, "goal": goal}
            )
            
            # Check robots.txt
            await self._check_robots(start_url)
            
            # Navigate to start URL
            await self._navigate(start_url)
            
            # Take a screenshot after initial navigation
            try:
                shot_dir = Path("logs/screenshots")
                shot_dir.mkdir(parents=True, exist_ok=True)
                shot_path = shot_dir / f"initial_{datetime.now().timestamp()}.png"
                await self.page.screenshot(path=str(shot_path))
                logger.info(f"Initial screenshot saved: {shot_path}", extra={"agent": "CrawlerAgent"})
            except Exception as e:
                logger.warning(f"Failed to take initial screenshot: {e}")
            
            # ReAct loop
            collected_html = []
            action_count = 0
            
            while action_count < self.max_actions:
                # Get page state
                page_state = await self._get_page_state()
                
                # Reason about next action
                action = await self._reason(page_state, goal)
                
                # Execute action
                observation = await self.execute_action(action)
                self.action_history.append(action)
                action_count += 1
                
                # Collect HTML if this is an article page
                if action.action_type == ActionType.EXTRACT:
                    html = await self.page.content()
                    collected_html.append(html)
                    logger.info(f"Collected HTML from: {page_state.url}", extra={"agent": "CrawlerAgent"})
                
                # Check if we should stop
                if observation.get("done", False):
                    break

            logger.info(
                f"Crawl completed: {len(collected_html)} items collected",
                extra={"agent": "CrawlerAgent", "items": len(collected_html)}
            )

            return collected_html

        except CrawlerError:
            raise
        except NotImplementedError as e:
            # Platform-specific async issue (Windows Python 3.14+ event loop)
            error_msg = (
                "Windows Python 3.14+ event loop issue. "
                "Please restart server using: python start_server.py"
            )
            logger.exception(error_msg, extra={"agent": "CrawlerAgent"})
            raise CrawlerError(error_msg) from e
        except Exception as e:
            error_msg = f"Crawl failed: {type(e).__name__}: {str(e) or 'Unknown error'}"
            logger.exception(error_msg, extra={"agent": "CrawlerAgent"})
            raise CrawlerError(error_msg) from e
        finally:
            await self.close()

    async def reason(self, page_state: PageState, goal: str) -> CrawlerAction:
        """
        Use LLM to decide next action based on current page state.
        
        Args:
            page_state: Current page snapshot
            goal: Crawling goal
        
        Returns:
            Next action to execute
        """
        return await self._reason(page_state, goal)

    async def _reason(self, page_state: PageState, goal: str) -> CrawlerAction:
        """
        Internal reasoning method using LLM.
        
        Uses LLM to analyze page state and decide next action.
        """
        try:
            # Build prompt with page state
            prompt = self._build_reasoning_prompt(page_state, goal)
            
            # Call LLM with retry
            response = await retry_with_backoff(
                self._call_llm,
                prompt,
                max_retries=3,
                base_delay=1.0,
                max_delay=10.0,
                retry_exceptions=(httpx.HTTPError, TimeoutError, ConnectionError)
            )
            
            # Parse LLM response
            action = self._parse_llm_response(response)
            
            return action
            
        except Exception as e:
            logger.warning(f"LLM reasoning failed: {e}, using fallback")
            # Fallback to simple heuristic
            return self._fallback_reasoning(page_state)

    def _build_reasoning_prompt(self, page_state: PageState, goal: str) -> str:
        """Build prompt for LLM reasoning."""
        prompt = f"""You are a web crawling agent. Analyze the current page state and decide the next action.

GOAL: {goal}

CURRENT PAGE:
- URL: {page_state.url}
- Title: {page_state.title}
- Content Preview: {page_state.text_content}

AVAILABLE LINKS (first 20):
{json.dumps(page_state.links[:20], indent=2)}

ACTION HISTORY (last 5):
{json.dumps([{"action": a.action_type.value, "target": a.target} for a in self.action_history[-5:]], indent=2)}

AVAILABLE ACTIONS:
- click: Click on an element. Use "target" to specify the link text or URL.
- extract: Extract the current page's HTML content (use when on article page).
- scroll: Scroll down to see more content. Set "direction" to "down".
- navigate: Go to a specific URL. Use "target" to specify the URL.
- wait: Wait for content to load. Set "duration" in seconds.

INSTRUCTIONS:
1. Analyze if current page has article-like content to extract
2. Look for links that match the goal (articles, blog posts, tutorials)
3. Avoid clicking the same link twice (check action history)
4. Scroll if you need to see more content
5. Extract when you're on a page with substantial content

Respond with JSON ONLY:
{{"action": "action_type", "target": "target_text_or_url", "reason": "why you chose this action"}}

Your decision:"""
        
        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API for reasoning."""
        payload = {
            "model": self.config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower for more consistent decisions
                "num_predict": 500
            }
        }
        
        response = await self.llm_client.post("/api/generate", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get("response", "")

    def _parse_llm_response(self, response: str) -> CrawlerAction:
        """Parse LLM response into CrawlerAction."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            
            if json_match:
                data = json.loads(json_match.group())
                action_type = data.get("action", "extract")
                target = data.get("target")
                
                # Map string to ActionType enum
                action_map = {
                    "click": ActionType.CLICK,
                    "extract": ActionType.EXTRACT,
                    "scroll": ActionType.SCROLL,
                    "navigate": ActionType.NAVIGATE,
                    "wait": ActionType.WAIT,
                    "next": ActionType.NEXT,
                    "prev": ActionType.PREV
                }
                
                action_type_enum = action_map.get(action_type, ActionType.EXTRACT)
                
                # Handle scroll direction
                direction = None
                if action_type_enum == ActionType.SCROLL:
                    direction = "down"
                
                # Handle wait duration
                duration = None
                if action_type_enum == ActionType.WAIT:
                    duration = 2.0
                
                return CrawlerAction(
                    action_type=action_type_enum,
                    target=target,
                    direction=direction,
                    duration=duration
                )
            else:
                return self._fallback_reasoning(None)
                
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return self._fallback_reasoning(None)

    def _fallback_reasoning(self, page_state: PageState | None) -> CrawlerAction:
        """Fallback heuristic-based reasoning when LLM fails."""
        if page_state is None:
            return CrawlerAction(action_type=ActionType.EXTRACT)
        
        # If we have links, try to click one
        if page_state.links:
            for link in page_state.links[:5]:
                link_href = link.get('href', '')
                if not any(a.target == link_href for a in self.action_history):
                    return CrawlerAction(action_type=ActionType.CLICK, target=link_href)
        
        # Default to extract
        return CrawlerAction(action_type=ActionType.EXTRACT)

    async def execute_action(self, action: CrawlerAction) -> dict[str, Any]:
        """
        Execute browser action via Playwright.
        
        Args:
            action: Action to perform
        
        Returns:
            Observation result
        
        Raises:
            CrawlerError: If action fails
        """
        try:
            if self.page is None:
                raise CrawlerError("Page not initialized")
            
            result = {}
            if action.action_type == ActionType.CLICK:
                result = await self._click(action)
            elif action.action_type == ActionType.NEXT:
                result = await self._next()
            elif action.action_type == ActionType.PREV:
                result = await self._prev()
            elif action.action_type == ActionType.EXTRACT:
                result = await self._extract()
            elif action.action_type == ActionType.SCROLL:
                result = await self._scroll(action)
            elif action.action_type == ActionType.WAIT:
                result = await self._wait(action)
            elif action.action_type == ActionType.NAVIGATE:
                result = await self._navigate(action.target or "")
            else:
                raise CrawlerError(f"Unknown action type: {action.action_type}")
            
            # Take a screenshot for debugging
            try:
                shot_dir = Path("logs/screenshots")
                shot_dir.mkdir(parents=True, exist_ok=True)
                shot_path = shot_dir / f"action_{datetime.now().timestamp()}.png"
                await self.page.screenshot(path=str(shot_path))
                logger.info(f"Screenshot saved: {shot_path}", extra={"agent": "CrawlerAgent"})
            except Exception as e:
                logger.warning(f"Failed to take screenshot: {e}")
                
            return result
                
        except CrawlerError:
            raise
        except Exception as e:
            logger.error(f"Action execution failed: {e}", extra={"agent": "CrawlerAgent"})
            return {"error": str(e), "success": False}

    async def _click(self, action: CrawlerAction) -> dict[str, Any]:
        """Click on an element."""
        try:
            # Try to click by text or selector
            if action.target:
                # Try clicking by text content
                try:
                    await self.page.get_by_text(action.target, exact=False).first.click(timeout=5000)
                except Exception:
                    # Fallback to CSS selector
                    await self.page.click(action.target, timeout=5000)
                
                await self.page.wait_for_load_state("domcontentloaded")
                return {"success": True, "action": "click", "target": action.target}
            else:
                return {"success": False, "error": "No target specified for click"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _next(self) -> dict[str, Any]:
        """Navigate to next page (browser forward)."""
        try:
            await self.page.go_forward()
            await self.page.wait_for_load_state("domcontentloaded")
            return {"success": True, "action": "next"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _prev(self) -> dict[str, Any]:
        """Navigate to previous page (browser back)."""
        try:
            await self.page.go_back()
            await self.page.wait_for_load_state("domcontentloaded")
            return {"success": True, "action": "prev"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _extract(self) -> dict[str, Any]:
        """Extract current page HTML."""
        try:
            html = await self.page.content()
            text = await self.page.inner_text("body")
            return {
                "success": True,
                "action": "extract",
                "html": html,
                "text": text,
                "url": self.page.url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _scroll(self, action: CrawlerAction) -> dict[str, Any]:
        """Scroll the page."""
        try:
            direction = action.direction or "down"
            if direction == "down":
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            else:
                await self.page.evaluate("window.scrollBy(0, -window.innerHeight)")
            
            await self.page.wait_for_timeout(500)  # Wait for scroll
            return {"success": True, "action": "scroll", "direction": direction}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _wait(self, action: CrawlerAction) -> dict[str, Any]:
        """Wait for specified duration."""
        try:
            duration = action.duration or 1.0
            await self.page.wait_for_timeout(duration * 1000)
            return {"success": True, "action": "wait", "duration": duration}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _navigate(self, url: str) -> dict[str, Any]:
        """Navigate to a URL."""
        try:
            # Check robots.txt
            await self._check_robots(url)
            
            await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return {"success": True, "action": "navigate", "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_page_state(self) -> PageState:
        """
        Capture current page state for LLM reasoning.
        
        Returns:
            PageState object with current page information
        """
        try:
            url = self.page.url
            title = await self.page.title()
            text_content = await self.page.inner_text("body")
            
            # Get all links
            links = await self.page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.slice(0, 15).map(link => ({
                    text: link.textContent.trim().substring(0, 80),
                    href: link.getAttribute('href')
                }));
            }""")
            
            # EXTRACT IMAGES - Architecture diagrams and visual content
            images = await self.page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img'));
                return imgs.map(img => ({
                    src: img.getAttribute('src') || img.getAttribute('data-src') || '',
                    alt: img.getAttribute('alt') || img.getAttribute('title') || '',
                    width: img.getAttribute('width') || img.naturalWidth || 0,
                    height: img.getAttribute('height') || img.naturalHeight || 0
                })).filter(img => img.src && img.src.startsWith('http'));
            }""")
            
            # Store images in metadata for blog generation
            self.current_page_images = images
            
            # Limit text content length — shorter = faster LLM reasoning
            if len(text_content) > 1200:
                text_content = text_content[:1200] + "..."
            
            return PageState(
                url=url,
                title=title,
                text_content=text_content,
                links=links,
                action_history=self.action_history.copy(),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.warning(f"Failed to get page state: {e}")
            return PageState(
                url="",
                title="",
                text_content="",
                links=[],
                action_history=self.action_history.copy(),
                timestamp=datetime.utcnow()
            )

    async def _check_robots(self, url: str) -> None:
        """
        Check robots.txt before crawling URL.
        
        Args:
            url: URL to check
        
        Raises:
            CrawlerError: If URL is disallowed
        """
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            # Initialize robots parser if needed
            if self.robots_parser is None or self.current_robots_url != robots_url:
                self.robots_parser = RobotFileParser()
                self.robots_parser.set_url(robots_url)
                self.current_robots_url = robots_url
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self.robots_parser.read)
                    logger.info(f"Robots.txt loaded successfully for {parsed.netloc}", extra={"agent": "CrawlerAgent"})
                except Exception as e:
                    logger.warning(f"Failed to read robots.txt from {robots_url}: {e}")
                    return  # Allow crawling if robots.txt can't be read
            
            # Check if URL is allowed
            # Note: RobotFileParser.can_fetch can be overly strict for some sites
            # We'll log but not block unless it's clearly disallowed
            can_fetch = self.robots_parser.can_fetch("*", url)
            
            if not can_fetch:
                logger.warning(
                    f"URL may be disallowed by robots.txt: {url}",
                    extra={"agent": "CrawlerAgent"}
                )
                # Log warning but don't block - allow LLM to make the decision
                return
                
        except CrawlerError:
            raise
        except Exception as e:
            logger.warning(f"Robots.txt check failed: {e}")
            # Allow crawling if robots.txt check fails

    async def close(self) -> None:
        """Close browser and clean up resources."""
        try:
            if hasattr(self, 'llm_client') and self.llm_client:
                await self.llm_client.aclose()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser and LLM client closed", extra={"agent": "CrawlerAgent"})
        except Exception as e:
            logger.warning(f"Error closing resources: {e}")
