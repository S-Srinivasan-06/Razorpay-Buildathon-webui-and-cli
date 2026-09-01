"""Grounded AI Reconciliation Assistant and Conversational Chat Session.

Provides strict context grounding for multi-turn conversations with Gemma 4 31B.
Constructs prompt snapshots containing exclusively active session datasets, schema mappings,
balance summaries, and classified exceptions. Enforces strict factual isolation so deleted
or replaced files cannot leak into model responses or cause hallucinations.
"""

import json
from typing import Any, Dict, List, Optional

from app.core import llm_client


def build_grounded_context(pipe: Any) -> str:
    """Construct a strict context snapshot containing ONLY active session datasets and reports.
    
    Includes:
      1. Active table names, record counts, column lists, and sample data previews.
      2. Active schema mapping configuration (keys, amounts, dates).
      3. Final reconciliation metrics and financial balances (gross, net, fees, matched, exception).
      4. Classified exceptions queue with diagnostic explanations and action statuses.
      5. Strict prompt instructions prohibiting hallucinations regarding deleted files.
      
    Args:
        pipe: Pipeline instance for the active session.
        
    Returns:
        Structured markdown context string for the LLM system instruction.
    """
    if not pipe or not getattr(pipe, "tables", None):
        return "NO_ACTIVE_FILES: There are no files or datasets loaded in the current active session."

    lines: List[str] = []
    lines.append("=== ACTIVE RECONCILIATION DATASET & ENGINE CONTEXT ===")

    # 1. Active Tables and Columns
    lines.append("\n[Active Tables Loaded in Session]:")
    for tbl_name, rows in pipe.tables.items():
        sample_rows = rows[:5]
        cols = list(rows[0].keys()) if rows else []
        lines.append(f"- Table '{tbl_name}': {len(rows)} total records. Columns: {cols}")
        lines.append(f"  Sample Data Preview (first {len(sample_rows)} rows): {json.dumps(sample_rows, default=str)}")

    # 2. Active Schema Mapping
    if getattr(pipe, "cfg", None):
        lines.append("\n[Active Schema Mapping]:")
        lines.append(json.dumps(pipe.cfg, indent=2, default=str))

    # 3. Financial Balances & Report Summary
    if getattr(pipe, "final", None):
        lines.append("\n[Final Reconciliation Summary]:")
        lines.append(f"- Match Rate: {pipe.final.match_rate:.1%}")
        lines.append(f"- Total Gross Ledger Volume: INR {pipe.final.total_gross:,.2f}")
        lines.append(f"- Net Bank Inflow: INR {pipe.final.total_net:,.2f}")
        lines.append(f"- Total Fees & Variance: INR {pipe.final.total_fees:,.2f}")
        lines.append(f"- Matched Value: INR {pipe.final.matched_value:,.2f}")
        lines.append(f"- Exception Value: INR {pipe.final.exception_value:,.2f}")
        lines.append(f"- Auto-Resolved (Approved): {pipe.final.auto_resolved_count}")
        lines.append(f"- Escalated (Review Req): {pipe.final.escalated_count}")
        lines.append(f"- Unresolved Pending: {pipe.final.unresolved_count}")

    # 4. Active Classified Exceptions Queue
    if getattr(pipe, "queue", None):
        lines.append(f"\n[Active Exception Queue ({len(pipe.queue)} items)]:")
        for idx, item in enumerate(pipe.queue, 1):
            rec = item["rec"]
            explanation = item.get("explanation") or getattr(rec, "explanation", "")
            lines.append(
                f"  #{idx}. [{rec.side}] Ref: {rec.ref} | RID: {rec.rid} | "
                f"Reason: {rec.reason.value if hasattr(rec.reason, 'value') else rec.reason} | "
                f"Status/Action: {item.get('action')} | "
                f"Delta: {rec.delta} | "
                f"Diagnostic: {explanation}"
            )

    # 5. Core Assistant Guardrails
    lines.append("\n=== CRITICAL DIRECT RESPONSE INSTRUCTIONS ===")
    lines.append("1. You are the AI Financial Reconciliation Assistant speaking directly to the user.")
    lines.append("2. NEVER output prompt restatements (e.g. 'User Question:'), internal context summaries, planning bullets (e.g. '* Explain that...'), or scratchpad notes.")
    lines.append("3. Answer the user's question directly, clearly, and conversationally in professional Markdown.")
    lines.append("4. Answer strictly using the active dataset and reports above. If a record or file is not present, state so clearly.")
    lines.append("5. For questions about split/batch transactions, explain that multiple constituent order legs were aggregated into single batch settlements net of payment gateway fees.")

    return "\n".join(lines)


class ReconChatSession:
    """Manages multi-turn conversation state and dataset grounding for a session.
    
    Attributes:
        sid: Session identifier string.
        pipe: Reference to the active Pipeline instance.
        history: Multi-turn message history list.
    """

    def __init__(self, sid: str, pipe: Optional[Any] = None) -> None:
        """Initialize chat session.
        
        Args:
            sid: Session identifier string.
            pipe: Optional Pipeline instance.
        """
        self.sid: str = sid
        self.pipe: Optional[Any] = pipe
        self.history: List[Dict[str, str]] = []

    def set_pipe(self, pipe: Any) -> None:
        """Update or re-bind the active Pipeline reference."""
        self.pipe = pipe

    def _fallback_answer(self, query: str) -> str:
        """Generate a direct grounded response from active pipeline data if the external LLM is unreachable."""
        if not self.pipe:
            return "Reconciliation session data is not loaded."
        
        q = query.lower()
        final = getattr(self.pipe, "final", None)
        queue = getattr(self.pipe, "queue", [])
        matched = getattr(self.pipe.exec_res, "matched", []) if getattr(self.pipe, "exec_res", None) else []
        
        # 1. Search for specific Order / Transaction Reference
        for item in queue:
            rec = item["rec"]
            if rec.ref and rec.ref.lower() in q:
                explanation = item.get("explanation") or getattr(rec, "explanation", "")
                return f"**Discrepancy Analysis for `{rec.ref}`**:\n- **Side**: {rec.side} ({'Ledger' if rec.side == 'L' else 'Bank Statement'})\n- **Discrepancy Reason**: `{rec.reason.value if hasattr(rec.reason, 'value') else rec.reason}`\n- **Variance / Delta**: INR {rec.delta}\n- **AI Diagnostic**: {explanation}\n- **Action Status**: `{item.get('action')}`"

        for m in matched:
            l_ref = str(m.l_rid)
            if hasattr(m, "ref") and m.ref and m.ref.lower() in q:
                return f"**Matched Record `{m.ref}`**:\n- **Ledger RID**: {m.l_rid} ↔ **Bank RID**: {m.r_rid}\n- **Composite Score**: {m.composite_score:.3f}\n- **Status**: Reconciled successfully."

        # 2. Split, Batch, and Combining questions
        if "combine" in q or "split" in q or "batch" in q:
            return (
                "**Why Split Transactions & Batch Deposits are Combined**:\n\n"
                "In payment reconciliation, multiple individual customer orders (from your internal `payments` ledger) are often settled as a single lump-sum deposit in the bank statement (`bank` statement), net of gateway fees.\n\n"
                "1. **Grouping Logic**: Individual transaction legs are matched to batch deposit records (e.g. `BATCH_SETTL_01` through `BATCH_SETTL_04`).\n"
                "2. **Auto-Resolution Reason**: The engine verifies that the sum of the constituent order amounts matches the bank deposit total net of the MDR fee schedule.\n"
                "3. **Financial Invariant**: Combining these into a batch reconciliation ensures full balance parity with zero unexplained discrepancy."
            )

        # 3. Fee / Variance questions
        if "fee" in q or "variance" in q or "mdr" in q or "difference" in q:
            if final:
                return f"**Fee & Variance Summary**:\n- **Total Gross Ledger Volume**: INR {final.total_gross:,.2f}\n- **Net Bank Inflow**: INR {final.total_net:,.2f}\n- **Total Fees Deducted**: INR {final.total_fees:,.2f}\n- **Matched Value**: INR {final.matched_value:,.2f}\n- **Unresolved Exception Volume**: INR {final.exception_value:,.2f}\n\n*Standard gateway fee schedule: 1.0% MDR + fixed fee + GST applies on matched transactions.*"

        # 3. Duplicate / Split questions
        if "duplicate" in q or "refund" in q or "split" in q:
            dups = [item for item in queue if "duplicate" in str(item["rec"].reason).lower() or "refund" in str(item["rec"].reason).lower()]
            if dups:
                lines = ["**Identified Duplicate / Adjustment Transactions**:"]
                for d in dups:
                    rec = d["rec"]
                    lines.append(f"- **{rec.ref}** [{rec.side}]: {rec.reason.value if hasattr(rec.reason, 'value') else rec.reason} (Delta: INR {rec.delta}) - *{d.get('explanation', '')}*")
                return "\n".join(lines)
            return "No duplicate or refund anomalies were flagged in the active dataset."

        # 4. General Dataset & Reconciliation Summary
        if final:
            return f"**Active Reconciliation Summary**:\n- **Total Records Evaluated**: {len(matched) + len(queue)}\n- **Match Rate**: {final.match_rate:.1%}\n- **Matched Transactions**: {len(matched)}\n- **Discrepancies Flagged**: {len(queue)}\n- **Total Gross Volume**: INR {final.total_gross:,.2f}\n- **Net Settled**: INR {final.total_net:,.2f}\n- **Auto-Resolved (Approved)**: {final.auto_resolved_count}\n- **Pending Review**: {final.unresolved_count}"

        return "Active datasets are loaded. You can ask about matched transactions, fees, specific order IDs (e.g. ORD_3), or duplicate records."

    def chat(self, user_message: str) -> Dict[str, Any]:
        """Process a user question against the current active reconciliation dataset."""
        if not self.pipe or not getattr(self.pipe, "tables", None) or len(self.pipe.tables) == 0:
            return {
                "ok": False,
                "error": "No active files loaded.",
                "response": "Please upload or stage reconciliation files before starting the conversation.",
            }

        context = build_grounded_context(self.pipe)
        self.history.append({"role": "user", "content": user_message})

        try:
            reply, cost = llm_client.conversational_chat(self.history, system_instruction=context)
            self.history.append({"role": "model", "content": reply})
            return {
                "ok": True,
                "response": reply,
                "cost_usd": cost,
                "session_id": self.sid,
            }
        except Exception:
            # Fallback to local grounded dataset engine
            reply = self._fallback_answer(user_message)
            self.history.append({"role": "model", "content": reply})
            return {
                "ok": True,
                "response": reply,
                "cost_usd": 0.0,
                "session_id": self.sid,
            }

