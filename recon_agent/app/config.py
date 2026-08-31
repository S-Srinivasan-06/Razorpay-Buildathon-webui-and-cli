"""Configuration and environment management for the reconciliation engine.

Provides filesystem path resolution, automatic directory initialization,
and lightweight .env parsing without third-party dotenv dependencies.
"""

import os
from pathlib import Path

# Base project directories resolved relative to this module
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
LOGS_DIR = DATA_DIR / "logs"
AUDIT_DIR = DATA_DIR / "audit"

# Ensure all working directories exist upon module import
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
AUDIT_DIR.mkdir(exist_ok=True)


def _load_env_file() -> None:
    """Load environment variables from a local recon_agent/.env file if present.
    
    Parses key=value pairs while ignoring comments and empty lines. Does not
    overwrite existing environment variables already present in os.environ.
    """
    env_path = BASE_DIR / ".env"
    if env_path.is_file():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            # Silently handle unreadable or malformed .env files
            pass


# Automatically load local .env definitions on startup
_load_env_file()

# Default LLM API key lookup prioritizing standard LLM / Gemini variable names
DEFAULT_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY", "")

