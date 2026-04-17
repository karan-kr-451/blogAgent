"""Main entry point and CLI for the Autonomous Blog Agent."""

import asyncio
import click
import uvicorn
import sys
from pathlib import Path

# CRITICAL: Set WindowsProactorEventLoopPolicy BEFORE any async operations
# This is required for Playwright to work on Python 3.14+ Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from src.config import Config, get_config
from src.logging_config import setup_logging, get_logger
from src.scheduler.scheduler import PipelineScheduler
from src.api.server import app

logger = get_logger(__name__)


@click.group()
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']), 
              default=None, help='Logging level (defaults to .env LOG_LEVEL)')
@click.option('--log-format', type=click.Choice(['json', 'text']), default=None, 
              help='Log output format (defaults to .env LOG_FORMAT)')
@click.option('--log-file', type=str, default=None, help='Log file path (defaults to .env LOG_FILE)')
@click.pass_context
def cli(ctx, log_level, log_format, log_file):
    """Autonomous Blog Agent CLI."""
    config = get_config()
    
    # Resolve values: CLI arg > .env/Config > Default
    log_level = log_level or config.log_level
    log_format = log_format or config.log_format
    log_file = log_file or config.log_file
    
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level
    ctx.obj['log_format'] = log_format
    ctx.obj['log_file'] = log_file
    
    # Setup logging
    setup_logging(log_level=log_level, log_format=log_format, log_file=log_file)


import os

@cli.command()
@click.option('--host', default=None, help='API server host (defaults to .env API_HOST)')
@click.option('--port', default=None, type=int, help='API server port (falls back to PORT env or .env API_PORT)')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.pass_context
def run_server(ctx, host, port, reload):
    """Start the FastAPI API server."""
    config = get_config()
    
    # Resolve host: CLI arg > .env > Default
    host = host or config.api_host or "0.0.0.0"
    
    # Resolve PORT at runtime for Render compatibility
    if port is None:
        port = int(os.environ.get("PORT", config.api_port or 8000))
    
    logger.info(f"Starting API server on {host}:{port}", extra={"agent": "CLI"})
    
    # Set the resolved port and host in config as well
    config.api_port = port
    config.api_host = host
    
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=["src"] if reload else None,
        log_level=config.log_level.lower()
    )


@cli.command()
@click.option('--time', default=None, help='Daily execution time (HH:MM) (defaults to .env SCHEDULE_TIME)')
@click.pass_context
def run_scheduler(ctx, time):
    """Run the agent on a daily schedule."""
    config = get_config()
    schedule_time = time or config.schedule_time
    
    logger.info(f"Starting scheduler for {schedule_time}", extra={"agent": "CLI"})
    
    scheduler = PipelineScheduler(config=config)
    
    try:
        scheduler.start(time=schedule_time)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user", extra={"agent": "CLI"})
        sys.exit(0)


@cli.command()
@click.option('--url', default=None, help='Starting URL for crawling')
@click.pass_context
def trigger_pipeline(ctx, url):
    """Manually trigger the content pipeline."""
    config = get_config()
    
    logger.info("Manually triggering pipeline", extra={"agent": "CLI"})
    
    scheduler = PipelineScheduler(config=config)
    
    try:
        result = scheduler.trigger_manual()
        click.echo(f"\nPipeline Result:")
        click.echo(f"Status: {result.get('status', 'unknown')}")
        click.echo(f"Items Processed: {result.get('items_processed', 0)}")
        
        if result.get('errors'):
            click.echo(f"\nErrors:")
            for error in result['errors']:
                click.echo(f"  - {error}")
        
        if result.get('publication_result'):
            pub_result = result['publication_result']
            click.echo(f"\nPublication:")
            click.echo(f"  Success: {pub_result.get('success', False)}")
            if pub_result.get('post_url'):
                click.echo(f"  URL: {pub_result['post_url']}")
                
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", extra={"agent": "CLI"})
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def respond_comments(ctx):
    """Manually trigger the comment responder agent."""
    from src.agents.comment_responder import CommentResponderAgent
    
    config = get_config()
    logger.info("Manually triggering comment responder", extra={"agent": "CLI"})
    
    async def run_responder():
        agent = CommentResponderAgent(config=config)
        await agent.initialize()
        results = await agent.run()
        await agent.close()
        return results

    try:
        results = asyncio.run(run_responder())
        click.echo(f"\nComment Responder Results:")
        click.echo(f"Total actions: {len(results)}")
        
        success_count = sum(1 for r in results if r.success)
        click.echo(f"Successes: {success_count}")
        click.echo(f"Failures: {len(results) - success_count}")
        
        for r in results:
            if not r.success:
                click.echo(f"  - Error in comment {r.comment_id}: {r.error}")
            else:
                click.echo(f"  - Replied to {r.comment_id} (Reply ID: {r.reply_id})")
                
    except Exception as e:
        logger.error(f"Comment responder failed: {e}", extra={"agent": "CLI"})
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx):
    """Check the health of the API server."""
    import httpx
    
    config = get_config()
    url = f"http://{config.api_host}:{config.api_port}/health"
    
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        
        health_data = response.json()
        click.echo("API server is healthy")
        click.echo(f"Status: {health_data.get('status')}")
        click.echo(f"Version: {health_data.get('version')}")
        click.echo(f"Timestamp: {health_data.get('timestamp')}")
        
    except Exception as e:
        click.echo(f"API server is not reachable: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
