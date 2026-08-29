import re

from app.core.constants import REG
from app.core.contracts import ArtifactPayload

_PAT = [(re.compile(r"[\w.+-]+@[\w-]+\.\w+"), 1.0),
        (re.compile(r"^\+?\d[\d\s-]{9,14}$"), 0.9),
        (re.compile(r"^[A-Z]{5}\d{4}[A-Z]$"), 0.8),
        (re.compile(r"^\d{12}$"), 0.75)]
_HINTS = ("email", "phone", "mobile", "pan", "aadhaar", "address")


def pii_score(field: str, value) -> float:
    if value is None:
        return 0.0
    s = str(value)
    for rx, sc in _PAT:
        if rx.match(s):
            return sc
    return 0.75 if any(h in field.lower() for h in _HINTS) else 0.0


def apply_masking(m: ArtifactPayload) -> ArtifactPayload:
    if not m.rows:
        return m
    masked = review = 0
    for row in m.rows:
        for k, v in row.items():
            sc = pii_score(k, v)
            if sc >= REG["pii_mask_threshold"]:
                row[k] = "[MASKED:pii]"
                masked += 1
            elif sc >= REG["pii_review_threshold"]:
                review += 1
    if masked:
        m.summary["pii_masked_fields"] = masked
    if review:
        m.summary["pii_review_needed"] = review
    return m
