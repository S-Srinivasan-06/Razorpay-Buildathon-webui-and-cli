"""Multi-Attribute Matching Engine and Similarity Scoring.

Implements multi-signal pairing algorithms combining:
  - Exact and fuzzy reference key similarity (Levenshtein distance, token containment, digit matching).
  - Net and gross amount tolerance matching with dynamic fee modeling.
  - Business day date window calculations (ignoring weekend clearing delays).
  - LLM-assisted semantic similarity scoring via Gemma 4 with fallback handling.
"""

import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, model_validator

from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import EvidencePiece, MessageKind
from app.core.dispatcher import dispatch_tool_call, ToolCall
from app.engine.fee import (
    compute_fee,
    compute_expected_net,
    compute_tax_component,
    compute_net_settlement,
    compute_deduction_breakdown,
    effective_tolerance,
)


class SemArgs(BaseModel):
    """Input payload schema for LLM semantic similarity evaluation."""
    left: Dict[str, Any]
    right: Dict[str, Any]


class SemResult(BaseModel):
    """Result schema for LLM semantic similarity scoring."""
    score: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def parse_score(cls, data: Any) -> Dict[str, float]:
        """Parse numerical score from various raw LLM response shapes."""
        if isinstance(data, dict):
            if "score" in data:
                try:
                    return {"score": float(data["score"])}
                except Exception:
                    pass
            for v in data.values():
                try:
                    return {"score": float(v)}
                except Exception:
                    pass
        elif isinstance(data, (int, float)):
            return {"score": float(data)}
        return {"score": 0.0}


# LLM tool call specification for semantic similarity scoring
SEM_TOOL = ToolCall(
    name="semantic_similarity",
    args_schema=SemArgs,
    result_schema=SemResult,
    timeout_s=REG["llm_tool_timeout_s"],
    retries=2,
    fallback=lambda a: None,
    cost_budget_usd=0.005,
)


def _lev(a: str, b: str) -> int:
    """Compute standard Levenshtein edit distance between two strings.
    
    Args:
        a: First string.
        b: Second string.
        
    Returns:
        Minimum number of single-character edits (insertions, deletions, substitutions).
    """
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _normalize_token(s: Any) -> str:
    """Strip all non-alphanumeric characters and convert string to lowercase.
    
    Example: 'INV/2026/1039' -> 'inv20261039'.
    """
    return re.sub(r"[^a-zA-Z0-9]", "", str(s)).lower()


def _sim(a: Any, b: Any) -> float:
    """Compute a multi-heuristic similarity score between two identifier strings.
    
    Evaluates:
      1. Exact match and normalized alphanumeric match (e.g. 'INV/2026/1039' == 'INV20261039').
      2. Token substring containment (e.g. 'TXN-ORD-1036' vs 'ORD-1036').
      3. Common numeric sequence matching (e.g. extracting digit runs like '1036').
      4. Normalized Levenshtein edit distance ratio.
      
    Args:
        a: First reference identifier.
        b: Second reference identifier.
        
    Returns:
        Similarity score between 0.0 (unrelated) and 1.0 (identical).
    """
    a_str, b_str = str(a).lower(), str(b).lower()
    if a_str == b_str:
        return 1.0

    # 1. Alphanumeric normalized match
    norm_a, norm_b = _normalize_token(a_str), _normalize_token(b_str)
    if norm_a and norm_a == norm_b:
        return 1.0

    # 2. Token containment and numeric key extraction
    if norm_a and norm_b:
        if norm_a in norm_b or norm_b in norm_a:
            shorter, longer = (norm_a, norm_b) if len(norm_a) < len(norm_b) else (norm_b, norm_a)
            # If the shared subpart is substantial (at least 4 chars or >=50% of the longer token)
            if len(shorter) >= 4 or (len(shorter) / max(len(longer), 1)) >= 0.5:
                return round(max(0.88, len(shorter) / max(len(longer), 1)), 3)

        # Extract digit sequences (e.g. 1036, 1037, 1038)
        digits_a = re.findall(r"\d{3,}", norm_a)
        digits_b = re.findall(r"\d{3,}", norm_b)
        if digits_a and digits_b and any(d in digits_b for d in digits_a):
            return 0.90

    # 3. Normalized Levenshtein distance
    if norm_a and norm_b:
        norm_score = 1 - _lev(norm_a, norm_b) / max(len(norm_a), len(norm_b), 1)
        if norm_score >= 0.70:
            return round(norm_score, 3)

    return round(1 - _lev(a_str, b_str) / max(len(a_str), len(b_str), 1), 3)


def _busdays(d1: datetime.date, d2: datetime.date) -> int:
    """Calculate the number of business days (Monday through Friday) between two dates.
    
    Excludes weekend days to avoid falsely penalizing banking clearing delays.
    Utilizes numpy.busday_count for vectorized C-speed calculation.
    
    Args:
        d1: First date.
        d2: Second date.
        
    Returns:
        Integer count of business days between d1 and d2.
    """
    a, b = sorted((d1, d2))
    try:
        return int(np.busday_count(a, b))
    except Exception:
        # Fallback closed-form computation if dates are edge-case objects
        diff_days = (b - a).days
        full_weeks, extra_days = divmod(diff_days, 7)
        return full_weeks * 5 + min(extra_days, 5)


def _d(v: Any) -> datetime.date:
    """Parse an arbitrary timestamp or date string into a standard date object."""
    return pd.to_datetime(v).date()


def fee_explains(
    a: float,
    rv: float,
    schedule: Optional[Any] = None,
    tol: float = 0.01,
    rules: Optional[List[Any]] = None,
    row: Optional[Dict[str, Any]] = None,
    total_rows: int = 1,
    row_idx: int = 0,
) -> bool:
    """Check if the variance between ledger amount and bank deposit matches the fee schedule or rules.
    
    Returns True if raw amount delta exceeds tolerance but net amount delta
    (gross minus calculated fee/tax) is strictly within tolerance.
    """
    if rules is not None and len(rules) > 0:
        breakdown = compute_deduction_breakdown(a, rules=rules, row=row, total_rows=total_rows, row_idx=row_idx)
        raw = abs(a - rv)
        net = abs(breakdown["expected_net"] - rv)
        return raw > tol and net <= tol and breakdown["total_deductions"] > 0
    if not schedule:
        return False
    raw = abs(a - rv)
    net = abs(compute_expected_net(a, schedule) - rv)
    return raw > tol and net <= tol


def score_pair(
    sid: str,
    l: Dict[str, Any],
    r: Dict[str, Any],
    cfg: Dict[str, Any],
    schedule: Optional[Any] = None,
    fallback_events: Optional[List[str]] = None,
    rules: Optional[List[Any]] = None,
    total_rows: int = 1,
    row_idx: int = 0,
) -> Tuple[float, Dict[str, float], List[EvidencePiece], Optional[float]]:
    """Compute composite multi-attribute match score for a candidate pair of records.
    
    Evaluates:
      1. Reference key similarity (`w_match_key`).
      2. Amount agreement on gross or net-of-fee basis (`w_match_amount`).
      3. Date proximity in business days (`w_match_date`).
      4. Semantic similarity via LLM or deterministic fallback (`w_match_semantic`).
    """
    if fallback_events is None:
        fallback_events = []
    abs_tol = float(cfg.get("tolerance_abs", cfg.get("tolerance", 0.01)))
    pct_tol = float(cfg.get("tolerance_pct", 0.0))
    mode = str(cfg.get("tolerance_mode", "absolute_only"))
    win = int(cfg.get("window_days", 3))

    comps: Dict[str, float] = {}
    w: Dict[str, float] = {}

    # 1. Key similarity
    key = (
        1.0
        if str(l[cfg["left_key"]]) == str(r[cfg["right_key"]])
        else _sim(l[cfg["left_key"]], r[cfg["right_key"]])
    )
    comps["key"], w["key"] = key, REG["w_match_key"]

    # 2. Amount scoring with fee/tax rule evaluation
    signed_delta = None
    raw_matched = fee_x = None
    if cfg.get("left_amount") and cfg.get("right_amount"):
        a, rv = float(l[cfg["left_amount"]]), float(r[cfg["right_amount"]])
        row_tol = effective_tolerance(a, abs_tol=abs_tol, pct_tol=pct_tol, mode=mode)
        raw_delta = abs(a - rv)
        raw_matched = raw_delta <= row_tol

        if rules is not None and len(rules) > 0:
            breakdown = compute_deduction_breakdown(a, rules=rules, row=l, total_rows=total_rows, row_idx=row_idx)
            net_expected = breakdown["expected_net"]
            has_expected_deduction = breakdown["total_deductions"] > 0
        elif schedule:
            net_expected = compute_expected_net(a, schedule)
            has_expected_deduction = abs(net_expected - a) > row_tol
        else:
            net_expected = a
            has_expected_deduction = False

        net_delta = abs(net_expected - rv)
        net_matched = net_delta <= row_tol

        # Enforce strict fee policy: if fee/tax is expected, raw zero-diff match is invalid
        if has_expected_deduction:
            raw_matched = raw_matched and abs(net_expected - a) <= row_tol

        fee_x = fee_explains(a, rv, schedule=schedule, tol=row_tol, rules=rules, row=l, total_rows=total_rows, row_idx=row_idx)
        signed_delta = a - rv
        best = min(raw_delta, net_delta)
        comps["amount"] = (
            1.0
            if (raw_matched or net_matched)
            else max(0.0, 1 - best / max(abs(a) * REG["amount_score_scale_pct"], 1.0))
        )
        w["amount"] = REG["w_match_amount"]
    else:
        fallback_events.append("amount_component_skipped")

    # 3. Date window scoring in business days
    ddiff = None
    if cfg.get("left_date") and cfg.get("right_date"):
        ddiff = _busdays(_d(l[cfg["left_date"]]), _d(r[cfg["right_date"]]))
        comps["date"] = max(0.0, 1 - ddiff / win)
        w["date"] = REG["w_match_date"]

    # 4. Semantic similarity scoring
    if key == 1.0:
        comps["semantic"], w["semantic"] = 1.0, REG["w_match_semantic"]
    elif key < 0.35:
        comps["semantic"], w["semantic"] = 0.0, REG["w_match_semantic"]
    else:
        sem, fb = dispatch_tool_call(sid, SEM_TOOL, {"left": l, "right": r})
        if isinstance(sem, SemResult):
            comps["semantic"], w["semantic"] = sem.score, REG["w_match_semantic"]
        else:
            fallback_events.append(f"semantic_renormalized:{fb}")

    # Calculate weighted composite score
    value = sum(comps[k] * w[k] for k in comps) / sum(w.values())

    # Collect discrete verified evidence pieces
    evidence: List[EvidencePiece] = []
    if key == 1.0:
        evidence.append(EvidencePiece.KEY_MATCH)
    if raw_matched:
        evidence.append(EvidencePiece.AMOUNT_WITHIN_TOL)
    if ddiff is not None and ddiff <= win:
        evidence.append(EvidencePiece.DATE_WITHIN_WINDOW)
    if fee_x:
        evidence.append(EvidencePiece.FEE_MODEL_MATCH)

    return value, comps, evidence, signed_delta
