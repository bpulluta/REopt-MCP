"""Runtime configuration for REopt MCP."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root, regardless of CWD.
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

REOPT_API_BASE_URL: str = (
    os.getenv("REOPT_API_BASE_URL", "").strip()
    or "https://developer.nlr.gov/api/reopt/stable"
)

NLR_API_KEY: str = os.getenv("NLR_API_KEY", "").strip()


def warn_if_unconfigured() -> None:
    """Print a startup warning when the API key is missing."""
    if not NLR_API_KEY:
        print("Warning: NLR_API_KEY is not set.", flush=True)
