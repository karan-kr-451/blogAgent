"""
Start the API server with correct Windows event loop policy.
Usage: python start_server.py
"""
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
    print(f"Event Loop Policy: {asyncio.get_event_loop_policy().__class__.__name__}")
    print("=" * 70)
    print()
    
    uvicorn.run(
        "src.api.server:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )

if __name__ == "__main__":
    main()
