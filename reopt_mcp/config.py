"""Runtime configuration for REopt MCP."""

import os
from dotenv import load_dotenv

load_dotenv()

NREL_API_KEY = os.getenv("NREL_API_KEY", "")
REOPT_API_BASE_URL = os.getenv(
    "REOPT_API_BASE_URL", "https://developer.nrel.gov/api/reopt/stable"
)


def warn_if_unconfigured() -> None:
    if not NREL_API_KEY:
        print(
            "Warning: NREL_API_KEY not set. Please configure your .env file.",
            flush=True,
        )
