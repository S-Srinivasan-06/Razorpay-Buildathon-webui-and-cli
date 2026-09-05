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

# Runtime data directory (logs, audit trails, uploads, outputs) outside src
DATA_DIR = Path(os.getenv("RECON_DATA_DIR", PROJECT_ROOT / "data"))
UPLOAD_DIR = Path(os.getenv("RECON_UPLOAD_DIR", DATA_DIR / "uploads"))
LOGS_DIR = Path(os.getenv("RECON_LOGS_DIR", DATA_DIR / "logs"))
AUDIT_DIR = Path(os.getenv("RECON_AUDIT_DIR", DATA_DIR / "audit"))
OUTPUT_DIR = Path(os.getenv("RECON_OUTPUT_DIR", DATA_DIR / "outputs"))

# Sample datasets located at root-level datasets/ outside src
ASSETS_DIR = Path(
    os.getenv(
        "RECON_ASSETS_DIR",
        PROJECT_ROOT / "datasets"
        if (PROJECT_ROOT / "datasets").exists()
        else BASE_DIR / "sample_data",
    )
)

# Static frontend assets strictly located in src/app/static
STATIC_DIR = Path(
    os.getenv(
        "RECON_STATIC_DIR",
        APP_DIR / "static",
    )
)

# Ensure all working runtime directories exist upon module import
for _directory in (DATA_DIR, UPLOAD_DIR, LOGS_DIR, AUDIT_DIR, OUTPUT_DIR):
    try:
        os.makedirs(str(_directory), exist_ok=True)
    except OSError:
        pass


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
                        k, v = k.strip(), v.strip()
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass
            break


# Load environment variables into os.environ on startup
_load_env_file()
