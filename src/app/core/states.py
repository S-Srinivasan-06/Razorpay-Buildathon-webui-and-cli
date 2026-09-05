"""Finite State Machine and Pipeline Execution Lifecycle.

Provides the State enum and StateMachine class that coordinate all state
transitions, abort tokens, circuit breaker halts, and safe interactive resumption.
Emits CONTROL events via the central channel dispatcher.
"""

import secrets
import uuid
from enum import Enum
from typing import Dict, List, Optional, Set

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


VALID_TRANSITIONS: Dict[State, Set[State]] = {
    State.INGESTING: {State.PROFILING, State.HALT, State.ABORT_CONFIRMED},
    State.PROFILING: {State.MAPPING_PROPOSED, State.HALT, State.ABORT_CONFIRMED},
    State.MAPPING_PROPOSED: {State.MAPPING_VALIDATED, State.POLICY_GENERATED, State.HALT, State.ABORT_CONFIRMED},
    State.MAPPING_VALIDATED: {State.POLICY_GENERATED, State.DRY_RUN, State.HALT, State.ABORT_CONFIRMED},
    State.POLICY_GENERATED: {State.DRY_RUN, State.EXECUTING, State.HALT, State.ABORT_CONFIRMED},
    State.DRY_RUN: {State.EXECUTING, State.HALT, State.ABORT_CONFIRMED},
    State.EXECUTING: {State.INSPECTING, State.HALT, State.ABORT_CONFIRMED},
    State.INSPECTING: {State.EXECUTING, State.REVISION, State.QA, State.HALT, State.ABORT_CONFIRMED},
    State.REVISION: {State.EXECUTING, State.INSPECTING, State.QA, State.HALT, State.ABORT_CONFIRMED},
    State.QA: {State.RESOLVING, State.HALT, State.ABORT_CONFIRMED},
    State.RESOLVING: {State.AGGREGATING, State.ARCHIVED, State.HALT, State.ABORT_CONFIRMED},
    State.AGGREGATING: {State.ARCHIVED, State.HALT, State.ABORT_CONFIRMED},
    State.HALT: set(State),
    State.ARCHIVED: set(),
    State.ABORT_CONFIRMED: set(),
}


class StateMachine:
    """Deterministic finite state machine managing reconciliation execution flow."""

    def __init__(self, sid: str) -> None:
        """Initialize state machine for a reconciliation session."""
        self.sid: str = sid
        self.state: Optional[State] = None
        self._token: str = secrets.token_hex(4)
        self._pre_halt: Optional[State] = None
        self._halt_tools: List[str] = []
        self._abort_pending: bool = False

    @property
    def token(self) -> str:
        """Active abort authorization token."""
        return self._token

    def enter(self, state: State, detail: str = "") -> None:
        """Forcefully enter a state without lifecycle validation checks."""
        self.state = state
        self._token = secrets.token_hex(4)
        detail_dict = {"info": str(detail)} if isinstance(detail, str) else (detail or {})
        validate_and_route(
            self.sid,
            MessageKind.CONTROL,
            {
                "event": "STATE_ENTERED",
                "state": state.value,
                "abort_token": self._token,
                "detail": detail_dict,
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
        """Transition from current state to a target state with transition validation.
        
        Checks if an abort was requested before transitioning. If aborted,
        transitions immediately to ABORT_CONFIRMED and returns False.
        
        Args:
            to: Destination state.
            detail: Contextual note or metrics for the transition.
            
        Returns:
            True if transition succeeded, False if aborted.
            
        Raises:
            ValueError: If attempting an illegal lifecycle transition.
        """
        if self._abort_pending:
            self._abort_pending = False
            self.enter(State.ABORT_CONFIRMED)
            return False

        if self.state is not None and self.state in VALID_TRANSITIONS:
            allowed = VALID_TRANSITIONS[self.state]
            if to not in allowed and to not in (State.ABORT_CONFIRMED, State.HALT):
                raise ValueError(
                    f"Illegal state transition from {self.state.value} to {to.value}."
                )

        if self.state is not None:
            validate_and_route(
                self.sid,
                MessageKind.CONTROL,
                {
                    "event": "STATE_EXITED",
                    "state": self.state.value,
                    "abort_token": self._token,
                    "detail": {},
                },
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

