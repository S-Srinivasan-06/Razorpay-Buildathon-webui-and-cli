import time

from pydantic import ValidationError

from app.core import llm_client
from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import MessageKind, ToolCall
from app.core.cost import tracker_for

_breakers: dict[tuple[str, str], int] = {}


def breaker_open(sid: str, tool: str) -> bool:
    return _breakers.get((sid, tool), 0) >= REG["circuit_breaker_failure_count"]


def _count_failure(sid: str, tool: str):
    k = (sid, tool)
    _breakers[k] = _breakers.get(k, 0) + 1
    if _breakers[k] == REG["circuit_breaker_failure_count"]:
        validate_and_route(sid, MessageKind.CONTROL,
                           {"event": "CIRCUIT_BREAKER_OPEN",
                            "detail": {"tool": tool, "session": sid}}, "system")


def reset_breaker(sid: str, tool: str):
    _breakers[(sid, tool)] = 0


def dispatch_tool_call(sid: str, tool: ToolCall, args: dict):
    try:
        validated = tool.args_schema.model_validate(args)
    except ValidationError as e:
        validate_and_route(sid, MessageKind.TRACE,
                           {"event": f"args_rejected:{tool.name}",
                            "detail": {"err": str(e)[:200]}}, "system")
        return tool.fallback(args), tool.name
    if breaker_open(sid, tool.name):
        return tool.fallback(args), tool.name
    if not tracker_for(sid).authorize(tool.cost_budget_usd):
        validate_and_route(sid, MessageKind.CONTROL,
                           {"event": "BUDGET_EXCEEDED",
                            "detail": {"tool": tool.name}}, "system")
        return tool.fallback(args), tool.name
    err = None
    for _ in range(tool.retries + 1):
        t0 = time.time()
        try:
            raw = llm_client.json_chat(tool.name, validated.model_dump(),
                                       timeout=tool.timeout_s)
            result = tool.result_schema.model_validate(raw)
            usd = llm_client.last_cost_usd()
            est = llm_client.last_estimated()
            tracker_for(sid).record(usd, estimated=est)
            if usd > tool.cost_budget_usd:
                validate_and_route(sid, MessageKind.TRACE,
                                   {"event": f"cost_overrun:{tool.name}",
                                    "detail": {"usd": usd}}, "system")
            _breakers[(sid, tool.name)] = 0
            validate_and_route(sid, MessageKind.TRACE,
                               {"event": f"tool_ok:{tool.name}",
                                "detail": {"s": round(time.time() - t0, 2),
                                           "usd": round(usd, 6), "estimated": est}}, "llm")
            return result, None
        except Exception as e:
            err = e
            _count_failure(sid, tool.name)
    validate_and_route(sid, MessageKind.TRACE,
                       {"event": f"llm_fallback:{tool.name}:{type(err).__name__}"}, "system")
    return tool.fallback(args), tool.name
