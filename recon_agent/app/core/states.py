"""Finite State Machine and Pipeline Execution Lifecycle.

Provides the State enum and StateMachine class that coordinate all state
transitions, abort tokens, circuit breaker halts, and safe interactive resumption.
Emits CONTROL events via the central channel dispatcher.
"""

import uuid
from enum import Enum
from typing import List, Optional

from app.core.channels import validate_and_route
from app.core.contracts import MessageKind
from app.core.dispatcher import reset_breaker


class State(str, Enum):
    """Pipeline execution lifecycle states."""
    INGESTING = "INGESTING"
    PROFILING = "PROFILING"
    MAPPING_PROPOSED = "MAPPING_PROPOSED"
    MAPPING_VALIDATED = "MAPPING_VALIDATED"
    POLICY_GENERATED = "POLICY_GENERATED"
    DRY_RUN = "DRY_RUN"
    EXECUTING = "EXECUTING"
    INSPECTING = "INSPECTING"
    REVISION = "REVISION"
    QA = "QA"
    RESOLVING = "RESOLVING"
    AGGREGATING = "AGGREGATING"
    ARCHIVED = "ARCHIVED"
    HALT = "HALT"
    ABORT_CONFIRMED = "ABORT_CONFIRMED"


class StateMachine:
    """Deterministic finite state machine managing reconciliation execution flow.
    
    Coordinates sequential execution steps, handles voluntary and error halts,
    maintains abort tokens for cancellation, and supports reentry upon resumption.
    """

    def __init__(self, session_id: str) -> None:
        """Initialize state machine for a specific session.
        
        Args:
            session_id: Unique session identifier string.
        """
        self.sid: str = session_id
        self.state: Optional[State] = None
        self._token: Optional[str] = None
        self._abort_pending: bool = False
        self._pre_halt: Optional[State] = None
        self._halt_tools: List[str] = []

    def enter(self, s: State, detail: str = "") -> None:
        """Enter a new state and emit a STATE_ENTERED control event.
        
        Generates a fresh abort token for the new state.
        
        Args:
            s: Target state to enter.
            detail: Contextual note or reason for entering the state.
        """
        self.state = s
        self._token = uuid.uuid4().hex
        validate_and_route(
            self.sid,
            MessageKind.CONTROL,
            {
                "event": "STATE_ENTERED",
                "state": s.value,
                "abort_token": self._token,
                "detail": {"d": detail},
            },
            "system",
        )

    def request_abort(self, token: str) -> None:
        """Request pipeline abort if the supplied token matches the active state token.
        
        Args:
            token: Abort authorization token.
        """
        if token == self._token:
            self._abort_pending = True

    def transition(self, to: State, detail: str = "") -> bool:
        """Transition from current state to a target state.
        
        Checks if an abort was requested before transitioning. If aborted,
        transitions immediately to ABORT_CONFIRMED and returns False.
        
        Args:
            to: Destination state.
            detail: Contextual note or metrics for the transition.
            
        Returns:
            True if transition succeeded, False if aborted.
        """
        if self._abort_pending:
            self._abort_pending = False
            self.enter(State.ABORT_CONFIRMED)
            return False

        if self.state is not None:
            validate_and_route(
                self.sid,
                MessageKind.CONTROL,
                {"event": "STATE_EXITED", "state": self.state.value},
                "system",
            )
        self.enter(to, detail)
        return True

    def halt(self, reason: str, tools: Optional[List[str]] = None) -> None:
        """Pause pipeline execution due to a policy condition or circuit breaker trip.
        
        Saves current state in `_pre_halt` so execution can safely resume
        or re-verify without skipping gates.
        
        Args:
            reason: Human-readable diagnostic reason for the halt.
            tools: Optional list of tripped tool names requiring breaker resets.
        """
        self._pre_halt = self.state
        self._halt_tools = tools or []
        validate_and_route(
            self.sid,
            MessageKind.CONTROL,
            {
                "event": "HALT",
                "detail": {"reason": reason, "tools": self._halt_tools},
            },
            "system",
        )
        self.enter(State.HALT, reason)

    def resume(self) -> None:
        """Resume execution from a HALT state.
        
        Resets tripped circuit breakers and re-enters the pre-halt state
        to safely re-evaluate pipeline gates.
        """
        for t in self._halt_tools:
            reset_breaker(self.sid, t)
        validate_and_route(
            self.sid,
            MessageKind.CONTROL,
            {"event": "RESUMED", "detail": {"tools": self._halt_tools}},
            "user",
        )
        target = self._pre_halt or State.INGESTING
        self._halt_tools = []
        self.enter(target, "resumed")

