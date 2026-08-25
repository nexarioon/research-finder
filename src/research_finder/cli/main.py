from __future__ import annotations

import argparse
import sys

from research_finder.web.server import run_server

APP_NAME = "Research Prospect Finder"
APP_VERSION = "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research-finder",
        description=f"{APP_NAME} v{APP_VERSION} - Web Application for finding and analyzing research prospects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    # Optional 'web' subcommand for backward compatibility
    sub = parser.add_subparsers(dest="command", help="Optional command")
    web_parser = sub.add_parser("web", help="Start the Web UI interface")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    web_parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    web_parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    host = getattr(args, "host", "127.0.0.1")
    port = getattr(args, "port", 8000)
    no_browser = getattr(args, "no_browser", False)
    reload_flag = getattr(args, "reload", False)

    try:
        run_server(host=host, port=port, reload=reload_flag, open_browser=not no_browser)
    except KeyboardInterrupt:
        print("\n👋 Research Finder stopped. Goodbye!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
