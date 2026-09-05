"""Pytest Test Suite Configuration and Global Fixtures.

Provides session-scoped test environment isolation, redirecting audit ledgers,
logs, uploaded datasets, and generated outputs to a temporary directory so unit
and integration tests do not pollute production or local development workspace folders.
"""

import os
from pathlib import Path
import shutil
import sys
import tempfile

import pytest

# Ensure src/ is in sys.path for test discovery
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Initialize an isolated temporary directory IMMEDIATELY at conftest import time
# before any application modules (config, api_v2, etc.) evaluate their module-level paths.
_TEST_TEMP_DIR = Path(tempfile.mkdtemp(prefix="recon_test_workspace_"))
_TEST_DATA = _TEST_TEMP_DIR / "data"
_TEST_AUDIT = _TEST_DATA / "audit"
_TEST_LOGS = _TEST_DATA / "logs"
_TEST_UPLOADS = _TEST_DATA / "uploads"
_TEST_OUTPUTS = _TEST_DATA / "outputs"

for _p in (_TEST_AUDIT, _TEST_LOGS, _TEST_UPLOADS, _TEST_OUTPUTS):
    _p.mkdir(parents=True, exist_ok=True)

# Set environment variables so app.config loads these upon initial import
os.environ["RECON_DATA_DIR"] = str(_TEST_DATA)
os.environ["RECON_AUDIT_DIR"] = str(_TEST_AUDIT)
os.environ["RECON_LOGS_DIR"] = str(_TEST_LOGS)
os.environ["RECON_UPLOAD_DIR"] = str(_TEST_UPLOADS)
os.environ["RECON_OUTPUT_DIR"] = str(_TEST_OUTPUTS)


@pytest.fixture(autouse=True, scope="session")
def isolate_test_environment() -> None:
    """Ensure all test runs write temporary logs and audit files to an isolated temp directory."""
    # Import modules and ensure all references point to isolated directory
    from app import config
    from app.core import audit

    audit.AUDIT_DIR = _TEST_AUDIT
    config.DATA_DIR = _TEST_DATA
    config.AUDIT_DIR = _TEST_AUDIT
    config.LOGS_DIR = _TEST_LOGS
    config.UPLOAD_DIR = _TEST_UPLOADS
    config.OUTPUT_DIR = _TEST_OUTPUTS

    try:
        from app.server import api_v2
        api_v2.DATA_DIR = _TEST_DATA
        api_v2.UPLOAD_DIR = _TEST_UPLOADS
        api_v2.OUTPUT_DIR = _TEST_OUTPUTS
        api_v2.AUDIT_DIR = _TEST_AUDIT
        api_v2.LOGS_DIR = _TEST_LOGS
    except ImportError:
        pass

    yield

    # Cleanup temporary test directory completely after test session
    try:
        shutil.rmtree(_TEST_TEMP_DIR, ignore_errors=True)
    except Exception:
        pass
