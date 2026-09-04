"""Unit Tests for Cryptographic Audit Trail Durability and Tamper Detection.

Verifies:
  1. Audit entries persist across process restarts with intact SHA-256 chain verification.
  2. Any unauthorized modification to an intermediate log record invalidates downstream hashes.
"""

from pathlib import Path

from app.core.audit import AuditLog


def test_restart_and_tamper(tmp_path: Path) -> None:
    """Verify cryptographic audit trail persistence, reloadability, and tamper detection."""
    p = tmp_path / "s1.audit.jsonl"
    a = AuditLog(p)
    a.append({"event": "STATE_ENTERED", "state": "INGESTING"})
    a.append({"event": "tool_ok:x", "usd": 0.001})
    a.append({"event": "STATE_EXITED", "state": "INGESTING"})
    del a

    # Reload from disk and verify clean SHA-256 chain integrity
    b = AuditLog(p)
    assert len(b.records) == 3 and b.verify()

    # Tamper with an intermediate line on disk
    txt = p.read_text().splitlines()
    txt[1] = txt[1].replace("tool_ok:x", "tool_ok:EVIL")
    p.write_text("\n".join(txt) + "\n")

    # Verification must fail on tampered audit ledger
    assert not AuditLog(p).verify()

