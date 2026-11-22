"""
Direct CLI entrypoint for running instahyre_mcp server.
"""
import os
import argparse
from instahyre_mcp.server import run_server


def main():
    parser = argparse.ArgumentParser(description="instahyre-mcp: Model Context Protocol Server for Instahyre")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=os.getenv("MCP_TRANSPORT", "sse"),
        help="Transport mode (default: sse or MCP_TRANSPORT env)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 8000)),
        help="Port for HTTP/SSE mode (default: PORT env or 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP/SSE mode"
    )
    args = parser.parse_args()
    run_server(transport=args.transport, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
