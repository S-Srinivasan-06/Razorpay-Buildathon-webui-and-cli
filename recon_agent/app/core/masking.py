"""Personally Identifiable Information (PII) Detection and Masking.

Provides regex- and heuristic-based PII scoring for sensitive financial fields
(email addresses, phone numbers, Indian PAN cards, Aadhaar IDs, and residential addresses).
Automatically redacts high-likelihood PII in artifact table rows before transmission.
"""

import re
from typing import Any

from app.core.constants import REG
from app.core.contracts import ArtifactPayload

# Compiled regex patterns with associated PII confidence scores:
#  - Email address (score: 1.00)
#  - International/Domestic phone numbers (score: 0.90)
#  - Indian Permanent Account Number / PAN: 5 letters, 4 digits, 1 letter (score: 0.80)
#  - 12-digit Indian Aadhaar number (score: 0.75)
_PAT = [
    (re.compile(r"^[\w.+-]+@[\w-]+\.\w+$"), 1.0),
    (re.compile(r"^\+?\d[\d\s-]{9,14}$"), 0.9),
    (re.compile(r"^[A-Z]{5}\d{4}[A-Z]$"), 0.8),
    (re.compile(r"^\d{12}$"), 0.75),
]

# Sensitive column header keywords that elevate PII review likelihood
_HINTS = ("email", "phone", "mobile", "pan", "aadhaar", "address")


def pii_score(field: str, value: Any) -> float:
    """Calculate the likelihood score that a field and value contain sensitive PII.
    
    Evaluates value against regex patterns first. If no regex matches, checks if
    the field name contains known sensitive keywords.
    
    Args:
        field: Column or attribute name.
        value: Cell or attribute value to inspect.
        
    Returns:
        Floating point score from 0.0 (non-PII) to 1.0 (confirmed PII).
    """
    if value is None:
        return 0.0
    s = str(value)
    for rx, sc in _PAT:
        if rx.match(s):
            return sc
    return 0.75 if any(h in field.lower() for h in _HINTS) else 0.0


def apply_masking(m: ArtifactPayload) -> ArtifactPayload:
    """Apply in-place masking to all rows in an ArtifactPayload above PII thresholds.
    
    Replaces values with '[MASKED:pii]' when score >= `pii_mask_threshold`, and
    updates artifact summary with total masked and review-needed count metrics.
    
    Args:
        m: ArtifactPayload instance containing table rows.
        
    Returns:
        The mutated ArtifactPayload with masked values.
    """
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

