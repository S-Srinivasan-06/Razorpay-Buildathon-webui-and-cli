import uuid
from enum import Enum

from app.core.channels import validate_and_route
from app.core.contracts import MessageKind
from app.core.dispatcher import reset_breaker


class State(str, Enum):
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
    def __init__(self, session_id: str):
        self.sid = session_id
        self.state = None
        self._token = None
        self._abort_pending = False
        self._pre_halt = None
        self._halt_tools: list[str] = []

    def enter(self, s: State, detail=""):
        self.state = s
        self._token = uuid.uuid4().hex
        validate_and_route(self.sid, MessageKind.CONTROL,
                           {"event": "STATE_ENTERED", "state": s.value,
                            "abort_token": self._token, "detail": {"d": detail}}, "system")

    def request_abort(self, token: str):
        if token == self._token:
            self._abort_pending = True

    def transition(self, to: State, detail="") -> bool:
        if self._abort_pending:
            self._abort_pending = False
            self.enter(State.ABORT_CONFIRMED)
            return False
        validate_and_route(self.sid, MessageKind.CONTROL,
                           {"event": "STATE_EXITED", "state": self.state.value}, "system")
        self.enter(to, detail)
        return True

    def halt(self, reason: str, tools: list[str] | None = None):
        self._pre_halt = self.state
        self._halt_tools = tools or []
        validate_and_route(self.sid, MessageKind.CONTROL,
                           {"event": "HALT",
                            "detail": {"reason": reason, "tools": self._halt_tools}}, "system")
        self.enter(State.HALT, reason)

    def resume(self):
        for t in self._halt_tools:
            reset_breaker(self.sid, t)
        validate_and_route(self.sid, MessageKind.CONTROL,
                           {"event": "RESUMED", "detail": {"tools": self._halt_tools}}, "user")
        target = self._pre_halt or State.INGESTING
        self._halt_tools = []
        self.enter(target, "resumed")
