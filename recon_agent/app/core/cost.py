"""LLM Cost Metering and Budget Enforcement.

Tracks cumulative LLM expenditure per session, enforces maximum budget caps
(e.g., $1.00 USD per session cap), and flags whether token counts were derived
from exact API usage metadata or estimated from prompt/response lengths.
"""

import threading
from typing import Dict

from app.core.constants import REG


class CostTracker:
    """Thread-safe cumulative cost tracker and budget authorizer for a session.
    
    Attributes:
        cap: Maximum authorized USD budget cap for the session.
        total: Cumulative USD spend incurred by tool and chat invocations.
        estimated_any: Boolean flag indicating if any cost calculation was estimated.
    """

    def __init__(self, cap_usd: float) -> None:
        """Initialize tracker with a strict USD budget cap.
        
        Args:
            cap_usd: Maximum allowable expenditure in USD.
        """
        self.cap: float = cap_usd
        self.total: float = 0.0
        self.estimated_any: bool = False
        self._lock: threading.Lock = threading.Lock()

    def authorize(self, budget_usd: float) -> bool:
        """Check whether an upcoming call with the given budget is authorized.
        
        Args:
            budget_usd: Estimated cost of the prospective call in USD.
            
        Returns:
            True if (total + budget_usd) <= cap, False otherwise.
        """
        with self._lock:
            return self.total + budget_usd <= self.cap

    def record(self, usd: float, estimated: bool = False) -> None:
        """Record the actual incurred cost of a completed LLM invocation.
        
        Args:
            usd: Cost in USD to add to the cumulative total.
            estimated: True if token counts were estimated rather than reported by API.
        """
        with self._lock:
            self.total += usd
            self.estimated_any = self.estimated_any or estimated


# Per-session CostTracker instance registry
_TRACKERS: Dict[str, CostTracker] = {}


def tracker_for(session_id: str) -> CostTracker:
    """Retrieve or lazily initialize the CostTracker for a specific session.
    
    Args:
        session_id: Unique session identifier string.
        
    Returns:
        CostTracker instance configured with the registry's session_cost_cap_usd.
    """
    if session_id not in _TRACKERS:
        _TRACKERS[session_id] = CostTracker(REG["session_cost_cap_usd"])
    return _TRACKERS[session_id]

