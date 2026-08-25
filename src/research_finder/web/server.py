from __future__ import annotations

import argparse
import sys
import webbrowser
from threading import Timer

import uvicorn


async def run_server_async(
    host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True
) -> None:
    url = f"http://{host}:{port}"
    print(f"\n🚀 Research Prospect Finder Web UI is starting at {url}\n")

    if open_browser:
        def _open():
            try:
                webbrowser.open(url)
            except Exception:
                pass
        Timer(1.0, _open).start()

    from research_finder.web.app import app
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def run_server(
    host: str = "127.0.0.1", port: int = 8000, reload: bool = False, open_browser: bool = True
) -> None:
    import asyncio
    asyncio.run(run_server_async(host=host, port=port, open_browser=open_browser))


def main() -> None:
    parser = argparse.ArgumentParser(description="Start Research Prospect Finder Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()
    try:
        run_server(host=args.host, port=args.port, reload=args.reload, open_browser=not args.no_browser)
    except KeyboardInterrupt:
        print("\n👋 Web server stopped. Goodbye!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
