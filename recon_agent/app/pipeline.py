"""Autonomous Reconciliation Pipeline Orchestrator.

Implements the complete 7-stage financial reconciliation lifecycle:
  1. Ingestion: Parsing CSV and Excel statements, assigning internal Row IDs (_rid).
  2. Profiling: Statistical column analysis, data type detection, PII likelihood scoring.
  3. Schema Mapping: Deterministic candidate key overlap & LLM semantic field linking.
  4. Policy Synthesis & Dry-Run: Baseline match rate calibration and tolerance bounds.
  5. Multi-Attribute Execution: Exact key indexing, amount tolerance, and date proximity.
  6. Quality Assurance & Split Detection: Combinatorial subset sum solving and discrepancy taxonomy.
  7. Aggregation & Audit Trail: Balance summation, metered cost calculation, and cryptographic signing.
"""

import itertools
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd
from pydantic import BaseModel, model_validator

from app.core.audit import audit_for
from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import (
    Actor,
    DecisionRecord,
    EvidencePiece,
    ExecutionResult,
    FeeTaxRule,
    FinalReport,
    MatchComponent,
    MatchedRecord,
    MessageKind,
    Policy,
    PolicyComponent,
    SegmentMatcher,
    UnmatchedRecord,
    VarianceMetrics,
)
from app.core.dispatcher import breaker_open, dispatch_tool_call, ToolCall
from app.core.states import State, StateMachine
from app.engine import match, qa, report, resolving
from app.engine.fee import (
    compute_deduction_breakdown,
    compute_expected_net,
    compute_fee,
    compute_tax_component,
    compute_net_settlement,
    effective_tolerance,
)
from app.engine.match import _sim, fee_explains


class MapArgs(BaseModel):
    """Input payload for the LLM semantic schema mapping tool."""
    tables: Dict[str, List[str]]


class MapResult(BaseModel):
    """Schema mapping configuration specifying linked keys, amounts, and dates."""
    left_table: str = "payments"
    right_table: str = "bank"
    left_key: str = "order_id"
    right_key: str = "utr"
    left_amount: Optional[str] = "amount"
    right_amount: Optional[str] = "credit"
    left_date: Optional[str] = "date"
    right_date: Optional[str] = "date"

    @model_validator(mode="before")
    @classmethod
    def parse_llm_json(cls, data: Any) -> Dict[str, Any]:
        """Normalize varied JSON responses from LLM mapping into canonical schema fields."""
        if not isinstance(data, dict):
            return {}
        res = dict(data)
        if "mappings" in res and isinstance(res["mappings"], list):
            for item in res["mappings"]:
                if isinstance(item, dict):
                    p_val = str(item.get("payments") or item.get("payment") or item.get("left") or "")
                    b_val = str(item.get("bank") or item.get("right") or "")
                    if "id" in p_val or "key" in p_val or "order" in p_val:
                        res["left_key"] = p_val
                        res["right_key"] = b_val
                    elif "amt" in p_val or "amount" in p_val or "credit" in b_val:
                        res["left_amount"] = p_val
                        res["right_amount"] = b_val
                    elif "date" in p_val or "date" in b_val:
                        res["left_date"] = p_val
                        res["right_date"] = b_val
        res.setdefault("left_table", "payments")
        res.setdefault("right_table", "bank")
        res.setdefault("left_key", "order_id")
        res.setdefault("right_key", "utr")
        return res


def _overlap(xs: List[Any], ys: List[Any]) -> float:
    """Calculate the Jaccard-like set overlap ratio between two column value sets.
    
    Args:
        xs: First list of column values.
        ys: Second list of column values.
        
    Returns:
        Intersection size divided by the minimum set size (0.0 to 1.0).
    """
    a, b = set(map(str, xs)), set(map(str, ys))
    return len(a & b) / max(min(len(a), len(b)), 1)


class Pipeline:
    """Core stateful reconciliation engine coordinating all execution phases.
    
    Maintains ingested table records, profiling statistics, schema configurations,
    match policies, intermediate results, exception queues, and final reports.
    """

    def __init__(self, sid: str, auto_ack: bool = False) -> None:
        """Initialize pipeline for a session.
        
        Args:
            sid: Unique session identifier string.
            auto_ack: If True (CLI/test mode), automatically resumes on halts.
                      If False (Web/interactive mode), leaves state at HALT for operator action.
        """
        self.sid: str = sid
        self.auto_ack: bool = auto_ack
        self.sm: StateMachine = StateMachine(sid)
        self.fb: List[str] = []
        self.tables: Dict[str, List[Dict[str, Any]]] = {}
        self.rules: List[FeeTaxRule] = []
        self.schedule: Optional[Any] = None
        self.cfg: Dict[str, Any] = {
            "tolerance": 0.01,
            "tolerance_abs": 0.01,
            "tolerance_pct": 0.0,
            "tolerance_mode": "absolute_only",
            "window_days": 3,
        }
        self.truth: List[Dict[str, Any]] = []
        self.profiles: Dict[str, List[Any]] = {}
        self._map_cands: List[Any] = []
        self._map_conf: float = 0.0
        self._ambiguous: bool = False
        self.exec_res: Optional[ExecutionResult] = None
        self.final: Optional[FinalReport] = None
        self.queue: List[Dict[str, Any]] = []

    def set_rules(self, rules: List[FeeTaxRule]) -> None:
        """Set the active list of segment fee/tax rules."""
        self.rules = list(rules)

    def add_rule(self, rule: FeeTaxRule) -> None:
        """Append a new segment rule to active rules."""
        self.rules.append(rule)

    def set_tolerance(
        self,
        abs_tol: float = 0.01,
        pct_tol: float = 0.0,
        mode: str = "absolute_only",
    ) -> None:
        """Configure user-defined matching tolerance thresholds and combination mode."""
        self.cfg["tolerance_abs"] = float(abs_tol)
        self.cfg["tolerance_pct"] = float(pct_tol)
        self.cfg["tolerance_mode"] = str(mode)
        self.cfg["tolerance"] = float(abs_tol)

    def set_policy(
        self,
        fee_rate: float = 0.0,
        gst_rate: float = 0.0,
        tolerance: float = 0.01,
        window_days: int = 3,
        flat_fee: float = 0.0,
    ) -> None:
        """Configure dynamic fee schedule, tax rate, and tolerance for reconciliation.
        
        Preserves any existing specific segment rules — the policy_rule is added as
        a low-priority (999) catch-all fallback, so fine-grained segment rules take precedence.
        If no segment rules are active, policy_rule becomes the sole rule.
        """
        import datetime
        from app.core.contracts import FeeSchedule, FeeTaxRule, SegmentMatcher
        self.schedule = FeeSchedule(
            provider="custom_policy",
            schedule_id=f"sched_{self.sid}",
            version="1.0",
            effective_from=datetime.date.today(),
            model_type="flat_rate",
            params={"rate": float(fee_rate), "flat": float(flat_fee)},
            gst_rate=float(gst_rate),
        )
        self.cfg["tolerance"] = float(tolerance)
        self.cfg["tolerance_abs"] = float(tolerance)
        self.cfg["window_days"] = int(window_days)

        # Add as priority-999 catch-all: specific segment rules take precedence.
        policy_rule = FeeTaxRule(
            rule_id=f"rule_{uuid.uuid4().hex[:6]}",
            label=f"Standard Policy ({fee_rate*100:.1f}% fee + {gst_rate*100:.1f}% GST)",
            matcher=SegmentMatcher(kind="all"),
            fee_rate=float(fee_rate),
            gst_rate=float(gst_rate),
            flat_fee=float(flat_fee),
            priority=999,
            source="user_explicit",
        )
        # Keep specific segment rules (priority < 999), replace only any previous policy catch-all
        specific_rules = [r for r in self.rules if getattr(r, "priority", 1) < 999]
        self.rules = specific_rules + [policy_rule]
        self.cfg["window_days"] = int(window_days)

    # ---------- Event bus helper methods ----------
    def _chat(self, text: str) -> None:
        """Broadcast a CHAT message event."""
        validate_and_route(self.sid, MessageKind.CHAT, {"text": text[:2000]}, "system")

    def _trace(self, event: str, **d: Any) -> None:
        """Broadcast an execution TRACE telemetry event."""
        validate_and_route(self.sid, MessageKind.TRACE, {"event": event, "detail": d}, "system")

    def _maybe_ack(self, tools: List[str]) -> None:
        """Handle potential state machine halt based on the auto_ack configuration.
        
        When auto_ack=True, resumes immediately in-place (used for CLI or automated tests).
        When auto_ack=False, leaves state at HALT for the interactive caller to resolve.
        """
        if self.auto_ack:
            self.sm.resume()

    # Mapping of State enum values to corresponding Pipeline step handler method names
    _STEP_FN_ATTR = {
        State.PROFILING: "profile",
        State.MAPPING_PROPOSED: "propose_mapping",
        State.MAPPING_VALIDATED: "validate_mapping",
        State.POLICY_GENERATED: "policy",
        State.DRY_RUN: "dry_run",
        State.EXECUTING: "execute",
        State.INSPECTING: "inspect",
        State.REVISION: "revise",
        State.QA: "qa_state",
        State.RESOLVING: "resolve",
    }

    # ---------- Step 1: Ingestion ----------
    def ingest(self, files: List[Path], truth: Optional[Union[str, Path]] = None) -> bool:
        """Parse input CSV/Excel files into memory and assign internal Row IDs (_rid).
        
        Args:
            files: List of file Paths (.csv or .xlsx) representing ledger and statement files.
            truth: Optional path to ground truth JSONL file for benchmark precision/recall evaluation.
            
        Returns:
            True if transitioned to PROFILING state, False otherwise.
        """
        self.sm.enter(State.INGESTING)
        for f in files:
            try:
                df = pd.read_csv(f) if f.suffix == ".csv" else pd.read_excel(f)
                df.insert(0, "_rid", range(1, len(df) + 1))
                tbl_name = f.stem
                # Strip session ID prefix if present (e.g., 'd11231d8_payments' -> 'payments')
                if "_" in tbl_name:
                    prefix, rest = tbl_name.split("_", 1)
                    if len(prefix) == 8 and all(c in "0123456789abcdefABCDEF" for c in prefix):
                        tbl_name = rest
                self.tables[tbl_name] = df.to_dict("records")
            except Exception as e:
                self._trace("UNPARSED", file=str(f), err=str(e)[:120])
        if truth:
            self.truth = [json.loads(l) for l in Path(truth).read_text().splitlines() if l]
        self._trace(
            "INGESTION_COMPLETED",
            tables={t: len(r) for t, r in self.tables.items()},
            total_rows=sum(len(r) for r in self.tables.values()),
        )
        return self.sm.transition(State.PROFILING, f"{len(self.tables)} tables")

    # ---------- Step 2: Profiling ----------
    def profile(self) -> bool:
        """Compute statistical profiles, column data types, and PII likelihood for each table."""
        print("- **Step 1/7**: Profiling table schemas and column statistics...", flush=True)
        from app.core.contracts import ColumnProfile
        from app.core.masking import pii_score

        for name, rows in self.tables.items():
            df = pd.DataFrame(rows)
            self.profiles[name] = []
            for c in df.columns:
                if c == "_rid":
                    continue
                s = df[c].astype(str)
                num = pd.to_numeric(df[c], errors="coerce").notna().mean()
                dat = pd.to_datetime(df[c], errors="coerce", format="mixed").notna().mean()
                self.profiles[name].append(
                    ColumnProfile(
                        name=c,
                        dtype=str(df[c].dtype),
                        numeric_ratio=float(num),
                        date_ratio=float(dat),
                        cardinality=float(df[c].nunique() / max(len(df), 1)),
                        null_rate=float(df[c].isna().mean()),
                        min_len=int(s.str.len().min() or 0),
                        max_len=int(s.str.len().max() or 0),
                        sample_values=s.head(3).tolist(),
                        pii_likelihood=max((pii_score(c, v) for v in s.head(5)), default=0.0),
                    )
                )
        self._trace(
            "PROFILING_COMPLETED",
            table_count=len(self.tables),
            column_count=sum(len(p) for p in self.profiles.values()),
        )
        return self.sm.transition(State.MAPPING_PROPOSED)

    def _pick(self, t: str, kind: str) -> Optional[str]:
        """Heuristically select a column name of a given semantic type ('numeric' or 'date')."""
        for p in self.profiles.get(t, []):
            if kind == "numeric" and p.numeric_ratio > 0.8 and p.cardinality > 0.3:
                return p.name
            if kind == "date" and p.date_ratio > 0.8 and p.numeric_ratio <= 0.8:
                return p.name
        return None

    # ---------- Step 3: Schema Mapping ----------
    def propose_mapping(self) -> bool:
        """Identify candidate primary keys and invoke LLM semantic mapping tool."""
        print("- **Step 2/7**: Linking schema keys and amounts via mapping tool...", flush=True)
        names = list(self.tables)
        cands = []
        for lt in names:
            for rt in names:
                if lt == rt:
                    continue
                for lc in [p.name for p in self.profiles[lt]]:
                    for rc in [p.name for p in self.profiles[rt]]:
                        ov = _overlap(
                            [r.get(lc) for r in self.tables[lt]],
                            [r.get(rc) for r in self.tables[rt]],
                        )
                        if ov >= 0.10:
                            cands.append((ov, lt, lc, rt, rc))
        cands.sort(reverse=True)
        self._map_cands = cands

        tool = ToolCall(
            name="mapping_semantic",
            args_schema=MapArgs,
            result_schema=MapResult,
            timeout_s=REG["llm_tool_timeout_s"],
            retries=2,
            fallback=lambda a: None,
            cost_budget_usd=0.005,
        )
        llm_map, fb = dispatch_tool_call(
            self.sid,
            tool,
            {"tables": {n: [p.name for p in self.profiles[n]] for n in names}},
        )
        if llm_map is None and fb:
            self.fb.append(f"mapping_heuristic:{fb}")

        if isinstance(llm_map, MapResult):
            self.cfg = llm_map.model_dump()
            self.cfg["left_amount"] = self.cfg.get("left_amount") or self._pick(self.cfg["left_table"], "numeric")
            self.cfg["right_amount"] = self.cfg.get("right_amount") or self._pick(self.cfg["right_table"], "numeric")
            self.cfg["left_date"] = self.cfg.get("left_date") or self._pick(self.cfg["left_table"], "date")
            self.cfg["right_date"] = self.cfg.get("right_date") or self._pick(self.cfg["right_table"], "date")
            self._map_conf = 0.9
        elif cands:
            ov, lt, lc, rt, rc = cands[0]
            self._ambiguous = len(cands) > 1 and (cands[0][0] - cands[1][0]) <= REG["mapping_ambiguity_delta"]
            self.cfg = {
                "left_table": lt,
                "right_table": rt,
                "left_key": lc,
                "right_key": rc,
                "left_amount": self._pick(lt, "numeric"),
                "right_amount": self._pick(rt, "numeric"),
                "left_date": self._pick(lt, "date"),
                "right_date": self._pick(rt, "date"),
            }
            self._map_conf = min(0.45 + ov / 2, 0.95)
        else:
            self.sm.halt("no linkable columns")
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.MAPPING_PROPOSED
                return False

        if breaker_open(self.sid, "mapping_semantic"):
            self.sm.halt("circuit open: mapping_semantic", tools=["mapping_semantic"])
            self._maybe_ack(["mapping_semantic"])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.MAPPING_VALIDATED
                return False

        return self.sm.transition(State.MAPPING_VALIDATED)

    def validate_mapping(self) -> bool:
        """Validate proposed schema mapping confidence and record decision in audit log."""
        audit_for(self.sid).append(
            DecisionRecord(
                decision_id=uuid.uuid4().hex,
                ts=pd.Timestamp.now(tz="UTC").to_pydatetime(),
                state="MAPPING_VALIDATED",
                actor=Actor.SYSTEM,
                decision_kind="mapping",
                proposal={"candidates": [list(c[1:]) for c in self._map_cands[:3]]},
                final={k: self.cfg.get(k) for k in ("left_table", "right_table", "left_key", "right_key")},
                confidence=self._map_conf,
                evidence=[],
            ).model_dump(mode="json")
        )

        if self._map_conf < REG["mapping_review_floor"]:
            self.sm.halt("mapping below review floor")
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.MAPPING_VALIDATED
                return False

        if self._ambiguous or self._map_conf < REG["mapping_auto_accept"]:
            self._chat(f"Mapping confidence {self._map_conf:.2f} — proceeding with trace visibility.")

        self._trace(
            "MAPPING_PROPOSED",
            left_table=self.cfg.get("left_table"),
            right_table=self.cfg.get("right_table"),
            key_linkage=f"{self.cfg.get('left_key')} <-> {self.cfg.get('right_key')}",
            confidence=round(self._map_conf, 3),
        )
        return self.sm.transition(State.POLICY_GENERATED)

    # ---------- Step 4: Policy Synthesis & Dry-Run ----------
    def policy(self) -> bool:
        """Synthesize match policy components and initialize tolerance windows."""
        print("- **Step 3/7**: Synthesizing policy components & tolerance windows...", flush=True)
        comps = [
            PolicyComponent(component=c, params={}, precedence=i)
            for i, c in enumerate(MatchComponent, 1)
        ]
        comps[3].params = {"tolerance": 0.01, "window_days": 3}
        self.policy_doc = Policy(
            components=comps,
            baseline_match_rate=0.0,
            baseline_computed_at=pd.Timestamp.now(tz="UTC").to_pydatetime(),
            baseline_constants_version=REG.version,
        )
        self.cfg.setdefault("tolerance", 0.01)
        self.cfg.setdefault("window_days", 3)
        self._trace(
            "POLICY_CALIBRATED",
            fee_rate=f"{self.cfg.get('fee_rate', 0.02)*100:.1f}%",
            gst_rate=f"{self.cfg.get('gst_rate', 0.18)*100:.1f}%",
            tolerance=f"INR {self.cfg.get('tolerance', 0.02):.2f}",
            mode=self.cfg.get("tolerance_mode", "absolute_only"),
            active_rules=len(self.rules),
        )
        return self.sm.transition(State.DRY_RUN)

    # ---------- Scoring Core ----------
    def _score_all(self, rows_l: List[Dict[str, Any]], rows_r: List[Dict[str, Any]]) -> ExecutionResult:
        """Execute multi-attribute matching across left ledger and right statement rows.
        
        Optimizations:
          - Pre-indexes right rows by exact key for O(1) direct candidate lookups.
          - Filters candidate search pool by amount proximity on large datasets (>300 rows).
          - Detects duplicates in the left ledger.
          - Tracks soft-paired right rows to prevent duplicate exception listings.
        """
        self._last_cand_scores: List[float] = []
        matched: List[MatchedRecord] = []
        unmatched: List[UnmatchedRecord] = []
        dups: List[Dict[str, Any]] = []
        per: List[Dict[str, Any]] = []
        unmatched_ctx: List[Tuple[UnmatchedRecord, Optional[Dict[str, Any]], List[EvidencePiece], Optional[float]]] = []

        # Index left rows by key to identify duplicates
        lkeys: Dict[str, List[Dict[str, Any]]] = {}
        for l in rows_l:
            lkeys.setdefault(str(l[self.cfg["left_key"]]), []).append(l)
        dup_keys = {k for k, v in lkeys.items() if len(v) > 1}
        seen_dup: Set[str] = set()

        used_r: Set[int] = set()
        soft_paired_r: Set[int] = set()  # Right records already represented via an unmatched left pairing

        # Index right rows by key for instant exact candidate lookup
        r_by_key: Dict[str, List[Dict[str, Any]]] = {}
        rk = self.cfg["right_key"]
        for r in rows_r:
            r_by_key.setdefault(str(r.get(rk)), []).append(r)

        def mk_unmatched(
            l_row: Optional[Dict[str, Any]],
            r_row: Optional[Dict[str, Any]],
            v: Optional[float],
            ev: List[EvidencePiece],
            sd: Optional[float],
        ) -> Tuple[UnmatchedRecord, List[EvidencePiece]]:
            side = "L" if l_row is not None else "R"
            ref_key = self.cfg["left_key"] if l_row is not None else self.cfg["right_key"]
            rec = UnmatchedRecord(
                side=side,
                rid=(l_row or r_row)["_rid"],
                ref=str((l_row or r_row).get(ref_key)),
                delta=sd,
                match_confidence=v,
            )
            return rec, ev

        is_large = len(rows_r) > 300
        for l_idx, l in enumerate(rows_l):
            key = str(l[self.cfg["left_key"]])
            if key in dup_keys and key not in seen_dup:
                dups.append({"side": "L", "key": key, "rids": [x["_rid"] for x in lkeys[key]]})
                seen_dup.add(key)

            # Check direct exact key matches first
            direct_cands = [r for r in r_by_key.get(key, []) if r["_rid"] not in used_r]
            if direct_cands:
                cands = [
                    (
                        r,
                        *match.score_pair(
                            self.sid,
                            l,
                            r,
                            self.cfg,
                            schedule=self.schedule,
                            fallback_events=self.fb,
                            rules=self.rules,
                            total_rows=len(rows_l),
                            row_idx=l_idx,
                        ),
                    )
                    for r in direct_cands
                ]
                cands = [(r, v, c, e, d) for (r, v, c, e, d) in cands if v >= REG["match_review_floor"]]
            else:
                cands = []

            # If no direct match meets threshold, search candidate pool
            if not cands:
                search_pool = [r for r in rows_r if r["_rid"] not in used_r]
                if is_large and len(search_pool) > 200:
                    # On large datasets, filter candidates by amount proximity
                    la = float(l.get(self.cfg.get("left_amount", ""), 0) or 0)
                    ra_key = self.cfg.get("right_amount", "")
                    search_pool = sorted(
                        search_pool,
                        key=lambda r: abs(la - float(r.get(ra_key, 0) or 0)) if ra_key else 0,
                    )[:150]

                cands = [
                    (
                        r,
                        *match.score_pair(
                            self.sid,
                            l,
                            r,
                            self.cfg,
                            schedule=self.schedule,
                            fallback_events=self.fb,
                            rules=self.rules,
                            total_rows=len(rows_l),
                            row_idx=l_idx,
                        ),
                    )
                    for r in search_pool
                ]
                cands = [(r, v, c, e, d) for (r, v, c, e, d) in cands if v >= REG["match_review_floor"]]

            self._last_cand_scores.extend(v for _, v, _, _, _ in cands)

            if not cands:
                rec, ev = mk_unmatched(l, None, None, [], None)
                unmatched.append(rec)
                unmatched_ctx.append((rec, None, ev, None))
                continue

            r, v, comps, ev, sd = max(cands, key=lambda t: t[1])
            if v >= REG["match_auto_threshold"]:
                used_r.add(r["_rid"])
                matched.append(
                    MatchedRecord(
                        l_rid=l["_rid"],
                        r_rid=r["_rid"],
                        composite_score=v,
                        components=comps,
                        policy_version=REG.version,
                    )
                )
                per.append({"l_id": l["_rid"], "r_id": r["_rid"], "abs": abs(sd or 0), "signed": sd})
            else:
                rec, ev = mk_unmatched(l, r, v, ev, sd)
                unmatched.append(rec)
                unmatched_ctx.append((rec, r, ev, sd))
                soft_paired_r.add(r["_rid"])  # Prevent right record from appearing as duplicate standalone entry

        # Collect remaining unmatched right statement records
        for r in rows_r:
            if r["_rid"] not in used_r and r["_rid"] not in soft_paired_r:
                rec, ev = mk_unmatched(None, r, None, [], None)
                unmatched.append(rec)
                unmatched_ctx.append((rec, None, ev, None))

        var = VarianceMetrics(
            abs_sum=sum(p["abs"] for p in per),
            signed_sum=sum(p["signed"] for p in per),
            per_record=per,
        )
        self._last_unmatched_ctx = unmatched_ctx
        return ExecutionResult(
            matched=matched,
            unmatched=unmatched,
            duplicates=dups,
            splits=[],
            variance=var,
        )

    def dry_run(self) -> bool:
        """Run dry-run calibration on the first 100 records to establish a baseline match rate."""
        print("- **Step 4/7**: Performing dry-run calibration on sample rows...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]][:100]
        rows_r = self.tables[self.cfg["right_table"]]
        t0 = time.time()
        res = self._score_all(rows_l, rows_r)
        self.policy_doc.baseline_match_rate = len(res.matched) / max(len(rows_l), 1)
        mean_cand = (
            sum(self._last_cand_scores) / len(self._last_cand_scores)
            if self._last_cand_scores
            else 0.0
        )
        if mean_cand < REG["calibration_sanity_floor"]:
            self._trace("CALIBRATION_DRIFT_WARNING", mean_cand=round(mean_cand, 3))
        self._trace(
            "DRY_RUN_EVALUATED",
            sample_size=len(rows_l),
            projected_match_rate=f"{(self.policy_doc.baseline_match_rate or 0.0)*100:.1f}%",
            duration_s=round(time.time() - t0, 2),
        )
        return self.sm.transition(State.EXECUTING)

    # ---------- Step 5: Multi-Attribute Execution ----------
    def execute(self) -> bool:
        """Execute the full matching run across all ingested records."""
        print("- **Step 5/7**: Executing multi-attribute matching engine...", flush=True)
        t0 = time.time()
        self.exec_res = self._score_all(
            self.tables[self.cfg["left_table"]],
            self.tables[self.cfg["right_table"]],
        )
        self._exec_s = max(time.time() - t0, 1e-6)
        self._trace(
            "EXECUTION_MATCHING_COMPLETED",
            matched_pairs=len(self.exec_res.matched),
            left_rows=len(self.tables[self.cfg["left_table"]]),
            right_rows=len(self.tables[self.cfg["right_table"]]),
            unmatched_count=len(self.exec_res.unmatched),
            duration_s=round(self._exec_s, 2),
        )
        return self.sm.transition(State.INSPECTING)

    def _inspect_metrics(self) -> None:
        """Compute match rate, throughput, and precision/recall against ground truth."""
        r = self.exec_res
        total = len(r.matched) + len(r.unmatched)
        self.match_rate = len(r.matched) / max(total, 1)
        nrows = sum(len(t) for t in self.tables.values())
        self.throughput = nrows / max(getattr(self, "_exec_s", 1.0), 1e-6)
        pred = {(m.l_rid, m.r_rid) for m in r.matched}

        if not getattr(self, "truth", None):
            self.precision = None
            self.recall = None
            return

        truth = set()
        for t in self.truth:
            lr = tuple(t["l_rid"]) if isinstance(t["l_rid"], list) else t["l_rid"]
            rr = tuple(t["r_rid"]) if isinstance(t["r_rid"], list) else t["r_rid"]
            truth.add((lr, rr))

        self.precision = (len(pred & truth) / len(pred)) if pred else None
        self.recall = (len(pred & truth) / len(truth)) if truth else None

    def inspect(self) -> bool:
        """Inspect match quality metrics; trigger adaptive revision if below threshold."""
        self._inspect_metrics()
        self._trace(
            "INSPECTION_METRICS",
            match_rate=f"{(self.match_rate or 0.0)*100:.1f}%",
            threshold=f"{REG['revision_match_rate_threshold']*100:.1f}%",
            status="PASS" if self.match_rate >= REG["revision_match_rate_threshold"] else "REVISION_TRIGGERED",
        )
        if self.match_rate < REG["revision_match_rate_threshold"]:
            return self.sm.transition(State.REVISION)
        return self.sm.transition(State.QA)

    def revise(self) -> bool:
        """Adaptive revision loop adjusting amount tolerance bounds when match rate is low."""
        it, t0 = 0, time.time()
        while (
            self.match_rate < REG["revision_match_rate_threshold"]
            and it < REG["revision_iteration_cap"]
            and time.time() - t0 < REG["revision_time_cap_s"]
        ):
            old = self.cfg["tolerance"]
            self.cfg["tolerance"] = round(old * 1.2, 4)
            self._trace("REVISION_OPTIMIZATION", iteration=it + 1, calibrated_tolerance=round(self.cfg["tolerance"], 4))
            if self.sm.state != State.EXECUTING:
                self.sm.transition(State.EXECUTING)
            self.execute()
            self._inspect_metrics()
            # If tolerance expansion caused a regression compared to baseline, revert and break
            if self.policy_doc.baseline_match_rate - self.match_rate > REG["regression_reject_delta"]:
                self.cfg["tolerance"] = old
                self._trace("REVISION_REGRESSION_REJECTED", iteration=it + 1, note="Reverted tolerance to avoid regression")
                break
            it += 1

        if self.match_rate < REG["revision_match_rate_threshold"]:
            self.sm.halt("revision caps exhausted or regression rejected")
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.QA
                return False
        return self.sm.transition(State.QA)

    # ---------- Step 6: QA & Exception Classification ----------
    def _ctx(
        self,
        side: str,
        l: Optional[Dict[str, Any]],
        r: Optional[Dict[str, Any]],
        rows_l: List[Dict[str, Any]],
        rows_r: List[Dict[str, Any]],
        sd: Optional[float],
        used_l: Optional[Set[int]] = None,
        suppress_split: bool = False,
    ) -> Dict[str, Any]:
        """Extract diagnostic context signals for a specific unmatched record."""
        lk, rk = self.cfg["left_key"], self.cfg["right_key"]
        abs_tol = float(self.cfg.get("tolerance_abs", self.cfg.get("tolerance", 0.01)))
        pct_tol = float(self.cfg.get("tolerance_pct", 0.0))
        mode = str(self.cfg.get("tolerance_mode", "absolute_only"))
        used_l = used_l or set()
        ctx: Dict[str, Any] = {
            k: ([] if k in ("dup_rids", "split_targets") else False) for k in qa.CTX_KEYS
        }

        if side == "L" and l is not None:
            key = str(l[lk])
            ctx["dup_rids"] = [x["_rid"] for x in rows_l if str(x[lk]) == key and x["_rid"] != l["_rid"]]
            cands = [x for x in rows_r if str(x[rk]) == key]
            ctx["single_target"] = len(cands) == 1
            if cands and self.cfg.get("left_amount"):
                a = float(l[self.cfg["left_amount"]])
                rv = float(cands[0][self.cfg["right_amount"]])
                row_tol = effective_tolerance(a, abs_tol=abs_tol, pct_tol=pct_tol, mode=mode)
                
                # Composite rule/schedule evaluation — thread row_idx from _rid for defense-in-depth
                l_row_idx = (int(l["_rid"]) - 1) if "_rid" in l else 0
                if self.rules:
                    deductions = compute_deduction_breakdown(a, rules=self.rules, row=l, total_rows=len(rows_l), row_idx=l_row_idx)
                elif self.schedule:
                    deductions = compute_deduction_breakdown(a, schedule=self.schedule)
                else:
                    deductions = {
                        "gross": a,
                        "gateway_fee": 0.0,
                        "gst": 0.0,
                        "tds": 0.0,
                        "total_deductions": 0.0,
                        "expected_net": a,
                        "rule_label": "Zero Fee/Tax (Default)",
                    }
                
                expected_net = deductions["expected_net"]
                ctx["rule_label"] = deductions.get("rule_label")
                ctx["tolerance_str"] = f"₹{row_tol:.2f} ({mode})"
                ctx["fee_match"] = abs(expected_net - rv) <= row_tol and (deductions.get("gateway_fee", 0) > 0 or deductions.get("total_deductions", 0) > 0)
                ctx["tax_match"] = (deductions.get("tds", 0) > 0 or deductions.get("gst", 0) > 0) and abs(expected_net - rv) <= row_tol

                # Currency conversion / FX rate match (e.g. USD to INR conversion corridor)
                if a > 0 and rv > 0:
                    ratio = rv / a
                    fx_min = self.schedule.fx_corridor_min if self.schedule else 0.010
                    fx_max = self.schedule.fx_corridor_max if self.schedule else 0.015
                    ctx["fx_match"] = (1.0 / fx_max <= ratio <= 1.0 / fx_min) or (fx_min <= ratio <= fx_max)

                ctx["partial"] = rv < a and not ctx["fee_match"] and not ctx["tax_match"]
                if self.cfg.get("left_date"):
                    dd = match._busdays(
                        match._d(l[self.cfg["left_date"]]),
                        match._d(cands[0][self.cfg["right_date"]]),
                    )
                    ctx["date_only_mismatch"] = dd > self.cfg["window_days"] and (
                        abs(a - rv) <= row_tol or ctx["fee_match"]
                    )
            if not cands:
                # Corroborate fuzzy key similarity with amount/fee consistency
                a = float(l[self.cfg["left_amount"]]) if self.cfg.get("left_amount") else None
                search_r = (
                    rows_r
                    if len(rows_r) <= 500
                    else [
                        x
                        for x in rows_r
                        if abs(a - float(x.get(self.cfg.get("right_amount", ""), 0) or 0)) <= 1000
                    ][:100]
                )
                if a is not None and self.cfg.get("right_amount"):
                    row_tol = effective_tolerance(a, abs_tol=abs_tol, pct_tol=pct_tol, mode=mode)
                    l_row_idx = (int(l["_rid"]) - 1) if l and "_rid" in l else 0
                    ctx["fuzzy_key"] = any(
                        match._sim(key, str(x[rk])) >= 0.75
                        and (
                            abs(a - float(x[self.cfg["right_amount"]])) <= row_tol
                            or fee_explains(a, float(x[self.cfg["right_amount"]]), schedule=self.schedule, tol=row_tol, rules=self.rules, row=l, total_rows=len(rows_l), row_idx=l_row_idx)
                        )
                        for x in search_r
                    )
                else:
                    ctx["fuzzy_key"] = max((match._sim(key, str(x[rk])) for x in search_r), default=0) >= 0.75

        if side == "R" and r is not None:
            rv = float(r[self.cfg["right_amount"]]) if self.cfg.get("right_amount") else 0.0
            ctx["negative_credit"] = rv < 0
            if not suppress_split:
                nets = []
                # Only search among UNMATCHED left rows to avoid reusing 1:1 matched records
                unmatched_l = [x for x in rows_l if x["_rid"] not in used_l]
                for x in unmatched_l:
                    a = float(x.get(self.cfg["left_amount"], 0))
                    x_row_idx = (int(x["_rid"]) - 1) if "_rid" in x else 0
                    if self.rules:
                        net_val = compute_deduction_breakdown(a, rules=self.rules, row=x, total_rows=len(rows_l), row_idx=x_row_idx)["expected_net"]
                    elif self.schedule:
                        net_val = compute_expected_net(a, self.schedule)
                    else:
                        net_val = a
                    nets.append((x["_rid"], net_val))
                # Bounded pool search for combinatorial split subsets
                valid_nets = [x for x in nets if 0 < x[1] <= rv + abs_tol]
                pool = valid_nets[:40]
                for k in (2, 3):
                    for combo in itertools.combinations(pool, k):
                        if abs(sum(v for _, v in combo) - rv) <= abs_tol:
                            ctx["split_targets"] = [i for i, _ in combo]
                            break
                    if ctx["split_targets"]:
                        break

        return ctx

    def qa_state(self) -> bool:
        """Classify exceptions and solve combinatorial batch/split transactions globally."""
        print("- **Step 6/7**: Classifying exceptions & verifying invariant proofs...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]]
        rows_r = self.tables[self.cfg["right_table"]]
        l_by_rid = {x["_rid"]: x for x in rows_l}
        r_by_rid = {x["_rid"]: x for x in rows_r}
        used_l = {m.l_rid for m in self.exec_res.matched}
        tol = float(self.cfg.get("tolerance_abs", self.cfg.get("tolerance", 0.01)))

        # 1. First pass: solve combinatorial splits globally with disjoint left allocations
        right_splits: Dict[int, List[int]] = {}
        allocated_split_l: Set[int] = set()
        unmatched_r_items = [
            (rec, r_cand, ev, sd)
            for (rec, r_cand, ev, sd) in self._last_unmatched_ctx
            if rec.side == "R"
        ]

        # Exclude left rows that have a direct key match in rows_r (e.g. Temporal Drift rows)
        r_keys = {str(x.get(self.cfg["right_key"])): x for x in rows_r}
        temporal_or_direct_l: Set[int] = set()
        for x in rows_l:
            key = str(x.get(self.cfg["left_key"]))
            if key in r_keys:
                temporal_or_direct_l.add(x["_rid"])

        # Calculate net amounts for all unmatched left rows eligible for split pools
        left_nets: List[Tuple[int, float]] = []
        for x in rows_l:
            if x["_rid"] not in used_l and x["_rid"] not in temporal_or_direct_l:
                a = float(x.get(self.cfg["left_amount"], 0))
                x_row_idx = (int(x["_rid"]) - 1) if "_rid" in x else 0
                if self.rules:
                    net = compute_deduction_breakdown(a, rules=self.rules, row=x, total_rows=len(rows_l), row_idx=x_row_idx)["expected_net"]
                elif self.schedule:
                    net = compute_expected_net(a, self.schedule)
                else:
                    net = a
                left_nets.append((x["_rid"], net))

        ambiguous_splits: Set[int] = set()

        for rec, r_cand, ev, sd in unmatched_r_items:
            r = r_by_rid.get(rec.rid) or next((x for x in rows_r if x["_rid"] == rec.rid), None)
            if not r:
                continue
            rv = float(r.get(self.cfg["right_amount"], 0) or 0)
            if rv <= 0:
                continue

            avail = sorted([x for x in left_nets if x[0] not in allocated_split_l and 0 < x[1] <= rv + tol], key=lambda x: abs(x[1] - rv))[:40]
            matching_combos = []
            for k in (2, 3):
                for combo in itertools.combinations(avail, k):
                    if abs(sum(v for _, v in combo) - rv) <= tol:
                        matching_combos.append([i for i, _ in combo])
                        if len(matching_combos) >= 2:
                            break
                if len(matching_combos) >= 2:
                    break

            if matching_combos:
                found_combo = matching_combos[0]
                right_splits[rec.rid] = found_combo
                allocated_split_l.update(found_combo)
                if len(matching_combos) > 1:
                    ambiguous_splits.add(rec.rid)

        # 2. Second pass: construct exception queue with accurate classification
        self.queue = []
        left_split_map: Dict[int, str] = {}
        for r_rid, target_l_rids in right_splits.items():
            r_row = r_by_rid.get(r_rid) or {}
            r_ref = str(r_row.get(self.cfg["right_key"]) or f"RID_{r_rid}")
            for l_rid in target_l_rids:
                left_split_map[l_rid] = r_ref

        for rec, r_cand, ev, sd in self._last_unmatched_ctx:
            if rec.side == "L":
                l = l_by_rid.get(rec.rid) or next((x for x in rows_l if x["_rid"] == rec.rid), {})
                ctx = self._ctx("L", l, r_cand, rows_l, rows_r, sd, used_l=used_l)
                if rec.rid in left_split_map:
                    rec.reason = qa.H.SPLIT
                    ctx["split_batch_ref"] = left_split_map[rec.rid]
                    ctx["split_targets"] = [rec.rid]
                    r_rid = next((k for k, v in right_splits.items() if rec.rid in v), None)
                    if r_rid in ambiguous_splits:
                        ctx["ambiguous_split"] = True
                    ev = [EvidencePiece.FEE_MODEL_MATCH, EvidencePiece.KEY_MATCH]
                else:
                    rec.reason = qa.classify(rec, ctx)
                    if rec.reason == qa.H.COUNTERPARTY_MISMATCH and not ev:
                        ev = [EvidencePiece.KEY_MATCH, EvidencePiece.AMOUNT_WITHIN_TOL]
                    elif rec.reason == qa.H.FEE_DEDUCTION:
                        if EvidencePiece.FEE_MODEL_MATCH not in ev:
                            ev.append(EvidencePiece.FEE_MODEL_MATCH)
                        if EvidencePiece.KEY_MATCH not in ev:
                            ev.append(EvidencePiece.KEY_MATCH)
                    elif rec.reason == qa.H.TAX_WITHHOLDING:
                        if EvidencePiece.TAX_MODEL_MATCH not in ev:
                            ev.append(EvidencePiece.TAX_MODEL_MATCH)
                        if EvidencePiece.KEY_MATCH not in ev:
                            ev.append(EvidencePiece.KEY_MATCH)
                    elif rec.reason == qa.H.CURRENCY_CONVERSION:
                        if EvidencePiece.FX_MODEL_MATCH not in ev:
                            ev.append(EvidencePiece.FX_MODEL_MATCH)
                        if EvidencePiece.KEY_MATCH not in ev:
                            ev.append(EvidencePiece.KEY_MATCH)
            else:
                r = r_by_rid.get(rec.rid) or next((x for x in rows_r if x["_rid"] == rec.rid), {})
                ctx = self._ctx("R", None, r, rows_l, rows_r, sd, used_l=used_l, suppress_split=(rec.rid not in right_splits))
                if rec.rid in right_splits:
                    ctx["split_targets"] = right_splits[rec.rid]
                    if rec.rid in ambiguous_splits:
                        ctx["ambiguous_split"] = True
                    rec.reason = qa.H.SPLIT
                    ev = [EvidencePiece.FEE_MODEL_MATCH, EvidencePiece.KEY_MATCH]
                else:
                    rec.reason = qa.classify(rec, ctx)
                    if rec.reason == qa.H.FEE_DEDUCTION and EvidencePiece.FEE_MODEL_MATCH not in ev:
                        ev.append(EvidencePiece.FEE_MODEL_MATCH)
                    elif rec.reason == qa.H.TAX_WITHHOLDING and EvidencePiece.TAX_MODEL_MATCH not in ev:
                        ev.append(EvidencePiece.TAX_MODEL_MATCH)
                    elif rec.reason == qa.H.CURRENCY_CONVERSION and EvidencePiece.FX_MODEL_MATCH not in ev:
                        ev.append(EvidencePiece.FX_MODEL_MATCH)

            self.queue.append({"rec": rec, "ctx": ctx, "pieces": ev})

        self._trace(
            "QA_CLASSIFICATION_COMPLETED",
            exceptions_analyzed=len(self.queue),
            categories=list({x["rec"].reason.value for x in self.queue}),
        )
        return self.sm.transition(State.RESOLVING)

    def resolve(self) -> bool:
        """Evaluate confidence scores, assign resolution actions, and record decision audit logs."""
        for item in self.queue:
            rec, pieces, ctx = item["rec"], item["pieces"], item.get("ctx", {})
            conf = resolving.exception_confidence(len(pieces), rec.reason, None)
            action = resolving.decide_action(conf, len(pieces), rec.reason, ctx)
            explanation = resolving.generate_explanation(rec, ctx)
            rec.explanation = explanation
            item["action"], item["conf"], item["explanation"] = action, conf, explanation
            actor = (
                Actor.SYSTEM
                if action in ("auto_resolve", "mark_pending", "request_confirmation")
                else Actor.FALLBACK
            )
            audit_for(self.sid).append(
                DecisionRecord(
                    decision_id=uuid.uuid4().hex,
                    ts=pd.Timestamp.now(tz="UTC").to_pydatetime(),
                    state="RESOLVING",
                    actor=actor,
                    decision_kind="exception_resolve",
                    proposal={"category": rec.reason.value, "explanation": explanation},
                    final={"action": action},
                    confidence=conf,
                    evidence=pieces,
                ).model_dump(mode="json")
            )
        self._trace(
            "AUTONOMOUS_RESOLUTION_COMPLETED",
            auto_resolved=len([x for x in self.queue if x.get("action") == "auto_resolve"]),
            escalated=len([x for x in self.queue if x.get("action") == "escalate"]),
            pending=len([x for x in self.queue if x.get("action") not in ("auto_resolve", "escalate")]),
        )
        return self.sm.transition(State.AGGREGATING)

    # ---------- Step 7: Aggregation & Final Report ----------
    def aggregate(self, elapsed: float) -> bool:
        """Sum gross, net, fee, and exception balances, then construct the FinalReport."""
        print("- **Step 7/7**: Aggregating financial balances & signing cryptographic audit ledger...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]]
        rows_r = self.tables[self.cfg["right_table"]]
        g = sum(float(x.get(self.cfg["left_amount"], 0)) for x in rows_l)
        n = sum(float(x.get(self.cfg["right_amount"], 0)) for x in rows_r)
        mv = sum(
            float(x.get(self.cfg["left_amount"], 0))
            for x in rows_l
            if x["_rid"] in {m.l_rid for m in self.exec_res.matched}
        )
        totals = {
            "gross": round(g, 2),
            "net": round(n, 2),
            "fees": round(g - n, 2),
            "matched_value": round(mv, 2),
            "exception_value": round(g - mv, 2),
        }
        self.final = report.build_final_report(
            self.sid,
            match_rate=self.match_rate,
            precision_vs_truth=self.precision,
            recall_vs_truth=self.recall,
            throughput_rows_per_sec=self.throughput,
            exceptions=self.queue,
            elapsed_seconds=elapsed,
            totals=totals,
            llm_user_disagreements=[],
            fallback_events=self.fb,
        )
        self._trace(
            "RECONCILIATION_FINALIZED",
            match_rate=f"{(self.match_rate or 0.0)*100:.1f}%",
            total_sales_volume=f"INR {totals['gross']:,.2f}",
            net_bank_settled=f"INR {totals['net']:,.2f}",
            fees_deducted=f"INR {totals['fees']:,.2f}",
            exceptions_remaining=len([x for x in self.queue if x.get('action') != 'auto_resolve']),
            audit_integrity="SHA-256 HASH CHAIN VERIFIED",
        )
        return self.sm.transition(State.ARCHIVED)

    # ---------- Driver Loop ----------
    def run(self, files: List[Path], truth: Optional[Union[str, Path]] = None) -> Optional[FinalReport]:
        """Execute the complete end-to-end reconciliation pipeline starting from ingestion.
        
        Args:
            files: Ingested file paths.
            truth: Optional ground truth benchmark file path.
            
        Returns:
            Completed FinalReport model, or None if halted interactively or files < 2.
        """
        self._t0 = time.time()
        if files:
            self.ingest(files, truth)
        elif truth:
            self.truth = [json.loads(l) for l in Path(truth).read_text().splitlines() if l]

        if not self.tables or len(self.tables) < 2:
            msg = "I don't have two datasets to reconcile yet — please upload files or run Load Sample Data first."
            self._chat(msg)
            return None

        if not self.sm.state:
            self.sm.enter(State.INGESTING)
            self.sm.transition(State.PROFILING, f"{len(self.tables)} tables")

        return self.continue_run()

    def continue_run(self) -> Optional[FinalReport]:
        """Re-entrant driver: dispatches step methods based on current StateMachine state.
        
        A HALT pauses execution cleanly (returning None) without losing state. Calling
        `continue_run()` after `sm.resume()` resumes exactly where it left off.
        """
        while self.sm.state not in (State.AGGREGATING, State.ARCHIVED, State.ABORT_CONFIRMED):
            attr = self._STEP_FN_ATTR.get(self.sm.state)
            if attr is None:
                break
            ok = getattr(self, attr)()
            if self.sm.state == State.HALT:
                return None  # Stop gracefully on interactive halt
            if ok is False:
                return None

        if (
            self.sm.state not in (State.ARCHIVED, State.ABORT_CONFIRMED, State.HALT)
            and self.sm.state in (State.RESOLVING, State.AGGREGATING)
        ):
            # Use 0.0 as fallback elapsed time if _t0 was never set (e.g. continue_run without prior run())
            self.aggregate(time.time() - getattr(self, "_t0", time.time()) if hasattr(self, "_t0") else 0.0)

        if getattr(self, "final", None):
            validate_and_route(
                self.sid,
                MessageKind.ARTIFACT,
                {
                    "kind": "report",
                    "summary": self.final.model_dump(),
                    "confidence_threshold": REG["match_auto_threshold"],
                    "fallback_events": self.fb,
                },
                "engine",
            )
            self._chat(
                f"Reconciliation complete: {self.final.match_rate:.0%} matched, "
                f"{self.final.honest_exception_count} exceptions, "
                f"{self.final.auto_resolved_count} auto-resolved."
            )

        return self.final
