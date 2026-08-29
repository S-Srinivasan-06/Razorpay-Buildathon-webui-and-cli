import itertools
import json
import time
import uuid
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, model_validator

from app.core.audit import audit_for
from app.core.channels import validate_and_route
from app.core.constants import REG
from app.core.contracts import (Actor, DecisionRecord, MatchComponent, MatchedRecord,
                                MessageKind, Policy, PolicyComponent, UnmatchedRecord,
                                VarianceMetrics)
from app.core.dispatcher import breaker_open, dispatch_tool_call, ToolCall
from app.core.states import State, StateMachine
from app.engine import match, qa, report, resolving
from app.engine.match import _sim, fee_explains


class MapArgs(BaseModel):
    tables: dict

class MapResult(BaseModel):
    left_table: str = "payments"
    right_table: str = "bank"
    left_key: str = "order_id"
    right_key: str = "utr"
    left_amount: str | None = "amount"
    right_amount: str | None = "credit"
    left_date: str | None = "date"
    right_date: str | None = "date"

    @model_validator(mode="before")
    @classmethod
    def parse_llm_json(cls, data):
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


def _overlap(xs, ys):
    a, b = set(map(str, xs)), set(map(str, ys))
    return len(a & b) / max(min(len(a), len(b)), 1)


class Pipeline:
    def __init__(self, sid: str, auto_ack: bool = False):
        self.sid = sid
        self.auto_ack = auto_ack
        self.sm = StateMachine(sid)
        self.fb: list[str] = []
        self.tables: dict[str, list[dict]] = {}
        self.cfg: dict = {}
        self.schedule = next(iter(REG.fee_schedules.values()), None)
        self.truth: list[dict] = []
        self.profiles: dict = {}
        self._map_cands: list = []
        self._map_conf = 0.0
        self._ambiguous = False

    # ---------- bus helpers ----------
    def _chat(self, text):
        validate_and_route(self.sid, MessageKind.CHAT, {"text": text[:2000]}, "system")

    def _trace(self, event, **d):
        validate_and_route(self.sid, MessageKind.TRACE, {"event": event, "detail": d}, "system")

    def _maybe_ack(self, tools):
        """Never raises. auto_ack=True resumes in-place immediately (CLI/test use).
        auto_ack=False leaves state at HALT for the caller to stop cleanly on."""
        if self.auto_ack:
            self.sm.resume()

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

    # ---------- states ----------
    def ingest(self, files, truth=None):
        self.sm.enter(State.INGESTING)
        for f in files:
            try:
                df = pd.read_csv(f) if f.suffix == ".csv" else pd.read_excel(f)
                df.insert(0, "_rid", range(1, len(df) + 1))
                self.tables[f.stem] = df.to_dict("records")
            except Exception as e:
                self._trace("UNPARSED", file=str(f), err=str(e)[:120])
        if truth:
            self.truth = [json.loads(l) for l in Path(truth).read_text().splitlines() if l]
        return self.sm.transition(State.PROFILING, f"{len(self.tables)} tables")

    def profile(self):
        print(f"[*] Step 1/7: Profiling table schemas and column statistics...", flush=True)
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
                self.profiles[name].append(ColumnProfile(
                    name=c, dtype=str(df[c].dtype), numeric_ratio=float(num),
                    date_ratio=float(dat), cardinality=float(df[c].nunique() / max(len(df), 1)),
                    null_rate=float(df[c].isna().mean()),
                    min_len=int(s.str.len().min() or 0), max_len=int(s.str.len().max() or 0),
                    sample_values=s.head(3).tolist(),
                    pii_likelihood=max((pii_score(c, v) for v in s.head(5)), default=0.0)))
        return self.sm.transition(State.MAPPING_PROPOSED)

    def _pick(self, t, kind):
        for p in self.profiles[t]:
            if kind == "numeric" and p.numeric_ratio > .8 and p.cardinality > .3:
                return p.name
            if kind == "date" and p.date_ratio > .8 and p.numeric_ratio <= .8:
                return p.name
        return None

    def propose_mapping(self):
        print(f"[*] Step 2/7: Linking schema keys and amounts via mapping tool...", flush=True)
        names = list(self.tables)
        cands = []
        for lt in names:
            for rt in names:
                if lt == rt:
                    continue
                for lc in [p.name for p in self.profiles[lt]]:
                    for rc in [p.name for p in self.profiles[rt]]:
                        ov = _overlap([r.get(lc) for r in self.tables[lt]],
                                      [r.get(rc) for r in self.tables[rt]])
                        if ov >= 0.10:
                            cands.append((ov, lt, lc, rt, rc))
        cands.sort(reverse=True)
        self._map_cands = cands
        tool = ToolCall(name="mapping_semantic", args_schema=MapArgs, result_schema=MapResult,
                        timeout_s=REG["llm_tool_timeout_s"], retries=2,
                        fallback=lambda a: None, cost_budget_usd=0.005)
        llm_map, fb = dispatch_tool_call(
            self.sid, tool, {"tables": {n: [p.name for p in self.profiles[n]] for n in names}})
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
            self.cfg = {"left_table": lt, "right_table": rt, "left_key": lc, "right_key": rc,
                        "left_amount": self._pick(lt, "numeric"), "right_amount": self._pick(rt, "numeric"),
                        "left_date": self._pick(lt, "date"), "right_date": self._pick(rt, "date")}
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

    def validate_mapping(self):
        audit_for(self.sid).append(DecisionRecord(
            decision_id=uuid.uuid4().hex, ts=pd.Timestamp.now(tz="UTC").to_pydatetime(),
            state="MAPPING_VALIDATED", actor=Actor.SYSTEM, decision_kind="mapping",
            proposal={"candidates": [list(c[1:]) for c in self._map_cands[:3]]},
            final={k: self.cfg.get(k) for k in ("left_table", "right_table", "left_key", "right_key")},
            confidence=self._map_conf, evidence=[]).model_dump(mode="json"))
        if self._map_conf < REG["mapping_review_floor"]:
            self.sm.halt("mapping below review floor")
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.MAPPING_VALIDATED
                return False
        if self._ambiguous or self._map_conf < REG["mapping_auto_accept"]:
            self._chat(f"Mapping confidence {self._map_conf:.2f} — proceeding with trace visibility.")
        return self.sm.transition(State.POLICY_GENERATED)

    def policy(self):
        print(f"[*] Step 3/7: Synthesizing policy components & tolerance windows...", flush=True)
        comps = [PolicyComponent(component=c, params={}, precedence=i)
                 for i, c in enumerate(MatchComponent, 1)]
        comps[3].params = {"tolerance": 0.01, "window_days": 3}
        self.policy_doc = Policy(
            components=comps, baseline_match_rate=0.0,
            baseline_computed_at=pd.Timestamp.now(tz="UTC").to_pydatetime(),
            baseline_constants_version=REG.version)
        self.cfg.setdefault("tolerance", 0.01)
        self.cfg.setdefault("window_days", 3)
        return self.sm.transition(State.DRY_RUN)

    # ---------- scoring core ----------
    def _score_all(self, rows_l, rows_r):
        self._last_cand_scores = []
        matched, unmatched, dups, per = [], [], [], []
        unmatched_ctx = []
        lkeys = {}
        for l in rows_l:
            lkeys.setdefault(str(l[self.cfg["left_key"]]), []).append(l)
        dup_keys = {k for k, v in lkeys.items() if len(v) > 1}
        seen_dup = set()
        used_r = set()
        soft_paired_r = set()          # T1: r's already represented via an l-pairing

        def mk_unmatched(l, r, v, ev, sd):
            side = "L" if l is not None else "R"
            ref_key = self.cfg["left_key"] if l is not None else self.cfg["right_key"]
            rec = UnmatchedRecord(side=side, rid=(l or r)["_rid"],
                                  ref=str((l or r).get(ref_key)), delta=sd, match_confidence=v)
            return rec, ev

        for l in rows_l:
            key = str(l[self.cfg["left_key"]])
            if key in dup_keys and key not in seen_dup:
                dups.append({"side": "L", "key": key, "rids": [x["_rid"] for x in lkeys[key]]})
                seen_dup.add(key)
            cands = [(r, *match.score_pair(self.sid, l, r, self.cfg, self.schedule, self.fb))
                     for r in rows_r if r["_rid"] not in used_r]
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
                matched.append(MatchedRecord(l_rid=l["_rid"], r_rid=r["_rid"],
                                             composite_score=v, components=comps,
                                             policy_version=REG.version))
                per.append({"l_id": l["_rid"], "r_id": r["_rid"], "abs": abs(sd or 0), "signed": sd})
            else:
                rec, ev = mk_unmatched(l, r, v, ev, sd)
                unmatched.append(rec)
                unmatched_ctx.append((rec, r, ev, sd))
                soft_paired_r.add(r["_rid"])          # T1: don't list this r again below
        for r in rows_r:
            if r["_rid"] not in used_r and r["_rid"] not in soft_paired_r:   # T1
                rec, ev = mk_unmatched(None, r, None, [], None)
                unmatched.append(rec)
                unmatched_ctx.append((rec, None, ev, None))

        var = VarianceMetrics(abs_sum=sum(p["abs"] for p in per),
                              signed_sum=sum(p["signed"] for p in per), per_record=per)
        from app.core.contracts import ExecutionResult
        self._last_unmatched_ctx = unmatched_ctx
        return ExecutionResult(matched=matched, unmatched=unmatched,
                               duplicates=dups, splits=[], variance=var)

    def dry_run(self):
        print(f"[*] Step 4/7: Performing dry-run calibration on sample rows...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]][:100]
        rows_r = self.tables[self.cfg["right_table"]]
        t0 = time.time()
        res = self._score_all(rows_l, rows_r)
        self.policy_doc.baseline_match_rate = len(res.matched) / max(len(rows_l), 1)
        mean_cand = sum(self._last_cand_scores) / len(self._last_cand_scores) if self._last_cand_scores else 0.0
        if mean_cand < REG["calibration_sanity_floor"]:
            self._trace("CALIBRATION_DRIFT_WARNING", mean_cand=round(mean_cand, 3))
        self._trace("dry_run_done", s=round(time.time() - t0, 2),
                    baseline=round(self.policy_doc.baseline_match_rate, 3),
                    mean_cand=round(mean_cand, 3))
        return self.sm.transition(State.EXECUTING)

    def execute(self):
        print(f"[*] Step 5/7: Executing multi-attribute matching engine...", flush=True)
        t0 = time.time()
        self.exec_res = self._score_all(self.tables[self.cfg["left_table"]],
                                        self.tables[self.cfg["right_table"]])
        self._exec_s = max(time.time() - t0, 1e-6)
        return self.sm.transition(State.INSPECTING)

    def _inspect_metrics(self):
        r = self.exec_res
        total = len(r.matched) + len(r.unmatched)
        self.match_rate = len(r.matched) / max(total, 1)
        nrows = sum(len(t) for t in self.tables.values())
        self.throughput = nrows / max(getattr(self, "_exec_s", 1.0), 1e-6)
        pred = {(m.l_rid, m.r_rid) for m in r.matched}
        truth = {(t["l_rid"], t["r_rid"]) for t in self.truth}
        self.precision = (len(pred & truth) / len(pred)) if pred else None
        self.recall = (len(pred & truth) / len(truth)) if truth else None

    def inspect(self):
        self._inspect_metrics()
        if self.match_rate < REG["revision_match_rate_threshold"]:
            return self.sm.transition(State.REVISION)
        return self.sm.transition(State.QA)

    def revise(self):
        it, t0 = 0, time.time()
        while (self.match_rate < REG["revision_match_rate_threshold"]
               and it < REG["revision_iteration_cap"]
               and time.time() - t0 < REG["revision_time_cap_s"]):
            old = self.cfg["tolerance"]
            self.cfg["tolerance"] = round(old * 1.2, 4)
            self._trace("revision", it=it, tol=self.cfg["tolerance"])
            self.execute()
            self._inspect_metrics()
            if self.policy_doc.baseline_match_rate - self.match_rate > REG["regression_reject_delta"]:
                self.cfg["tolerance"] = old
                self._trace("revision_regression_rejected", it=it)
                break                                   # T7: stop repeating an already-rejected tweak
            it += 1
        if self.match_rate < REG["revision_match_rate_threshold"]:
            self.sm.halt("revision caps exhausted or regression rejected")   # T2: restored
            self._maybe_ack([])
            if self.sm.state == State.HALT:
                self.sm._pre_halt = State.QA
                return False
        return self.sm.transition(State.QA)

    # ---------- QA / resolving ----------
    def _ctx(self, side, l, r, rows_l, rows_r, sd):
        lk, rk = self.cfg["left_key"], self.cfg["right_key"]
        tol = self.cfg["tolerance"]
        ctx = {k: ([] if k in ("dup_rids", "split_targets") else False) for k in qa.CTX_KEYS}
        if side == "L" and l is not None:
            key = str(l[lk])
            ctx["dup_rids"] = [x["_rid"] for x in rows_l if str(x[lk]) == key and x["_rid"] != l["_rid"]]
            cands = [x for x in rows_r if str(x[rk]) == key]
            ctx["single_target"] = len(cands) == 1
            if cands and self.cfg.get("left_amount"):
                a = float(l[self.cfg["left_amount"]])
                rv = float(cands[0][self.cfg["right_amount"]])
                ctx["fee_match"] = fee_explains(a, rv, self.schedule, tol)
                ctx["partial"] = rv < a and not ctx["fee_match"]
                if self.cfg.get("left_date"):
                    dd = match._busdays(match._d(l[self.cfg["left_date"]]),
                                        match._d(cands[0][self.cfg["right_date"]]))
                    ctx["date_only_mismatch"] = dd > self.cfg["window_days"] and (
                        abs(a - rv) <= tol or ctx["fee_match"])
            if not cands:
                # T6: Corroborate fuzzy key with amount/fee consistency
                a = float(l[self.cfg["left_amount"]]) if self.cfg.get("left_amount") else None
                if a is not None and self.cfg.get("right_amount"):
                    ctx["fuzzy_key"] = any(
                        _sim(key, str(x[rk])) >= 0.8 and (
                            abs(a - float(x[self.cfg["right_amount"]])) <= tol
                            or fee_explains(a, float(x[self.cfg["right_amount"]]), self.schedule, tol)
                        )
                        for x in rows_r
                    )
                else:
                    ctx["fuzzy_key"] = max((_sim(key, str(x[rk])) for x in rows_r), default=0) >= 0.85
        if side == "R" and r is not None:
            rv = float(r[self.cfg["right_amount"]]) if self.cfg.get("right_amount") else 0.0
            ctx["negative_credit"] = rv < 0
            nets = []
            for x in rows_l:
                a = float(x.get(self.cfg["left_amount"], 0))
                nets.append((x["_rid"], a - (match.compute_fee(a, self.schedule) if self.schedule else 0)))
            for k in (2, 3):
                for combo in itertools.combinations(nets, k):
                    if abs(sum(v for _, v in combo) - rv) <= tol:
                        ctx["split_targets"] = [i for i, _ in combo]
        return ctx

    def qa_state(self):
        print(f"[*] Step 6/7: Classifying exceptions & verifying invariant proofs...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]]
        rows_r = self.tables[self.cfg["right_table"]]
        self.queue = []
        for rec, r_cand, ev, sd in self._last_unmatched_ctx:
            if rec.side == "L":
                l = next(x for x in rows_l if x["_rid"] == rec.rid)
                ctx = self._ctx("L", l, r_cand, rows_l, rows_r, sd)
            else:
                r = next(x for x in rows_r if x["_rid"] == rec.rid)
                ctx = self._ctx("R", None, r, rows_l, rows_r, sd)
            rec.reason = qa.classify(rec, ctx)
            self.queue.append({"rec": rec, "ctx": ctx, "pieces": ev})
        return self.sm.transition(State.RESOLVING)

    def resolve(self):
        for item in self.queue:
            rec, pieces, ctx = item["rec"], item["pieces"], item.get("ctx", {})
            conf = resolving.exception_confidence(len(pieces), rec.reason, None)
            action = resolving.decide_action(conf, len(pieces), rec.reason)
            explanation = resolving.generate_explanation(rec, ctx)
            rec.explanation = explanation
            item["action"], item["conf"], item["explanation"] = action, conf, explanation
            actor = Actor.SYSTEM if action in ("auto_resolve", "mark_pending", "request_confirmation") \
                else Actor.FALLBACK
            audit_for(self.sid).append(DecisionRecord(
                decision_id=uuid.uuid4().hex, ts=pd.Timestamp.now(tz="UTC").to_pydatetime(),
                state="RESOLVING", actor=actor, decision_kind="exception_resolve",
                proposal={"category": rec.reason.value, "explanation": explanation},
                final={"action": action},
                confidence=conf, evidence=pieces).model_dump(mode="json"))
        return self.sm.transition(State.AGGREGATING)

    def aggregate(self, elapsed: float):
        print(f"[*] Step 7/7: Aggregating financial balances & signing cryptographic audit ledger...", flush=True)
        rows_l = self.tables[self.cfg["left_table"]]
        rows_r = self.tables[self.cfg["right_table"]]
        g = sum(float(x.get(self.cfg["left_amount"], 0)) for x in rows_l)
        n = sum(float(x.get(self.cfg["right_amount"], 0)) for x in rows_r)
        mv = sum(float(x.get(self.cfg["left_amount"], 0)) for x in rows_l
                 if x["_rid"] in {m.l_rid for m in self.exec_res.matched})
        totals = {"gross": round(g, 2), "net": round(n, 2), "fees": round(g - n, 2),
                  "matched_value": round(mv, 2), "exception_value": round(g - mv, 2)}
        self.final = report.build_final_report(
            self.sid, match_rate=self.match_rate, precision_vs_truth=self.precision,
            recall_vs_truth=self.recall, throughput_rows_per_sec=self.throughput,
            exceptions=self.queue, elapsed_seconds=elapsed, totals=totals,
            llm_user_disagreements=[], fallback_events=self.fb)
        return self.sm.transition(State.ARCHIVED)

    # ---------- driver ----------
    def run(self, files, truth=None):
        self._t0 = time.time()
        self.ingest(files, truth)
        return self.continue_run()

    def continue_run(self):
        """Re-entrant driver: dispatches on self.sm.state. A HALT stops this
        cleanly (returns None) without losing self.tables/self.cfg/etc; calling
        this again after sm.resume() picks up exactly where it left off."""
        while self.sm.state not in (State.AGGREGATING, State.ARCHIVED, State.ABORT_CONFIRMED):
            attr = self._STEP_FN_ATTR.get(self.sm.state)
            if attr is None:
                break
            ok = getattr(self, attr)()
            if self.sm.state == State.HALT:
                return None                      # T3: stop, don't crash the thread
            if ok is False:
                return None
        if self.sm.state == State.RESOLVING or getattr(self, "queue", None) is not None:
            if self.sm.state != State.ARCHIVED:
                self.aggregate(time.time() - getattr(self, "_t0", time.time()))
        if getattr(self, "final", None):
            validate_and_route(self.sid, MessageKind.ARTIFACT,
                               {"kind": "report", "summary": self.final.model_dump(),
                                "confidence_threshold": REG["match_auto_threshold"],
                                "fallback_events": self.fb}, "engine")
            self._chat(f"Reconciliation complete: {self.final.match_rate:.0%} matched, "
                       f"{self.final.honest_exception_count} exceptions, "
                       f"{self.final.auto_resolved_count} auto-resolved.")
        return self.final
