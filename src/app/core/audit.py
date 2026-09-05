"""Cryptographic Audit Ledger with Tamper-Evident SHA-256 Hash Chain.

Provides durable, append-only audit logging for every state transition, LLM decision,
and user override. Each log entry incorporates the cryptographic hash of the previous
entry (starting from 'GENESIS'), ensuring mathematical tamper detection upon verification.
"""

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union

AUDIT_DIR = Path(os.getenv("RECON_AUDIT_DIR", "data/audit"))


class AuditLog:
    """Tamper-evident audit log backed by a JSONL file and SHA-256 hash chain.
    
    Each line in the log is a JSON object with:
      - `seq`: Monotonically increasing 0-based integer sequence index.
      - `ts`: ISO-8601 UTC timestamp string.
      - `payload`: The logged event or decision payload dictionary.
      - `prev_hash`: Hash of the previous entry ('GENESIS' for the 0th entry).
      - `this_hash`: SHA-256 hash of canonical JSON {"seq", "payload", "prev"}.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        """Initialize and open the audit log file, loading existing history if present.
        
        Args:
            path: Filesystem path to the .audit.jsonl file.
        """
        self.path: Path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock: threading.Lock = threading.Lock()
        self.records: List[Dict[str, Any]] = []
        self._prev: str = "GENESIS"

        # Reconstruct chain from disk if log file already exists
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    self.records.append(r)
                    self._prev = r["this_hash"]

        self._fh = open(self.path, "a", encoding="utf-8")

    def close(self) -> None:
        """Close the underlying file descriptor cleanly."""
        with self._lock:
            if getattr(self, "_fh", None) and not self._fh.closed:
                self._fh.close()

    def __enter__(self) -> "AuditLog":
        return self

    def __iter__(self):
        with self._lock:
            return iter(list(self.records))

    def __len__(self) -> int:
        with self._lock:
            return len(self.records)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def append(self, payload: Dict[str, Any]) -> None:
        """Append a new record to the audit chain with SHA-256 signing and disk fsync.
        
        Args:
            payload: Event or decision dictionary to record permanently.
        """
        with self._lock:
            seq = len(self.records)
            # Create canonical deterministic JSON representation for hashing
            canon = json.dumps(
                {"seq": seq, "payload": payload, "prev": self._prev},
                sort_keys=True,
                default=str,
            )
            h = hashlib.sha256(canon.encode("utf-8")).hexdigest()
            rec = {
                "seq": seq,
                "ts": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
                "prev_hash": self._prev,
                "this_hash": h,
            }
            self._fh.write(json.dumps(rec, default=str) + "\n")
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self.records.append(rec)
            self._prev = h

    def verify(self) -> bool:
        """Verify the cryptographic integrity of the entire audit chain from genesis.
        
        Reads the log file from disk and recalculates hashes for every entry.
        
        Returns:
            True if all hashes and chain links are strictly intact, False if tampered.
        """
        if not self.path.exists():
            return True
        prev = "GENESIS"
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            canon = json.dumps(
                {"seq": r["seq"], "payload": r["payload"], "prev": prev},
                sort_keys=True,
                default=str,
            )
            calculated_hash = hashlib.sha256(canon.encode("utf-8")).hexdigest()
            if r["prev_hash"] != prev or calculated_hash != r["this_hash"]:
                return False
            prev = r["this_hash"]
        return True


# Session-to-AuditLog registry with thread-safe access lock
_LOGS: Dict[str, AuditLog] = {}
_LOGS_LOCK = threading.Lock()


def audit_for(session_id: str) -> AuditLog:
    """Retrieve or lazily initialize the AuditLog instance for a given session.
    
    Args:
        session_id: Unique session identifier string.
        
    Returns:
        AuditLog instance writing to data/audit/{session_id}.audit.jsonl.
    """
    with _LOGS_LOCK:
        if session_id not in _LOGS:
            from app import config
            audit_dir = getattr(config, "AUDIT_DIR", AUDIT_DIR)
            _LOGS[session_id] = AuditLog(audit_dir / f"{session_id}.audit.jsonl")
        return _LOGS[session_id]

