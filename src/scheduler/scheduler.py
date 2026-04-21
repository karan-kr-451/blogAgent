"""Scheduler for daily pipeline execution."""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

import httpx

from src.config import Config, get_config
from src.logging_config import get_logger
from src.companies_database import get_random_companies

logger = get_logger(__name__)


class PipelineScheduler:
    """
    Scheduler for triggering the content pipeline on a daily schedule.
    
    Uses the schedule library for timing control and prevents
    concurrent execution.
    """

    def __init__(self, config: Config | None = None):
        """
        Initialize the Pipeline Scheduler.
        
        Args:
            config: Application configuration. If None, uses global config.
        """
        self.config = config or get_config()
        self.is_running = False
        # ALWAYS resolve host+port from env vars at runtime.
        # config values can be stale; Render injects PORT dynamically.
        # API_HOST may be "0.0.0.0" (bind-all) — not valid for loopback calls, coerce to 127.0.0.1.
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("API_HOST", "127.0.0.1")
        if host == "0.0.0.0":
            host = "127.0.0.1"
        self.api_base_url = f"http://{host}:{port}"

        # Render injects RENDER_EXTERNAL_URL with the public HTTPS URL of the service.
        # We use this for keep-alive pings (internal loopback doesn't count as Render activity).
        self.public_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")

        logger.info(
            "PipelineScheduler initialized",
            extra={
                "agent": "Scheduler",
                "schedule_time": self.config.schedule_time,
                "schedule_enabled": self.config.schedule_enabled,
                "api_base_url": self.api_base_url,
                "keep_alive": bool(self.public_url),
            }
        )

    async def run_pipeline(self) -> dict[str, Any]:
        """
        Trigger the content pipeline.
        
        Returns:
            Pipeline execution result
        
        Raises:
            RuntimeError: If pipeline is already running
        """
        if self.is_running:
            logger.warning(
                "Pipeline already running, skipping",
                extra={"agent": "Scheduler"}
            )
            raise RuntimeError("Pipeline is already running")
        
        self.is_running = True
        
        try:
            logger.info(
                f"[{datetime.now()}] Starting scheduled pipeline run",
                extra={"agent": "Scheduler"}
            )
            
            # Call the API to trigger pipeline
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/pipeline/trigger",
                    json={"start_url": self.config.crawler_start_url}
                )
                response.raise_for_status()
                result = response.json()
            
            logger.info(
                f"[{datetime.now()}] Pipeline completed: {result.get('status')}",
                extra={"agent": "Scheduler", "result": result.get("status")}
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"[{datetime.now()}] Pipeline failed: {e}",
                extra={"agent": "Scheduler", "error": str(e)}
            )
            raise
        finally:
            self.is_running = False

    async def run_comment_responder(self) -> dict[str, Any]:
        """
        Trigger the comment responder agent via API.
        
        Returns:
            Execution result
        """
        try:
            logger.info(
                f"[{datetime.now()}] Starting scheduled comment response run",
                extra={"agent": "Scheduler"}
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base_url}/comments/respond")
                response.raise_for_status()
                result = response.json()
            
            logger.info(
                f"[{datetime.now()}] Comment responder triggered: {result.get('status')}",
                extra={"agent": "Scheduler"}
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"[{datetime.now()}] Comment responder trigger failed: {e}",
                extra={"agent": "Scheduler", "error": str(e)}
            )
            raise

    async def _keep_alive(self) -> None:
        """
        Ping the service's own public URL every 10 minutes to prevent
        Render's free tier from spinning the service down due to inactivity.

        Uses RENDER_EXTERNAL_URL (auto-injected by Render) so the ping goes
        through Render's load balancer and counts as real inbound traffic.
        Does nothing when running locally (no RENDER_EXTERNAL_URL set).
        """
        if not self.public_url:
            logger.info(
                "No RENDER_EXTERNAL_URL set — keep-alive disabled (local env).",
                extra={"agent": "Scheduler"}
            )
            return

        ping_url = f"{self.public_url}/health"
        logger.info(
            f"Keep-alive started. Pinging {ping_url} every 10 minutes.",
            extra={"agent": "Scheduler"}
        )

        while True:
            await asyncio.sleep(10 * 60)  # 10 minutes
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(ping_url)
                logger.info(
                    f"Keep-alive ping OK ({resp.status_code})",
                    extra={"agent": "Scheduler"}
                )
            except Exception as e:
                logger.warning(
                    f"Keep-alive ping failed: {e}",
                    extra={"agent": "Scheduler"}
                )

    async def start_async(self):
        """
        Start scheduler asynchronously (non-blocking).
        Perfect for running inside a FastAPI lifespan background task.
        """
        schedule_time = self.config.schedule_time

        if not self.config.schedule_enabled:
            logger.info("Scheduler is disabled in config", extra={"agent": "Scheduler"})
            return

        logger.info(
            f"Starting async scheduler (Daily: {schedule_time}, Comment Responder: Every Hour)",
            extra={"agent": "Scheduler"}
        )

        # Launch keep-alive concurrently so Render free tier stays awake
        asyncio.create_task(self._keep_alive())

        last_daily_run = None
        last_hourly_run = None

        # ── Startup catch-up ─────────────────────────────────────────────────
        # If today's scheduled time has ALREADY passed when the service starts
        # (e.g. deployed at 09:38 when schedule is 09:00), run the pipeline
        # immediately instead of waiting until tomorrow.
        now = datetime.now()
        sched_hour, sched_minute = map(int, schedule_time.split(":"))
        sched_today = now.replace(hour=sched_hour, minute=sched_minute, second=0, microsecond=0)

        if now >= sched_today:
            logger.info(
                f"Scheduled time {schedule_time} already passed today "
                f"(server started at {now.strftime('%H:%M')}). "
                "Triggering pipeline now as startup catch-up.",
                extra={"agent": "Scheduler"}
            )
            # Wait 15 s so the server is fully initialised before hitting /pipeline/trigger
            await asyncio.sleep(15)
            asyncio.create_task(self.run_pipeline())
            last_daily_run = now.date()
        # ─────────────────────────────────────────────────────────────────────

        while True:
            try:
                now = datetime.now()
                current_time = now.strftime("%H:%M")

                # 1. Daily pipeline — fires once at the scheduled minute
                if current_time == schedule_time and last_daily_run != now.date():
                    asyncio.create_task(self.run_pipeline())
                    last_daily_run = now.date()
                    logger.info(
                        f"Daily pipeline triggered at {current_time}.",
                        extra={"agent": "Scheduler"}
                    )

                # 2. Hourly comment responder — fires at the top of every hour
                if now.minute == 0 and last_hourly_run != now.hour:
                    asyncio.create_task(self.run_comment_responder())
                    last_hourly_run = now.hour
                    logger.info(
                        f"Hourly comment responder triggered at {now.strftime('%H:%M')}.",
                        extra={"agent": "Scheduler"}
                    )

            except Exception as e:
                logger.error(f"Scheduler error in loop: {e}", extra={"agent": "Scheduler"})

            # Check every 30 seconds (catches any minute window)
            await asyncio.sleep(30)

    def trigger_manual(self) -> dict[str, Any]:
        """
        Manually trigger pipeline execution.
        
        Returns:
            Pipeline execution result
        """
        logger.info("Manual pipeline trigger", extra={"agent": "Scheduler"})
        
        # Create new event loop for async execution
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.run_pipeline())


def create_scheduler(config: Config | None = None) -> PipelineScheduler:
    """
    Create a PipelineScheduler instance.
    
    Args:
        config: Application configuration
    
    Returns:
        Configured PipelineScheduler instance
    """
    return PipelineScheduler(config=config)
