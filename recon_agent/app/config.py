import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
LOGS_DIR = DATA_DIR / "logs"
AUDIT_DIR = DATA_DIR / "audit"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
AUDIT_DIR.mkdir(exist_ok=True)


def _load_env_file():
    """Load environment variables from single recon_agent/.env file if present."""
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
            pass


_load_env_file()

DEFAULT_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY", "")
