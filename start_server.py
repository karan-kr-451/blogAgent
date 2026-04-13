import os
import sys

# MUST be before ANY imports that create event loops
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

def main():
    print("=" * 70)
    print("Starting Autonomous Blog Agent API Server")
    print("=" * 70)
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    if sys.platform == 'win32':
        import asyncio
        print(f"Event Loop Policy: {asyncio.get_event_loop_policy().__class__.__name__}")
    print("=" * 70)
    print()
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    # Host must be 0.0.0.0 for Render
    host = "0.0.0.0"
    
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        log_level="info",
    )

if __name__ == "__main__":
    main()
