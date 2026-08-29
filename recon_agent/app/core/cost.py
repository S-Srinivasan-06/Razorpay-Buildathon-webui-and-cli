import threading

from app.core.constants import REG


class CostTracker:
    def __init__(self, cap_usd: float):
        self.cap = cap_usd
        self.total = 0.0
        self.estimated_any = False
        self._lock = threading.Lock()

    def authorize(self, budget_usd: float) -> bool:
        with self._lock:
            return self.total + budget_usd <= self.cap

    def record(self, usd: float, estimated: bool = False):
        with self._lock:
            self.total += usd
            self.estimated_any = self.estimated_any or estimated


_TRACKERS: dict[str, CostTracker] = {}


def tracker_for(session_id: str) -> CostTracker:
    if session_id not in _TRACKERS:
        _TRACKERS[session_id] = CostTracker(REG["session_cost_cap_usd"])
    return _TRACKERS[session_id]
