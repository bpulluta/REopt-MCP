"""Main entry point for running the REopt MCP server as a module."""

import asyncio
from reopt_mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())
