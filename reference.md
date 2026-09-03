# Full Codebase Bug Audit

I went through every file line-by-line. Below are the findings, ordered by severity.

---

## CRITICAL — Will crash at import/run time

### 1. Five Pydantic models are imported but never defined in `contracts.py`

`contracts.py` defines models ending at `FinalReport`. However, two other modules import models that **do not exist** in that file:

**`recon_agent/app/engine/journal.py` line 14:**
```python
from app.core.contracts import JournalEntry, JournalEntryLine   # ← neither exists
```

**`recon_agent/app/engine/multiway.py` lines 17-21:**
```python
from app.core.contracts import (
    CashPosition,       # ← does not exist
    FeeTaxRule,
    MultiWayLeg,        # ← does not exist
    MultiWayReport,     # ← does not exist
)
```

Any code path that imports `journal.py` or `multiway.py` will raise `ImportError`. Because `multiway.py` also imports `journal.py`, the entire multi-way chaining subsystem is dead on arrival.

**Fix:** Add these five models to `contracts.py`. Based on every constructor call in the codebase, they need these fields:

```python
class JournalEntryLine(BaseModel):
    account: str
    debit: float = 0.0
    credit: float = 0.0

class JournalEntry(BaseModel):
    je_id: str
    date: str
    description: str
    leg: str
    lines: List[JournalEntryLine]
    total_debit: float
    total_credit: float

class CashPosition(BaseModel):
    opening_balance: float
    gross_sales: float
    expected_settlements: float
    settled_in_bank: float
    in_transit_total: float
    in_transit_t1: float
    in_transit_t2: float
    in_transit_t7_plus: float
    fees_withheld: float
    gst_withheld: float
    refund_chargeback_reserve: float
    exception_value_at_risk: float
    projected_closing: float
    variance_unexplained: float

class MultiWayLeg(BaseModel):
    leg_name: str
    source_table: str
    target_table: str
    matched_count: int
    unmatched_count: int
    matched_value: float
    unmatched_value: float
    match_rate: float

class MultiWayReport(BaseModel):
    legs: List[MultiWayLeg]
    consolidated_match_rate: float
    total_orders_evaluated: int
    fully_reconciled_count: int
    pending_bank_clearing_count: int
    gateway_variance_count: int
    dropped_by_gateway_count: int
    direct_bank_charge_count: int
    cash_position: CashPosition
    journal_entries: List[JournalEntry]
```

---

### 2. Aborted pipeline can silently re-aggregate and reach ARCHIVED

**`pipeline.py`, `continue_run()`:**

```python
while self.sm.state not in (State.AGGREGATING, State.ARCHIVED, State.ABORT_CONFIRMED):
    ...
    if ok is False:
        return None          # ← abort exits here, state = ABORT_CONFIRMED

# post-loop:
if self.sm.state == State.RESOLVING or getattr(self, "queue", None) is not None:
    if self.sm.state != State.ARCHIVED:   # ← ABORT_CONFIRMED passes this check
        self.aggregate(...)               # ← runs on an aborted pipeline
```

If the pipeline is aborted mid-run, the state becomes `ABORT_CONFIRMED` and the queue may already be populated. A subsequent call to `continue_run()` (e.g. from the web UI "Resume" button) will skip the while-loop, hit the post-loop block, and call `aggregate()` — overwriting the abort with a completed report.

**Fix:**
```python
if self.sm.state not in (State.ARCHIVED, State.ABORT_CONFIRMED):
    self.aggregate(...)
```

---

## HIGH — Functional / correctness bugs

### 3. Hard-coded LLM model slug does not exist

**`llm_client.py`:**
```python
MODEL = "gemma-4-31b-it"

def resolve_model_slug(model_name: str = "") -> str:
    return "gemma-4-31b-it"      # always returns this, ignores env var
```

There is no `gemma-4-31b-it` in the Google Generative Language API. Every `json_chat` and `conversational_chat` call will get a 404/model-not-found error. The `LLM_MODEL` env var documented in `README.md` and `.env.example` is also never read — `resolve_model_slug` ignores its argument entirely.

**Fix:** Read `os.getenv("LLM_MODEL", "gemma-2-27b-it")` and pass it through `resolve_model_slug`.

---

### 4. Web UI "Remove File" only removes local state, not the server-side file

**`index.html`, `removeFile`:**
```javascript
window.removeFile = function (idx) {
    State.stagedFiles.splice(idx, 1);   // local array only
    renderStaged();
};
```

This never calls `DELETE /api/v2/sessions/{sid}/files/{filename}`. When the user clicks **Run Reconciliation** with no `rawFile` objects remaining (e.g. after loading sample data), the code calls `POST /run` with no body, which uses **all server-side staged files** — including the one the user "removed."

**Fix:** Add a `DELETE` call inside `removeFile`:
```javascript
window.removeFile = async function (idx) {
    const f = State.stagedFiles[idx];
    try { await fetchApi(`/sessions/${State.sid}/files/${encodeURIComponent(f.name)}`, {method:'DELETE'}); } catch(e){}
    State.stagedFiles.splice(idx, 1);
    renderStaged();
};
```

---

### 5. Split-solving inconsistency between global pass and per-record `_ctx`

**`pipeline.py`, `qa_state()`:**

The first pass builds `right_splits` with globally disjoint left-row allocations. The second pass then calls `self._ctx("R", ...)` for every right-side exception, which runs its **own** local combinatorial search:

```python
# inside _ctx, side == "R":
for k in (2, 3):
    for combo in itertools.combinations(pool, k):
        if abs(sum(v for _, v in combo) - rv) <= abs_tol:
            ctx["split_targets"] = [i for i, _ in combo]
```

A right record **not** in `right_splits` can still get `split_targets` from `_ctx`, causing `qa.classify` to label it `SPLIT` with a different combination than the global allocator would have chosen. This can produce conflicting split assignments across the exception queue.

**Fix:** In the second pass, skip the local `_ctx` split search for right records not in `right_splits`, or pass a flag to `_ctx` to suppress its own split search when global allocation has already been done.

---

## MEDIUM — Edge cases, race conditions, resource issues

### 6. `AuditLog` file handle is never closed

**`audit.py`:**
```python
self._fh = open(self.path, "a", encoding="utf-8")
# no __del__, no close(), no context manager
```

The file handle stays open for the lifetime of the process. Under long-running server use this leaks descriptors. Add `__del__` or make `AuditLog` a context manager.

---

### 7. Race condition on `RUN_RECONCILIATION`

**`actions.py`:**
```python
state_val = pipe.sm.state.value if pipe.sm.state else "IDLE"
if state_val in ACTIVE_RUN_STATES:
    raise ValueError("...already running.")
# ↓ gap: another request can also pass the check before this thread starts
threading.Thread(target=_work, daemon=True).start()
```

Two near-simultaneous requests can both read `IDLE`, both pass the guard, and both spawn pipeline threads. Add a threading lock or set state to `INGESTING` synchronously before spawning the thread.

---

### 8. `_busdays` is O(n) in calendar days

**`match.py`:**
```python
while cur < b:
    cur += datetime.timedelta(days=1)
    if cur.weekday() < 5:
        n += 1
```

For a 90-day window this loops 90 times per pair. With 10k rows × candidate pairs this adds up. Replace with `numpy.busday_count` or a closed-form weekday calculation.

---

### 9. State machine allows arbitrary transitions

**`states.py`:** `transition()` never validates whether the target state is reachable from the current state. A bug in any step method could jump from `INGESTING` directly to `ARCHIVED`, skipping all gates.

---

### 10. `journal.py` ignores `matched_pairs` and `exceptions` parameters in multiway path

**`multiway.py`:**
```python
journal_entries = generate_journal_entries(
    sid,
    matched_pairs=[],      # ← always empty
    exceptions=[],         # ← always empty
    totals=totals,
)
```

The suspense journal entries (JE 3 in `generate_journal_entries`) are never produced because `exceptions` is always `[]`. The multi-way report's journal entries will be missing suspense accruals for unresolved discrepancies.

---

## LOW — Minor / style / security

| # | Location | Issue |
|---|----------|-------|
| 11 | `llm_client.py` | API key is placed in the URL query string (`?key=...`), exposing it in proxy logs and browser history. Use a header instead. |
| 12 | `main.py` (v1 API) | `override()` only maps `"approve"` → `mark_resolved`, everything else → `escalate`. There is no `"decline"` path, inconsistent with v2. |
| 13 | `index.html` | Exception queue fetched with `page_size=1000`; sessions with >1000 exceptions silently truncate. |
| 14 | `masking.py` | Email regex lacks `$` anchor; `"user@example.com extra"` still scores 1.0 via `re.match`. Phone regex has `^...$`. Inconsistent anchoring. |
| 15 | `dispatcher.py` | `_breakers` dict grows unboundedly across sessions — no cleanup. |
| 16 | `fee.py` | `compute_fee` hard-codes a 0.9% debit-card cap (`Decimal("0.009")`), overriding whatever the fee schedule specifies. |
| 17 | `chatbot.py` | `_fallback_answer` hard-codes fallback defaults `sample_ref="ORD_1001"`, `actual_credit=976.40` which leak into responses if no differing pair is found in the data. |

---

## Summary

| Severity | Count | Key theme |
|----------|-------|-----------|
| **Critical** | 2 | Missing models (ImportError), abort→aggregate bypass |
| **High** | 3 | Invalid model slug, UI file-delete desync, split inconsistency |
| **Medium** | 5 | Resource leak, race condition, O(n) date math, unused params |
| **Low** | 7 | Security, consistency, hard-coded values |

The two **critical** items (#1 and #2) will prevent the multi-way engine from even importing and can corrupt an aborted session's final state. Those should be fixed first.

I did a full pass across the pipeline, fee/rule engine, chatbot/actions layer, REST API, and the static frontend. There's a real, high-impact bug at the center of the segment-rules feature, plus a second architectural gap (multi-file reconciliation) that's bigger than a bug — it's a whole engine that was built but never wired in. Here's everything, organized so you can work through it in order.

---

# PART 1 — BUGS (with root cause and fix)

## 🔴 CRITICAL — Segment rules silently misapplied to nearly every unmatched/displayed row

**Root cause:** `row_range_pct` matching (`matches_rule()` in `fee.py`) depends on a `row_idx` parameter that must be threaded in by the caller. It's only correctly passed in exactly **two** places:
- `pipeline.py::_score_all()` → `match.score_pair(..., row_idx=l_idx)` ✅
- `api_v2.py::line_matching()` → `compute_deduction_breakdown(..., row_idx=l_idx)` ✅

Everywhere else, `row_idx` is **omitted**, silently defaulting to `0`:
- `pipeline.py::_ctx()` — L-side fee/tax/fx evaluation (3 call sites)
- `pipeline.py::_ctx()` — R-side split-candidate net calculation
- `pipeline.py::qa_state()` — split-detection candidate pool building
- `api_v2.py::results()` — the Results Grid's per-row deduction breakdown

**Effect:** Any percentage-range rule ("first 20% get 2% fee, rest get 1.5%") gets applied correctly *only* during initial matching. The moment a row becomes an exception (QA phase) or is rendered in the Results Grid, it's evaluated as if it were **row 0** every time — meaning every unmatched row gets bucketed into whatever rule covers the start of the dataset, regardless of its real position. This directly breaks the exact "first 40% / rest 60%" scenario that's central to the redesign.

**Fix (two parts, do both):**
1. Make `row_range_pct` derive position from `row["_rid"]` instead of a separately-threaded index — this makes it self-correcting regardless of caller diligence:
```python
if k == "row_range_pct":
    rid = row.get("_rid")
    pos_idx = (int(rid) - 1) if rid is not None else row_idx
    curr_pct = (pos_idx / max(total_rows, 1)) * 100.0
    ...
```
2. Still pass `row_idx` explicitly everywhere for defense-in-depth and for `row_range_abs`/other matchers that might need it later. Add a unit test that builds a 100-row dataset with a 40%/60% split rule and asserts row 39 and row 41 get different rule labels **after** going through `_ctx()`/`results()`, not just `score_pair()` — this is the exact gap that let the bug ship undetected.

## 🔴 CRITICAL — Two disconnected reconciliation engines; 3+ file datasets silently drop a table

`pipeline.py`'s standard flow only ever picks **one** (left_table, right_table) pair via `propose_mapping()`'s highest-overlap heuristic — even when 3+ tables are staged. Any additional tables remain visible in Data Explorer and chat context but are **never reconciled**, with no warning to the user.

Meanwhile, a completely separate, fully-built 3-way engine (`multiway.py` + `journal.py`, with its own cash-position/aging/double-entry logic) exists specifically to handle this — but:
- No REST endpoint exposes it (`api_v2.py` has zero routes calling `run_multiway_chaining`)
- No UI surfaces it
- Not even the test suite exercises it directly

Telling evidence: `test_3file_benchmark_offline_truth` generates 3 files but calls `p.run([sales_file, bank_file])` — the test author had to **skip the third file** to make the standard pipeline work at all.

**Fix:** Pick one of two paths:
- **(A) Wire it in** — add `POST /sessions/{sid}/multiway-run`, have it call `detect_table_roles()` + `run_multiway_chaining()` when ≥3 tables are staged, and add a "Multi-Way Reconciliation" tab to the UI showing the leg-by-leg match rates, cash position, and journal entries (`export_journal_entries_csv` already exists and just needs a download route).
- **(B) Explicitly gate it off** — if you're not shipping multiway reconciliation yet, make the standard pipeline **refuse or warn** when >2 tables are staged for a run ("Detected 3 tables; only `sales` and `bank` will be reconciled — the third table `gateway` will be ignored)."

Silence is the one option that isn't acceptable, since it's currently losing data without telling anyone.

## 🔴 HIGH — Chat-triggered re-run of an already-completed reconciliation returns a stale cached report

`Pipeline.run()`:
```python
if not self.sm.state:
    self.sm.enter(State.INGESTING)
    self.sm.transition(State.PROFILING, ...)
return self.continue_run()
```
If `self.sm.state` is already `ARCHIVED` (i.e., this pipe already completed a run once) and `execute_agent_action("RUN_RECONCILIATION", ...)` calls `pipe.run([])` on the **same, reused** pipe object, `continue_run()`'s loop condition (`while state not in (AGGREGATING, ARCHIVED, ABORT_CONFIRMED)`) is already false — so nothing executes, and the stale `self.final` from the first run is returned silently. A user who says "reconcile again" via chat after a first run completed will get told it's done, but no new computation happens.

Compare: the REST `/sessions/{sid}/run` endpoint sidesteps this entirely by constructing a **fresh** `Pipeline(sid, auto_ack=True)` on every call — the chat path is the odd one out.

**Fix:** In `execute_agent_action`'s `RUN_RECONCILIATION` branch, if `pipe.sm.state in (State.ARCHIVED, State.ABORT_CONFIRMED)`, construct a fresh `Pipeline` that copies over `pipe.tables`, `pipe.rules`, `pipe.schedule`, and `pipe.cfg` (tolerance/mapping config) before calling `.run([])`, exactly mirroring what the REST endpoint does. Update `V2_SESSIONS[sid]["pipe"]` and the `ReconChatSession.pipe` reference to point at the new object (see next bug — this reference-sync problem shows up twice).

## 🟠 HIGH — Chat-configured rules/policy/tolerance can silently vanish if set before any file upload

`execute_agent_action()` creates a throwaway `Pipeline` if `pipe` is `None`, stores it in `V2_SESSIONS[sid]["pipe"]`, but **never updates `ReconChatSession.pipe`** (the caller's own reference). This is reachable: the natural-language rule-compiler branch and the confirmation "yes/no" handler both run *before* the "no active files" gate in `chat()`. So a user can say "first 20% have 2% fee, rest 1.5%" with zero files uploaded, confirm with "YES," and have it silently applied to an orphaned Pipeline that's discarded the instant they later upload real files (since `stage_analysis_files`/`load_sample` construct a brand-new Pipeline and reassign `pipe`).

**Fix:** Either (a) have `execute_agent_action` return the pipe object it used/created, and have `chat()` do `self.pipe = result["pipe"]` after every call, or (b) simplest — block SET_RULES/SET_POLICY/SET_TOLERANCE confirmation until at least one file is staged, with a clear message: *"Upload your data first, then I can apply this configuration to it."* Option (b) is safer and matches how the rest of the chat gating already works.

## 🟠 HIGH — Multiple `<action>` tags in one reply: only the last one is confirmable via plain "yes"

The multi-action parsing loop in `chat()` overwrites `self.pending_action` (singular) on every iteration. If the model emits two state-changing tags in one reply, both get a "Confirmation Required" message appended and both get stored in `self.pending_actions` (plural, by token), but the simple "reply YES" flow only ever checks `self.pending_action`, so only the **last** proposed action is actually executable that way. This directly contradicts the "one turn may emit multiple actions" design goal from the previous spec.

**Fix:** Either queue all pending actions and have "yes" confirm them in order, or explicitly tell the user in the confirmation text: *"Reply YES to confirm the last action above, or use the confirmation link for the others."* Cleanest fix: make `pending_action` a list, and have the confirmation handler iterate and execute all of them, auditing each individually.

## 🟠 HIGH — "AI can propose rule structures" is only true via a brittle regex layer, not the actual LLM

`build_grounded_context()`'s action vocabulary (what the model is told it *can* do) lists only `RUN_RECONCILIATION`, `SET_POLICY`, `SET_TOLERANCE`, `VERIFY_TAX`, `VERIFY_CHARGES` — **there is no `ADD_RULE`/`SET_RULES` action tag the LLM can emit.** Segment rules can only ever be created through a hand-rolled `re.search`/`re.finditer` pre-processor that runs *before* the LLM is even called, triggered by hardcoded substrings including the literal string `"for electronics"` (a placeholder that clearly should have been generalized, not shipped).

This means: if you have a real Gemini/Gemma API key configured and ask the model something slightly outside the regex's narrow phrasing (e.g., "apparel should be taxed at 12%" instead of "for category apparel tax is 12%"), the actual LLM never gets a chance to help — it falls through to plain conversational chat with no way to act.

**Fix:** Two changes:
1. Add `<action>ADD_RULE:...</action>` (or better, a structured JSON tool call) to the vocabulary in `build_grounded_context()`.
2. Wire `rule_compiler.compile_rules_from_text` as a real `ToolCall` through the existing `dispatch_tool_call()` pattern (the same one already used for `mapping_semantic`/`semantic_similarity`) so the actual configured LLM does the interpretation with structured-output validation, and the regex parser becomes the **fallback** (used only when the LLM is unreachable), not the primary path. This is the single most important fix for actually satisfying "the AI should interpret this," since right now the AI mostly doesn't.

## 🟡 MEDIUM — Rule compiler can invert user intent on reordered ranges

`compile_rules_from_text`'s percentage-range regex captures words like "first"/"next"/"last"/"remaining" but never inspects them — ranges are assigned strictly by order of appearance in the text. "Last 20% get X, first 80% get Y" would incorrectly assign the "last 20%" clause to the range 0%–20%.

**Fix:** Either explicitly special-case "last"/"remaining" to anchor from the end of the range, or — simpler and safer — detect this ambiguity and ask for clarification rather than guessing, consistent with the ambiguity-halt pattern already used elsewhere.

## 🟡 MEDIUM — `set_policy()` silently wipes any previously configured segment rules

`Pipeline.set_policy()` unconditionally does `self.rules = [policy_rule]`. If a user configured detailed segment rules via chat and then adjusts the flat "Fee/MDR %" input in the UI and clicks "Save & Apply," all segment rules are destroyed without warning.

**Fix:** Either disable/hide the flat policy panel once segment rules are active (show "Segment rules are active — clear them to use the flat policy panel" instead), or have `set_policy()` add its rule with the lowest priority instead of replacing the list outright, and warn the user in the response payload.

## 🟡 MEDIUM — "Remove file" button doesn't call the delete endpoint

`window.removeFile(idx)` in the frontend only does `State.stagedFiles.splice(idx, 1)` — a **local array splice**. It never calls `DELETE /sessions/{sid}/files/{filename}`. The file remains staged server-side (`pipe.tables`, `sess["files"]`) even though the UI shows it removed. If the user then clicks "Run," the "removed" file may still be included.

**Fix:** `removeFile` must call the DELETE endpoint and only splice the array on success.

## 🟡 MEDIUM — Journal engine hardcodes 18% GST regardless of actual rules used

`journal.py::generate_journal_entries` computes `base_fee = round(total_fees / 1.18, 2)` unconditionally — this silently assumes every fee included exactly 18% GST, which is wrong the instant any segment rule uses a different rate (0%, 5%, 12%, 28%, or a mix). Low severity only because this engine is currently unreachable (see multiway gap above) — but must be fixed before wiring it in.

**Fix:** Compute `base_fee`/`gst_itc` from the actual per-rule breakdown totals (sum of `gateway_fee` and `gst` fields already returned by `compute_deduction_breakdown`), not a hardcoded division.

## 🟢 MINOR / cleanup items
- `pipeline.py::qa_state()` has a literal duplicate `return self.sm.transition(State.RESOLVING)` — dead code, delete the second line.
- `multiway.py`'s cash-position "invariant assertion" compares a formula against the exact same formula — it can never fail and verifies nothing. Replace with a genuinely independent cross-check (e.g., against `gross_sales - fees_withheld - gst_withheld - exception_value_at_risk`).
- `SET_POLICY` chat-action payload defaults `gst_rate` to `0.18` and the REST `PolicyUpdateRequest` Pydantic model does the same — both contradict the "zero by default" requirement whenever a caller omits the field. Default to `0.0`.
- The "Fee Schedule & Tax Tolerance" UI panel's inputs are pre-filled `2.0` / `18.0` on page load. The backend genuinely starts at zero fee/tax until the user clicks "Save & Apply," so this is cosmetic — but it visually implies a schedule is already active when it isn't. Pre-fill with `0.0`/`0.0` or add a "No fee/tax configured" indicator instead.
- `resolve_model_slug(model_name: str = "")` still accepts a parameter it now ignores entirely (model is hardcoded) — harmless but vestigial; drop the parameter.
- `execute_agent_action` reaching into `app.server.api_v2.V2_SESSIONS` from inside `app/engine/actions.py` is a layering violation (engine importing server internals). Works today via deferred import, but is fragile — consider passing a session-registry callback instead.

---

# PART 2 — UI ⇄ Backend Parity Audit

Every REST endpoint in `api_v2.py`, cross-checked against whether the shipped `index.html` actually calls it.

| Endpoint | Called by frontend? | Notes |
|---|---|---|
| `POST /sessions` | ✅ | |
| `GET /overview` | ✅ | |
| `GET /ingestion` | ✅ | |
| `GET /mapping` | ✅ | |
| `GET /policy` | ❌ | Never fetched — form fields aren't pre-populated from server state on load |
| `POST /policy` | ✅ | |
| `GET /tolerance` | ❌ | Same issue — no pre-population |
| `POST /tolerance` | ✅ | |
| `GET /rules` | ❌ | **No UI at all for viewing active rules** |
| `POST /rules` | ❌ | **No UI at all for adding/editing rules directly** — only reachable via chat |
| `POST /confirm-action/{token}` | ❌ | Confirmation is chat-text-only ("type YES"); no button UI exists |
| `GET /results` | ✅ | |
| `GET /exceptions` | ✅ | |
| `POST /exceptions/{rid}/action` | ✅ | |
| `POST /exceptions/bulk-action` | ❌ | No multi-select checkboxes in the exceptions list |
| `GET /audit` | ✅ | |
| `GET /export.csv` | ✅ | |
| `GET /export/report.json` | ❌ | No download link/button |
| `GET /export/audit.jsonl` | ❌ | No download link/button |
| `GET /trace` | ✅ | |
| `GET /logs` | ❌ | Only `/trace` is polled |
| `POST /files` | ✅ | |
| `DELETE /files/{filename}` | ❌ | **Bug** — see above, UI removes locally but never calls this |
| `GET /line-matching` | ✅ | |
| `POST /load_sample` | ✅ | Hardcoded to only the base 2-file demo — `clean_demo/`, `benchmark_3file/`, `enterprise_ecosystem/` are unreachable from the UI |
| `POST /run` | ✅ | |
| `POST /resume` | ❌ | **No "Resume" control** — if a run HALTs, the UI shows a status dot and nothing else |
| `POST /restart` | ❌ | No "restart session" control |
| `POST /abort` | ✅ | |

**Summary: 11 of 27 endpoints have zero frontend wiring.** The most consequential missing pieces:
1. **No rules management UI** — the core "user can add any tax, any charge dynamically" requirement from the redesign has a fully working backend (`GET`/`POST /rules`) and *no UI surface for it at all* outside of chat prose.
2. **No resume/restart controls** — a halted pipeline has no way to be un-stuck from the UI.
3. **No confirmation-button UI** — every state-changing chat action requires typing "yes," even though the backend already built a proper token-based confirm endpoint for exactly this purpose.
4. **Sample dataset picker missing** — three demo dataset folders exist on disk (`clean_demo`, `benchmark_3file`, `enterprise_ecosystem`) with zero way to load them from the running app.

---

# PART 3 — Unused Endpoints: Recommendation

You asked to remove unused endpoints if there aren't any real uses for them — but in this case, **every one of the 11 unused endpoints represents a real, needed capability that's simply missing its UI**, not dead functionality that should be deleted. My recommendation is the opposite of removal:

| Endpoint | Recommended action |
|---|---|
| `GET /policy`, `GET /tolerance` | Wire into page load / session-switch so the form pre-populates instead of always showing defaults |
| `GET /rules`, `POST /rules` | **Build a "Fee & Tax Rules" panel** — table of active rules (label, matcher description, fee%, tax%, priority) with an "Add Rule" form (matcher type dropdown → conditional fields, fee/tax inputs) and a delete/clear-all control. This is the single highest-priority UI gap. |
| `POST /confirm-action/{token}` | Surface pending chat actions as an inline confirm/cancel button pair in the chat drawer instead of requiring typed "yes" |
| `POST /exceptions/bulk-action` | Add checkboxes to the exception list + a bulk approve/decline toolbar |
| `GET /export/report.json`, `GET /export/audit.jsonl` | Add two more buttons next to "Export CSV" |
| `GET /logs` | Optional — add a "Debug Logs" tab if useful for support/debugging; otherwise fine to leave unused |
| `DELETE /files/{filename}` | Fix `removeFile()` to actually call this (bug fix, not a UI addition) |
| `POST /resume` | Add a "Resume" button that appears when status is HALTED |
| `POST /restart` | Add a "Restart Session" button, probably in the sidebar near "Active Session" |
| `POST /load_sample` variants | Extend to a dropdown: "Basic Demo / Clean Demo / 3-File Benchmark / Enterprise Ecosystem" |

If after reviewing this you decide some of these genuinely aren't needed for your use case (e.g., bulk actions, or the extra sample datasets), it's fine to leave those specific ones unused — but I'd keep the endpoints rather than delete them, since removing working backend code to match an incomplete frontend is the wrong direction to fix a parity gap.

---

# PART 4 — Suggested Fix Order

1. Fix the `row_idx` bug (Part 1, item 1) — this silently breaks the core feature you asked for.
2. Decide multiway engine's fate: wire it in or explicitly gate 3+ file uploads (item 2).
3. Fix chat re-run staleness and pipe-reference sync (items 3–4) — both stem from the same root cause (chat actions operating on/creating pipe objects that don't get synced back).
4. Wire `rule_compiler` as a real LLM tool call, not just a regex pre-filter (item 6) — this is what actually makes "the AI interprets this" true.
5. Build the Rules Management UI panel — closes the biggest UI/backend gap.
6. Add resume/restart/confirm-action UI controls.
7. Fix `removeFile()` to call DELETE.
8. Sweep the minor/cleanup items (dead code, hardcoded 18% GST in journal, default-value inconsistencies).



# Verification: Yes — these are real bugs. Your analysis is accurate and thorough.

I re-checked every claim against the source. Below is my per-item verdict, plus a few things you missed and one nuance worth flagging.

---

## PART 1 — Bug-by-bug confirmation

### 🔴 #1: `row_idx` threading — **CONFIRMED, and your call-site inventory is exact**

I traced every `compute_deduction_breakdown` call that passes `rules=`:

| Call site | `row_idx` passed? |
|---|---|
| `_score_all()` → `score_pair(row_idx=l_idx)` | ✅ |
| `api_v2.py::line_matching()` (deduction mode) | ✅ `row_idx=l_idx` |
| `actions.py` VERIFY_TAX / VERIFY_CHARGES | ✅ `row_idx=idx` |
| `_ctx()` L-side deductions | ❌ omitted → defaults 0 |
| `_ctx()` R-side split-pool net calc | ❌ omitted → defaults 0 |
| `_ctx()` → `fee_explains()` in fuzzy-key check | ❌ omitted → defaults 0 |
| `qa_state()` split-pool building | ❌ omitted → defaults 0 |
| `api_v2.py::results()` per-row breakdown | ❌ omitted → defaults 0 |

Your fix (derive from `row["_rid"]`) is the right primary fix, **but** one wrinkle: in `api_v2.py::results()`, the row dict is stripped of `_rid` before being passed:

```python
l_d = {k: v for k, v in l_rows.get(m.l_rid, {}).items() if not k.startswith("_")}
```

So `_rid` won't be present there. You'll need to pass `row_idx=m.l_rid - 1` explicitly at that site, or include `_rid` in `l_d`. Your defense-in-depth suggestion (pass explicitly everywhere) covers this.

### 🔴 #2: Multiway engine unwired — **CONFIRMED**

- Zero routes in `api_v2.py` reference `run_multiway_chaining`.
- Zero tests call it.
- `test_3file_benchmark_offline_truth` literally generates `gw_file` and never uses it: `p.run([sales_file, bank_file])`.
- `pipeline.py::run()` has no guard for `len(self.tables) > 2` — it silently proceeds with the best pair from `propose_mapping()`.

Your framing is right: this is an architectural gap, not a logic bug. But the *silent* part is the bug — data is ingested, shown in the explorer, then never reconciled, with no user-facing notice.

### 🔴 #3: Stale re-run via chat — **CONFIRMED**

The exact code path:
```python
# pipeline.py run()
if not self.sm.state:          # ARCHIVED is truthy → skipped
    self.sm.enter(State.INGESTING)
    self.sm.transition(State.PROFILING, ...)
return self.continue_run()     # loop condition already false → returns stale self.final
```

And the REST `/run` endpoint does create a fresh `Pipeline(sid, auto_ack=True)` every time, so the asymmetry is real. The chat path reuses the same pipe object.

### 🟠 #4: Orphaned pipe / lost rules — **CONFIRMED**

Traced the full lifecycle:
1. `chat()` creates `self.pipe = Pipeline(...)` locally when None
2. `execute_agent_action(self.sid, self.pipe, ...)` — pipe is not None, so `V2_SESSIONS[sid]["pipe"]` is **never updated**
3. `stage_analysis_files()` does `pipe = sess.get("pipe") or Pipeline(...)` → creates a **brand new** Pipeline
4. `CHAT_SESSIONS[sid].set_pipe(pipe)` → replaces `self.pipe`
5. Rules applied in step 2 are gone

Your option (b) — block rule/policy/tolerance actions until files are staged — is the safer fix and matches the existing gating pattern.

### 🟠 #5: Multiple `<action>` tags — **CONFIRMED**

```python
for action_match in re.finditer(...):
    ...
    self.pending_action = {"kind": action_kind, ...}   # overwritten each iteration
    self.pending_actions[token] = self.pending_action   # dict keeps all
```

The "YES" handler only reads `self.pending_action` (singular). So with two state-changing actions in one reply, only the last is confirmable by text. The `pending_actions` dict and the REST `confirm-action/{token}` endpoint exist but have no UI path.

### 🟠 #6: Rule creation is regex-only — **CONFIRMED**

- `build_grounded_context()` vocabulary: `RUN_RECONCILIATION`, `SET_POLICY`, `SET_TOLERANCE`, `VERIFY_TAX`, `VERIFY_CHARGES`. No `ADD_RULE` / `SET_RULES` tag.
- Trigger list includes the literal `"for electronics"` — clearly a placeholder.
- `compile_rules_from_text` is called *before* the LLM, not as an LLM tool. Your recommendation to wire it through `dispatch_tool_call()` as a proper `ToolCall` with the regex as fallback is the correct architecture — it mirrors the existing `mapping_semantic` / `semantic_similarity` pattern.

### 🟡 #7: Reordered ranges invert intent — **CONFIRMED**

```python
r"(?:first|next|remaining|last)?\s*(\d+...)..."
```
The `(?:first|next|remaining|last)?` group is captured but never inspected. Ranges are assigned strictly by match order. "Last 20% get X, first 80% get Y" → 0–20% gets X, 20–100% gets Y.

### 🟡 #8: `set_policy()` wipes rules — **CONFIRMED**

```python
self.rules = [policy_rule]   # unconditional replace
```

### 🟡 #9: `removeFile()` doesn't call DELETE — **CONFIRMED** (I flagged this independently in my prior audit)

### 🟡 #10: Journal hardcodes `/1.18` — **CONFIRMED**

```python
base_fee = round(total_fees / 1.18, 2)
```
Currently unreachable (see #2), but will break the moment multiway is wired in with non-18% rules.

### 🟢 Minor items — all confirmed

- Duplicate `return self.sm.transition(State.RESOLVING)` in `qa_state()` — dead code, second line unreachable.
- `multiway.py` invariant asserts a formula against itself — tautological, can never fail.
- `gst_rate: float = 0.18` defaults in both `PolicyUpdateRequest` and the chat payload parser — contradicts zero-default mandate.
- `resolve_model_slug(model_name)` ignores its parameter — vestigial.
- `actions.py` importing `V2_SESSIONS` from `app.server.api_v2` — layering violation, works via deferred import but fragile.

---

## Things your audit missed

### A. `declined` action creates a counting inconsistency between v1 and v2 APIs

In `api_v2.py::exception_action()`:
```python
pipe.final.unresolved_count = sum(
    1 for e in pipe.queue if e.get("action") in ("mark_pending", "declined")
)
```

But in `report.py::build_final_report()`:
```python
unresolved_count=sum(1 for e in exceptions if e.get("action") == "mark_pending"),
```

And in the v1 `main.py::override()`:
```python
pipe.final.unresolved_count = sum(1 for e in pipe.queue if e.get("action") == "mark_pending")
```

So `declined` is counted in `unresolved_count` by the v2 API but **not** by `report.py` or the v1 API. In practice this doesn't cause a runtime crash because `decide_action()` never returns `"declined"` (it's only set by user overrides), and the report counts are updated in-place after overrides rather than rebuilt. But if `build_final_report()` is ever called again after overrides (e.g., on a re-run), the sum invariant `auto + escalated + unresolved == honest_total` will break. Add `"declined"` to `report.py`'s `unresolved_count` filter for consistency.

### B. `_ctx()` fuzzy-key `fee_explains` call also omits `row_idx`

You listed "3 call sites" in `_ctx()` — the third is the `fee_explains(...)` call inside the fuzzy-key comprehension:
```python
or fee_explains(a, float(x[...]), schedule=self.schedule, tol=row_tol,
                rules=self.rules, row=l, total_rows=len(rows_l))
```
`fee_explains` passes `row_idx` through to `compute_deduction_breakdown`, but since the caller doesn't supply it, it defaults to 0. Same class of bug, just confirming it's in your count.

### C. `chatbot.py::_fallback_answer` hardcodes `sample_ref="ORD_1001"`, `actual_credit=976.40`

If no differing pair is found in the loaded data (e.g., all amounts match exactly), the custom-policy simulation falls back to these hardcoded values from the base demo dataset. This leaks demo-specific numbers into responses for arbitrary user data.

### D. `pipeline.py::aggregate()` calls `time.time() - getattr(self, "_t0", time.time())`

If `_t0` was never set (e.g., `continue_run()` is called without a prior `run()`), the elapsed time is `time.time() - time.time() = 0.0`. Minor, but the fallback should probably be `0.0` explicitly rather than `time.time()`.

---

## PART 2 — Parity audit: accurate

I spot-checked every "not called" claim against the JavaScript. All 11 are correct. The four most consequential gaps you identified (no rules UI, no resume/restart, no confirm buttons, no dataset picker) are the right priorities.

One addition: the `POST /load_sample` endpoint hardcodes only `payments.csv` and `bank.csv`:
```python
sample_names = ["payments.csv", "bank.csv"]
```
The three other demo folders (`clean_demo`, `benchmark_3file`, `enterprise_ecosystem`) have zero loading path from any endpoint.

---

## PART 3 — Agreed: keep the endpoints, build the UI

Removing working backend to match an incomplete frontend is backwards. The 11 unused endpoints represent real capabilities that need UI, not dead code.

---

## PART 4 — Fix order: one adjustment

Your order is sound. I'd insert the `declined` counting fix (item A above) into the sweep at step 8, and I'd swap steps 3 and 4:

1. Fix `row_idx` (silent data corruption — highest priority)
2. Decide multiway fate (wire or gate)
3. **Wire `rule_compiler` as LLM tool call** (this unblocks the core "AI interprets rules" requirement)
4. Fix chat re-run staleness + pipe-reference sync (items 3–4)
5. Build Rules Management UI panel
6. Resume / restart / confirm-action UI
7. Fix `removeFile()`
8. Sweep: dead code, journal `/1.18`, `declined` counting, default values, hardcoded chatbot fallbacks, `resolve_model_slug` cleanup, layering violation

The rationale for swapping 3↔4: the rule-compiler-as-LLM-tool is the feature that makes "the AI interprets this" actually true, and it's referenced by the Rules UI (step 5). The pipe-sync bugs are real but lower-impact since they only manifest in specific chat-before-upload sequences.

---

**Bottom line:** Your audit is accurate on every substantive point. The `row_idx` bug is the most dangerous because it silently corrupts the core feature. The multiway gap is the most visible. Everything else is real and correctly diagnosed.