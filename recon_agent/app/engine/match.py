import datetime

from pydantic import BaseModel, model_validator

from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import EvidencePiece, MessageKind
from app.core.dispatcher import dispatch_tool_call, ToolCall
from app.engine.fee import compute_fee


class SemArgs(BaseModel):
    left: dict
    right: dict

class SemResult(BaseModel):
    score: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def parse_score(cls, data):
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


SEM_TOOL = ToolCall(name="semantic_similarity", args_schema=SemArgs,
                    result_schema=SemResult, timeout_s=REG["llm_tool_timeout_s"],
                    retries=2, fallback=lambda a: None, cost_budget_usd=0.005)


import re

def _lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _normalize_token(s: str) -> str:
    # Strip non-alphanumeric chars and convert to lower
    return re.sub(r"[^a-zA-Z0-9]", "", str(s)).lower()


def _sim(a, b):
    a_str, b_str = str(a).lower(), str(b).lower()
    if a_str == b_str:
        return 1.0

    # 1. Alphanumeric normalized match (e.g. INV/2026/1039 == INV20261039)
    norm_a, norm_b = _normalize_token(a_str), _normalize_token(b_str)
    if norm_a and norm_a == norm_b:
        return 1.0

    # 2. Token containment / numeric key match (e.g. TXN-ORD-1036 vs ORD-1036, BILL_1040 vs BILL-1040-SETTL, RZP_1037 vs 1037_RZP)
    if norm_a and norm_b:
        if norm_a in norm_b or norm_b in norm_a:
            shorter, longer = (norm_a, norm_b) if len(norm_a) < len(norm_b) else (norm_b, norm_a)
            # If the shared subpart is substantial (at least 4 chars or 60% of longer)
            if len(shorter) >= 4 or len(shorter) / max(len(longer), 1) >= 0.5:
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


def _busdays(d1, d2):
    a, b = sorted((d1, d2))
    n, cur = 0, a
    while cur < b:
        cur += datetime.timedelta(days=1)
        if cur.weekday() < 5:
            n += 1
    return n


def _d(v):
    import pandas as pd
    return pd.to_datetime(v).date()


def fee_explains(a: float, rv: float, schedule, tol: float) -> bool:
    if not schedule:
        return False
    raw = abs(a - rv)
    net = abs((a - compute_fee(a, schedule)) - rv)
    return raw > tol and net <= tol


def score_pair(sid, l, r, cfg, schedule, fallback_events):
    tol, win = cfg["tolerance"], cfg["window_days"]
    comps, w = {}, {}
    key = 1.0 if str(l[cfg["left_key"]]) == str(r[cfg["right_key"]]) \
        else _sim(l[cfg["left_key"]], r[cfg["right_key"]])
    comps["key"], w["key"] = key, REG["w_match_key"]

    signed_delta = None
    raw_matched = fee_x = None
    if cfg.get("left_amount") and cfg.get("right_amount"):
        a, rv = float(l[cfg["left_amount"]]), float(r[cfg["right_amount"]])
        raw_delta = abs(a - rv)
        raw_matched = raw_delta <= tol
        fee = compute_fee(a, schedule) if schedule else 0.0
        net_delta = abs((a - fee) - rv)
        net_matched = net_delta <= tol
        fee_x = fee_explains(a, rv, schedule, tol)
        signed_delta = a - rv
        best = min(raw_delta, net_delta)
        comps["amount"] = 1.0 if (raw_matched or net_matched) else max(
            0.0, 1 - best / max(abs(a) * REG["amount_score_scale_pct"], 1.0))
        w["amount"] = REG["w_match_amount"]
    else:
        fallback_events.append("amount_component_skipped")

    ddiff = None
    if cfg.get("left_date") and cfg.get("right_date"):
        ddiff = _busdays(_d(l[cfg["left_date"]]), _d(r[cfg["right_date"]]))
        comps["date"] = max(0.0, 1 - ddiff / win)
        w["date"] = REG["w_match_date"]

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

    value = sum(comps[k] * w[k] for k in comps) / sum(w.values())
    evidence = []
    if key == 1.0:
        evidence.append(EvidencePiece.KEY_MATCH)
    if raw_matched:
        evidence.append(EvidencePiece.AMOUNT_WITHIN_TOL)
    if ddiff is not None and ddiff <= win:
        evidence.append(EvidencePiece.DATE_WITHIN_WINDOW)
    if fee_x:
        evidence.append(EvidencePiece.FEE_MODEL_MATCH)
    return value, comps, evidence, signed_delta
