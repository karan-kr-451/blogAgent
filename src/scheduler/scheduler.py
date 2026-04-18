"""Scheduler for daily pipeline execution."""

import asyncio
import logging
import schedule
import time
from datetime import datetime
from typing import Any
from pathlib import Path

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
        # For internal loopback calls, use localhost if binding to 0.0.0.0
        host = self.config.api_host
        if host == "0.0.0.0":
            host = "127.0.0.1"
        self.api_base_url = f"http://{host}:{self.config.api_port}"
        
        logger.info(
            "PipelineScheduler initialized",
            extra={
                "agent": "Scheduler",
                "schedule_time": self.config.schedule_time,
                "schedule_enabled": self.config.schedule_enabled
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

    def start(self, time: str | None = None):
        """
        Start scheduler with daily execution at specified time.

        Args:
            time: Time to run pipeline (HH:MM format). Uses config if None.
        """
        schedule_time = time or self.config.schedule_time

        if not self.config.schedule_enabled:
            logger.info("Scheduler is disabled, not starting", extra={"agent": "Scheduler"})
            return

        logger.info(
            f"Starting scheduler with daily execution at {schedule_time}",
            extra={
                "agent": "Scheduler",
                "schedule_time": schedule_time,
                "api_url": self.api_base_url
            }
        )

        # Schedule daily run - use sync wrapper that creates its own event loop
        schedule.every().day.at(schedule_time).do(self._run_pipeline_sync)
        
        # Schedule comment responder to run every hour
        schedule.every().hour.do(self._run_comment_responder_sync)

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

        last_daily_run = None
        last_hourly_run = None

        while True:
            try:
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                
                # 1. Check for daily pipeline run
                # Using a small window or state check to ensure it runs only once at that minute
                if current_time == schedule_time and last_daily_run != now.date():
                    # Check connection before triggering (one-time check on startup)
                    if last_daily_run is None:
                        await asyncio.sleep(5) # Give the server a moment to start
                    
                    # Run in background to not block the scheduler loop
                    asyncio.create_task(self.run_pipeline())
                    last_daily_run = now.date()
                    logger.info(f"Daily pipeline scheduled for {current_time} triggered.", extra={"agent": "Scheduler"})

                # 2. Check for hourly comment responder
                if now.minute == 0 and last_hourly_run != now.hour:
                    asyncio.create_task(self.run_comment_responder())
                    last_hourly_run = now.hour
                    logger.info(f"Hourly comment responder triggered.", extra={"agent": "Scheduler"})

            except Exception as e:
                logger.error(f"Scheduler error in loop: {e}", extra={"agent": "Scheduler"})
            
            # Wait 30 seconds before next check for higher precision
            await asyncio.sleep(30)

    def _run_scheduler_loop(self):
        """Run the scheduler loop."""
        logger.info("Scheduler loop started", extra={"agent": "Scheduler"})

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user", extra={"agent": "Scheduler"})
        except Exception as e:
            logger.error(f"Scheduler loop failed: {e}", extra={"agent": "Scheduler"})

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
