import json
from typing import List, Dict, Tuple, Optional
from app.core import llm_client


def build_grounded_context(pipe) -> str:
    """
    Builds a strict context snapshot containing ONLY the currently active tables,
    schema mappings, matched records, exceptions, and financial balances.
    Deleted files and tables are automatically excluded.
    """
    if not pipe or not getattr(pipe, "tables", None):
        return "NO_ACTIVE_FILES: There are no files or datasets loaded in the current active session."

    lines = []
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

    lines.append("\n=== CRITICAL RECONCILIATION ASSISTANT RULES ===")
    lines.append("1. You are the AI Reconciliation Assistant for this financial dataset.")
    lines.append("2. Answer the user's questions strictly using the ACTIVE dataset and report provided above.")
    lines.append("3. If the user asks about a file, order, transaction, or column that was deleted, replaced, or is not in the active dataset, you MUST state clearly that the file/data is not present in the current active session.")
    lines.append("4. Never hallucinate data for deleted files or nonexistent transactions.")
    lines.append("5. Keep answers concise, factual, and formatted in clear markdown.")

    return "\n".join(lines)


class ReconChatSession:
    def __init__(self, sid: str, pipe=None):
        self.sid = sid
        self.pipe = pipe
        self.history: List[Dict[str, str]] = []

    def set_pipe(self, pipe):
        self.pipe = pipe

    def chat(self, user_message: str) -> Dict[str, any]:
        if not self.pipe or not getattr(self.pipe, "tables", None) or len(self.pipe.tables) == 0:
            return {
                "ok": False,
                "error": "No active files loaded. The conversation starts only after files are uploaded/ingested.",
                "response": "Please upload or ingest reconciliation files before starting the conversation."
            }

        context = build_grounded_context(self.pipe)
        
        # Append user message
        self.history.append({"role": "user", "content": user_message})

        try:
            reply, cost = llm_client.conversational_chat(self.history, system_instruction=context)
            self.history.append({"role": "model", "content": reply})
            return {
                "ok": True,
                "response": reply,
                "cost_usd": cost,
                "session_id": self.sid
            }
        except Exception as e:
            # Rollback last user message on failure
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            return {
                "ok": False,
                "error": str(e),
                "response": f"Failed to generate response: {e}"
            }
