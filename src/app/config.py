"""Configuration and environment management for the reconciliation engine.

Provides filesystem path resolution, automatic directory initialization,
and lightweight .env parsing without third-party dotenv dependencies.
"""

import os
from pathlib import Path

# Base project directories resolved relative to this module
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
PROJECT_ROOT = BASE_DIR.parent if (BASE_DIR.parent / "src").is_dir() else BASE_DIR

# Runtime data directory (logs, audit trails, uploads, outputs)
DATA_DIR = Path(os.getenv("RECON_DATA_DIR", PROJECT_ROOT / "data"))
UPLOAD_DIR = Path(os.getenv("RECON_UPLOAD_DIR", DATA_DIR / "uploads"))
LOGS_DIR = Path(os.getenv("RECON_LOGS_DIR", DATA_DIR / "logs"))
AUDIT_DIR = Path(os.getenv("RECON_AUDIT_DIR", DATA_DIR / "audit"))
OUTPUT_DIR = Path(os.getenv("RECON_OUTPUT_DIR", DATA_DIR / "outputs"))

# Static assets and sample datasets
ASSETS_DIR = Path(
    os.getenv(
        "RECON_ASSETS_DIR",
        BASE_DIR / "assets" / "sample_datasets"
        if (BASE_DIR / "assets" / "sample_datasets").exists()
        else BASE_DIR / "sample_data",
    )
)
STATIC_DIR = Path(
    os.getenv(
        "RECON_STATIC_DIR",
        BASE_DIR / "static" if (BASE_DIR / "static").exists() else APP_DIR / "static",
    )
)
CONSTANTS_FILE = Path(
    os.getenv("RECON_CONSTANTS_FILE", BASE_DIR / "constants_v0.yaml")
)

# Ensure all working directories exist upon module import
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_env_file() -> None:
    """Load environment variables from project root or local .env file if present.
    
    Parses key=value pairs while ignoring comments and empty lines. Does not
    overwrite existing environment variables already present in os.environ.
    """
    for env_path in [PROJECT_ROOT / ".env", BASE_DIR / ".env"]:
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

