import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

AUDIT_DIR = Path(os.getenv("RECON_AUDIT_DIR", "data/audit"))


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.records = []
        self._prev = "GENESIS"
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                r = json.loads(line)
                self.records.append(r)
                self._prev = r["this_hash"]
        self._fh = open(self.path, "a", encoding="utf-8")

    def append(self, payload: dict):
        with self._lock:
            seq = len(self.records)
            canon = json.dumps({"seq": seq, "payload": payload, "prev": self._prev},
                               sort_keys=True, default=str)
            h = hashlib.sha256(canon.encode()).hexdigest()
            rec = {"seq": seq, "ts": datetime.now(timezone.utc).isoformat(),
                   "payload": payload, "prev_hash": self._prev, "this_hash": h}
            self._fh.write(json.dumps(rec, default=str) + "\n")
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self.records.append(rec)
            self._prev = h

    def verify(self) -> bool:
        prev = "GENESIS"
        for line in self.path.read_text().splitlines():
            r = json.loads(line)
            canon = json.dumps({"seq": r["seq"], "payload": r["payload"], "prev": prev},
                               sort_keys=True, default=str)
            if r["prev_hash"] != prev or hashlib.sha256(canon.encode()).hexdigest() != r["this_hash"]:
                return False
            prev = r["this_hash"]
        return True


_LOGS: dict[str, AuditLog] = {}
_LOGS_LOCK = threading.Lock()


def audit_for(session_id: str) -> AuditLog:
    with _LOGS_LOCK:
        if session_id not in _LOGS:
            from app import config
            audit_dir = getattr(config, "AUDIT_DIR", AUDIT_DIR)
            _LOGS[session_id] = AuditLog(audit_dir / f"{session_id}.audit.jsonl")
        return _LOGS[session_id]
