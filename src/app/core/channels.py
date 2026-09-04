"""Event Distribution Bus and Schema Validation Routing.

Provides a pub/sub event distribution mechanism across message kinds (CHAT,
ARTIFACT, TRACE, CONTROL). Validates incoming payloads against Pydantic contracts,
intercepts and masks PII on ARTIFACT payloads, and logs contract violations.
"""

from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, ValidationError

from app.core.audit import audit_for
from app.core.contracts import MessageKind, SCHEMAS
from app.core.masking import apply_masking

# Registry of subscriber callbacks grouped by MessageKind
_subscribers: Dict[MessageKind, List[Callable[[str, BaseModel, str], None]]] = {
    k: [] for k in MessageKind
}


def subscribe(kind: MessageKind, fn: Callable[[str, BaseModel, str], None]) -> None:
    """Register a subscriber callback for a specific message kind.
    
    Args:
        kind: The MessageKind category to listen for.
        fn: Callback taking (session_id, validated_model, source).
    """
    _subscribers[kind].append(fn)


def validate_and_route(
    session_id: str,
    kind: MessageKind,
    payload: Dict[str, Any],
    source: str,
) -> Optional[BaseModel]:
    """Validate a payload against its schema and route to all registered subscribers.
    
    If validation fails, records a CONTRACT_VIOLATION event in the session audit log
    and returns None. If valid, applies PII masking on ARTIFACT payloads before
    broadcasting to subscribers.
    
    Args:
        session_id: Unique session identifier.
        kind: MessageKind classification of the event.
        payload: Raw dictionary data matching the schema for `kind`.
        source: Originator identifier (e.g. 'system', 'engine', 'llm', 'user').
        
    Returns:
        The validated Pydantic model instance, or None if validation failed.
    """
    try:
        model = SCHEMAS[kind].model_validate(payload)
    except ValidationError as e:
        # Audit contract violations without crashing the executing pipeline
        audit_for(session_id).append({
            "event": "CONTRACT_VIOLATION",
            "session": session_id,
            "kind": kind.value,
            "source": source,
            "err": str(e)[:200],
        })
        return None

    # Intercept artifact payloads to automatically redact sensitive PII
    if kind == MessageKind.ARTIFACT:
        model = apply_masking(model)

    # Deliver validated message to all registered listeners
    for fn in _subscribers[kind]:
        fn(session_id, model, source)

    return model

