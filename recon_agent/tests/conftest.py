import os
import shutil
import tempfile
import pytest
from pathlib import Path


@pytest.fixture(autouse=True, scope="session")
def isolate_test_environment():
    """Ensure tests write temporary logs and audit files to a temporary directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="recon_test_"))
    test_audit = temp_dir / "audit"
    test_logs = temp_dir / "logs"
    test_uploads = temp_dir / "uploads"
    test_audit.mkdir(parents=True, exist_ok=True)
    test_logs.mkdir(parents=True, exist_ok=True)
    test_uploads.mkdir(parents=True, exist_ok=True)

    old_audit = os.environ.get("RECON_AUDIT_DIR")
    old_logs = os.environ.get("RECON_LOGS_DIR")
    os.environ["RECON_AUDIT_DIR"] = str(test_audit)
    os.environ["RECON_LOGS_DIR"] = str(test_logs)

    # Import modules to patch directories
    from app.core import audit
    from app import config
    audit.AUDIT_DIR = test_audit
    config.AUDIT_DIR = test_audit
    config.LOGS_DIR = test_logs
    config.UPLOAD_DIR = test_uploads

    yield

    # Cleanup after test session
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    if old_audit is not None:
        os.environ["RECON_AUDIT_DIR"] = old_audit
    else:
        os.environ.pop("RECON_AUDIT_DIR", None)
    if old_logs is not None:
        os.environ["RECON_LOGS_DIR"] = old_logs
    else:
        os.environ.pop("RECON_LOGS_DIR", None)
