from pydantic import ValidationError

from app.core.audit import audit_for
from app.core.contracts import MessageKind, SCHEMAS
from app.core.masking import apply_masking

_subscribers: dict[MessageKind, list] = {k: [] for k in MessageKind}


def subscribe(kind: MessageKind, fn):
    _subscribers[kind].append(fn)


def validate_and_route(session_id: str, kind: MessageKind, payload: dict, source: str):
    try:
        model = SCHEMAS[kind].model_validate(payload)
    except ValidationError as e:
        audit_for(session_id).append({
            "event": "CONTRACT_VIOLATION", "session": session_id,
            "kind": kind.value, "source": source, "err": str(e)[:200]})
        return None
    if kind == MessageKind.ARTIFACT:
        model = apply_masking(model)
    for fn in _subscribers[kind]:
        fn(session_id, model, source)
    return model
