"""Tool Dispatcher with Circuit Breakers, Cost Control, and Deterministic Fallbacks.

Manages execution of external LLM tool calls. Implements safety circuit breakers,
cost budget enforcement, retry loops with latency/cost telemetry, and fallback
execution when LLM endpoints are unavailable or budget limits are reached.
"""

import time
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, ValidationError

from app.core import llm_client
from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import MessageKind, ToolCall
from app.core.cost import tracker_for

# Circuit breaker failure counters keyed by (session_id, tool_name)
_breakers: Dict[Tuple[str, str], int] = {}


def breaker_open(sid: str, tool: str) -> bool:
    """Check if the circuit breaker is tripped open for a specific session and tool.
    
    Args:
        sid: Session identifier string.
        tool: Name of the tool.
        
    Returns:
        True if failure count has reached the threshold, False otherwise.
    """
    return _breakers.get((sid, tool), 0) >= REG["circuit_breaker_failure_count"]


def cleanup_breakers(sid: Optional[str] = None) -> None:
    """Evict breaker entries for a specific session or prune old entries if size exceeds limit."""
    global _breakers
    if sid:
        _breakers = {k: v for k, v in _breakers.items() if k[0] != sid}
    elif len(_breakers) > 1000:
        keys = list(_breakers.keys())[-500:]
        _breakers = {k: _breakers[k] for k in keys}


def _count_failure(sid: str, tool: str) -> None:
    """Increment failure counter and emit a CIRCUIT_BREAKER_OPEN event if threshold is hit.
    
    Args:
        sid: Session identifier string.
        tool: Name of the tool that encountered a failure.
    """
    if len(_breakers) > 1000:
        cleanup_breakers()
    k = (sid, tool)
    _breakers[k] = _breakers.get(k, 0) + 1
    if _breakers[k] == REG["circuit_breaker_failure_count"]:
        validate_and_route(
            sid,
            MessageKind.CONTROL,
            {
                "event": "CIRCUIT_BREAKER_OPEN",
                "detail": {"tool": tool, "session": sid},
            },
            "system",
        )


def reset_breaker(sid: str, tool: str) -> None:
    """Reset the failure counter for a specific session and tool.
    
    Args:
        sid: Session identifier string.
        tool: Name of the tool.
    """
    _breakers[(sid, tool)] = 0


def dispatch_tool_call(
    sid: str,
    tool: ToolCall,
    args: Dict[str, Any],
) -> Tuple[Any, Optional[str]]:
    """Safely dispatch an LLM tool call with budget checking, retries, and fallback.
    
    Workflow:
      1. Validate input args against `tool.args_schema`. If invalid, execute fallback.
      2. Check if circuit breaker is open. If open, immediately return fallback.
      3. Check cost budget with CostTracker. If exceeded, return fallback.
      4. Execute LLM call with retry loop up to `tool.retries`.
      5. On success: record token cost, reset circuit breaker, and emit trace telemetry.
      6. On repeated failure: increment circuit breaker and execute deterministic fallback.
      
    Args:
        sid: Session identifier string.
        tool: ToolCall specification defining schemas, timeouts, and fallback.
        args: Input argument dictionary.
        
    Returns:
        Tuple of (result_or_fallback_output, fallback_used_flag_or_name).
    """
    # 1. Validate argument schema
    try:
        validated = tool.args_schema.model_validate(args)
    except ValidationError as e:
        validate_and_route(
            sid,
            MessageKind.TRACE,
            {
                "event": f"args_rejected:{tool.name}",
                "detail": {"err": str(e)[:200]},
            },
            "system",
        )
        return tool.fallback(args), tool.name

    # 2. Check circuit breaker state
    if breaker_open(sid, tool.name):
        return tool.fallback(args), tool.name

    # 3. Authorize cost budget
    if not tracker_for(sid).authorize(tool.cost_budget_usd):
        validate_and_route(
            sid,
            MessageKind.CONTROL,
            {"event": "BUDGET_EXCEEDED", "detail": {"tool": tool.name}},
            "system",
        )
        return tool.fallback(args), tool.name

    # 4. Execute tool call with retries
    err = None
    for _ in range(tool.retries + 1):
        t0 = time.time()
        try:
            raw = llm_client.json_chat(
                tool.name,
                validated.model_dump(),
                timeout=tool.timeout_s,
            )
            result = tool.result_schema.model_validate(raw)
            usd = llm_client.last_cost_usd()
            est = llm_client.last_estimated()
            tracker_for(sid).record(usd, estimated=est)

            if usd > tool.cost_budget_usd:
                validate_and_route(
                    sid,
                    MessageKind.TRACE,
                    {"event": f"cost_overrun:{tool.name}", "detail": {"usd": usd}},
                    "system",
                )

            # Reset breaker on successful response
            _breakers[(sid, tool.name)] = 0
            validate_and_route(
                sid,
                MessageKind.TRACE,
                {
                    "event": f"tool_ok:{tool.name}",
                    "detail": {
                        "s": round(time.time() - t0, 2),
                        "usd": round(usd, 6),
                        "estimated": est,
                    },
                },
                "llm",
            )
            return result, None
        except Exception as e:
            err = e
            _count_failure(sid, tool.name)
            # On network timeout or unreachable endpoint, break immediately to avoid compounding latency
            if isinstance(e, (TimeoutError, OSError)):
                break

    # 5. All retries failed — invoke deterministic fallback
    validate_and_route(
        sid,
        MessageKind.TRACE,
        {"event": f"llm_fallback:{tool.name}:{type(err).__name__}"},
        "system",
    )
    return tool.fallback(args), tool.name

