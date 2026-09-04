#!/usr/bin/env python3
"""Razorpay Autonomous Financial Reconciliation Agent CLI & Server Runner.

Provides the unified command-line entry point for both the terminal CLI engine
and the FastAPI web application server.

CLI Usage Examples:
  # Standard two-file reconciliation (payments vs bank):
  python run.py sample_data/payments.csv sample_data/bank.csv

  # Reconciliation with precision/recall benchmark evaluation against ground truth:
  python run.py sample_data/payments.csv sample_data/bank.csv --truth sample_data/ground_truth.jsonl

  # Start interactive grounded AI assistant REPL after reconciliation:
  python run.py sample_data/payments.csv sample_data/bank.csv --chat

  # Run in pure offline deterministic mode without external LLM calls:
  python run.py sample_data/payments.csv sample_data/bank.csv --deterministic

  # Output final report and classified exception queue as structured JSON:
  python run.py sample_data/payments.csv sample_data/bank.csv --json

Server Usage Examples:
  # Launch FastAPI web console server (defaults to http://127.0.0.1:8000/console):
  python run.py --server
  python run.py --server --host 0.0.0.0 --port 8000
"""

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Ensure src directory is in sys.path
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from app.config import AUDIT_DIR, LOGS_DIR, OUTPUT_DIR
from app.core import llm_client
from app.core.audit import audit_for
from app.engine.chatbot import ReconChatSession
from app.engine.report import export_reconciliation_csv_string
from app.pipeline import Pipeline


def format_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Format tabular data into a clean, aligned GitHub-flavored Markdown table.
    
    Dynamically computes maximum column widths to ensure clean monospaced alignment
    without requiring third-party table formatting packages.
    
    Args:
        headers: List of column header strings.
        rows: List of row lists containing cell values.
        
    Returns:
        Formatted Markdown table string.
    """
    if not headers or not rows:
        return "_No records available._"
    str_rows = [[str(val) for val in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, val in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(val))

    header_line = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    separator_line = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    data_lines = [
        "| " + " | ".join(row[i].ljust(widths[i]) if i < len(row) else "".ljust(widths[i]) for i in range(len(headers))) + " |"
        for row in str_rows
    ]
    return "\n".join([header_line, separator_line] + data_lines)


def start_chat_repl(pipe: Pipeline, sid: str) -> None:
    """Start an interactive terminal chat REPL grounded in the current reconciliation session.
    
    Args:
        pipe: Completed Pipeline instance containing active datasets and reports.
        sid: Session identifier string.
    """
    print("\n---\n", flush=True)
    print(f"## 💬 Interactive Reconciliation Assistant (Session: `{sid}`)\n", flush=True)
    print("- Connected to **Gemma 4 31B** (`gemma-4-31b-it`) strictly grounded in active session datasets.", flush=True)
    print("- Ask questions about matched records, fee schedules, duplicates, or root causes.", flush=True)
    print("- Type `exit` or `quit` to end the conversation.\n", flush=True)

    chat_session = ReconChatSession(sid, pipe)

    while True:
        try:
            sys.stdout.write("recon-bot> ")
            sys.stdout.flush()
            user_input = sys.stdin.readline()
            if not user_input:
                break
            query = user_input.strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("\n- **Status**: Chat session closed.", flush=True)
                break

            result = chat_session.chat(query)
            if result.get("ok"):
                cost_str = f" *(LLM Cost: ${result['cost_usd']:.6f})*" if result.get("cost_usd") else ""
                print(f"\n{result['response']}{cost_str}\n", flush=True)
            else:
                print(f"\n> ⚠️ **Error**: {result.get('error', result.get('response'))}\n", flush=True)
        except (KeyboardInterrupt, EOFError):
            print("\n- **Status**: Exiting chat.", flush=True)
            break


def run_cli(
    files: List[Path],
    truth: Optional[Path] = None,
    auto_ack: bool = True,
    as_json: bool = False,
    deterministic: bool = False,
    chat: bool = False,
    out_dir: Optional[Path] = None,
) -> None:
    """Execute reconciliation pipeline in terminal CLI mode and render results.
    
    Args:
        files: List of statement file paths (.csv or .xlsx).
        truth: Optional ground truth benchmark file path (.jsonl).
        auto_ack: Whether to auto-acknowledge non-fatal halts.
        as_json: If True, prints output as structured JSON.
        deterministic: If True, disables external LLM calls and forces heuristic paths.
        chat: If True, launches interactive grounded chat REPL upon completion.
    """
    sid = uuid.uuid4().hex[:8]
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    session_file = LOGS_DIR / f"{sid}.log"
    latest_session_log = LOGS_DIR / "session.log"
    session_file.write_text("", encoding="utf-8")
    latest_session_log.write_text("", encoding="utf-8")

    print("# ⚡ Razorpay Reconciliation Agent", flush=True)
    print(f"**Session ID**: `{sid}`\n", flush=True)
    print("## Execution Steps", flush=True)
    
    if deterministic:
        print("- **Mode**: Deterministic Engine (Offline / Zero-LLM)", flush=True)
        def boom(*a: Any, **k: Any) -> None:
            raise ConnectionError("Deterministic mode enabled")
        llm_client.json_chat = boom

    for f in files:
        if not f.exists():
            print(f"> ❌ **Error**: File not found: `{f}`", file=sys.stderr, flush=True)
            sys.exit(1)
            
    if truth and not truth.exists():
        print(f"> ❌ **Error**: Truth file not found: `{truth}`", file=sys.stderr, flush=True)
        sys.exit(1)

    print(f"- **Ingesting**: `{', '.join(str(f) for f in files)}`", flush=True)
    if truth:
        print(f"- **Ground Truth Benchmark**: `{truth}`", flush=True)
    
    t0 = time.time()
    pipe = Pipeline(sid=sid, auto_ack=auto_ack)
    report = pipe.run(files, truth)
    elapsed = time.time() - t0

    if as_json:
        out = {
            "session_id": sid,
            "input_data": pipe.tables,
            "report": report.model_dump(mode="json") if report else None,
            "exceptions": [
                {
                    "rid": item["rec"].rid,
                    "side": item["rec"].side,
                    "ref": item["rec"].ref,
                    "reason": item["rec"].reason.value if hasattr(item["rec"].reason, "value") else str(item["rec"].reason),
                    "action": item.get("action", "pending"),
                    "confidence": item.get("conf", 0.0),
                    "delta": item["rec"].delta,
                    "explanation": item.get("explanation") or getattr(item["rec"], "explanation", None),
                    "evidence": [p.value if hasattr(p, "value") else str(p) for p in item.get("pieces", [])]
                }
                for item in pipe.queue
            ],
            "audit": {
                "records_count": len(audit_for(sid).records),
                "verified": audit_for(sid).verify()
            }
        }
        print(json.dumps(out, indent=2), flush=True)
        if chat:
            start_chat_repl(pipe, sid)
        return

    # 1. Ingested Input Data Section (Markdown Tables)
    print("\n---\n", flush=True)
    print("## Ingested Input Datasets", flush=True)
    for tbl_name, rows in pipe.tables.items():
        if not rows:
            continue
        cols = [k for k in rows[0].keys() if not k.startswith("_")]
        headers = ["#"] + cols
        data_rows = [[i] + [r.get(c, "") for c in cols] for i, r in enumerate(rows, 1)]
        print(f"\n### Table: `{tbl_name}` ({len(rows)} records)\n", flush=True)
        print(format_markdown_table(headers, data_rows), flush=True)

    # 2. Formatted Markdown Summary
    print("\n---\n", flush=True)
    print("## Reconciliation Report", flush=True)
    
    if report:
        perf_headers = ["Metric", "Value"]
        perf_rows = [
            ["Match Rate", f"{report.match_rate:.1%}"],
            ["Precision vs Truth", f"{report.precision_vs_truth:.1%}" if report.precision_vs_truth is not None else "N/A"],
            ["Recall vs Truth", f"{report.recall_vs_truth:.1%}" if report.recall_vs_truth is not None else "N/A"],
            ["Throughput", f"{report.throughput_rows_per_sec:.0f} rows/sec"],
            ["Execution Time", f"{elapsed:.2f}s"],
            ["LLM Metered Cost", f"${report.cost_usd:.6f}"]
        ]
        print("\n### Performance & Metrics\n", flush=True)
        print(format_markdown_table(perf_headers, perf_rows), flush=True)

        fin_headers = ["Financial Balance Component", "Amount (INR)"]
        fin_rows = [
            ["Gross Ledger Volume", f"₹{report.total_gross:,.2f}"],
            ["Net Bank Inflow", f"₹{report.total_net:,.2f}"],
            ["Gateway Fees Variance", f"₹{report.total_fees:,.2f}"],
            ["Matched Value", f"₹{report.matched_value:,.2f}"],
            ["Exception Value", f"₹{report.exception_value:,.2f}"]
        ]
        print("\n### Financial Balances\n", flush=True)
        print(format_markdown_table(fin_headers, fin_rows), flush=True)
        
        inv_ok = (report.auto_resolved_count + report.escalated_count + report.unresolved_count == report.honest_exception_count)
        q_headers = ["Queue Metric", "Count", "Status"]
        q_rows = [
            ["Auto-Resolved (Approved)", str(report.auto_resolved_count), "APPROVED [NO ERROR]"],
            ["Escalated (Review Req)", str(report.escalated_count), "REQUIRES ACTION [ERROR]"],
            ["Unresolved Pending", str(report.unresolved_count), "PENDING"],
            ["Total Honest Exceptions", str(report.honest_exception_count), f"Sum Invariant: {'VALID [OK]' if inv_ok else 'INVALID'}"]
        ]
        print(f"\n### Exception Queue Summary ({report.honest_exception_count} Total)\n", flush=True)
        print(format_markdown_table(q_headers, q_rows), flush=True)
    
    if pipe.queue:
        print("\n### Classified Discrepancies & Diagnostics\n", flush=True)
        exc_headers = ["#", "Side", "Reference", "Discrepancy Class", "Action Status", "Delta (INR)", "Diagnostic & Root Cause"]
        exc_rows = []
        for i, item in enumerate(pipe.queue, 1):
            rec = item["rec"]
            action = item.get("action", "pending")
            action_badge = "APPROVED [NO ERROR]" if action == "auto_resolve" else "REQUIRES ACTION [ERROR]"
            delta_str = f"₹{rec.delta:,.2f}" if rec.delta is not None else "—"
            reason_str = rec.reason.value if hasattr(rec.reason, "value") else str(rec.reason)
            explanation = item.get("explanation") or getattr(rec, "explanation", "") or "No diagnostic available."
            exc_rows.append([str(i), rec.side, str(rec.ref or "N/A"), reason_str, action_badge, delta_str, explanation])
        print(format_markdown_table(exc_headers, exc_rows), flush=True)

    # 3. Cryptographic Audit Ledger Section
    audit_log = audit_for(sid)
    print("\n---\n", flush=True)
    print("## Cryptographic Audit Ledger\n", flush=True)
    audit_headers = ["Audit Attribute", "Value"]
    audit_rows = [
        ["Audit Entries Logged", str(len(audit_log.records))],
        ["SHA-256 Chain Integrity", "VERIFIED [OK]" if audit_log.verify() else "TAMPERED [FAIL]"],
        ["Session Audit Path", f"`data/audit/{sid}.audit.jsonl`"]
    ]
    print(format_markdown_table(audit_headers, audit_rows), flush=True)
    print("\n---\n", flush=True)

    # 4. Save Output Artifacts to Disk
    target_out = out_dir if out_dir else (OUTPUT_DIR / sid)
    target_out.mkdir(parents=True, exist_ok=True)
    rep_path = target_out / "final_report.json"
    csv_path = target_out / "reconciliation_output.csv"
    aud_path = target_out / "audit_chain.jsonl"
    
    if report:
        rep_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    csv_str = export_reconciliation_csv_string(pipe)
    csv_path.write_text(csv_str, encoding="utf-8")
    audit_src = AUDIT_DIR / f"{sid}.audit.jsonl"
    if audit_src.exists():
        shutil.copy2(audit_src, aud_path)

    print("## Saved Output Files\n", flush=True)
    out_headers = ["Output Artifact", "Disk Path"]
    out_rows = [
        ["Session Output Directory", f"`{target_out}`"],
        ["Reconciliation Output CSV", f"`{csv_path}`"],
        ["Final Report JSON", f"`{rep_path}`"],
        ["Cryptographic Audit Ledger", f"`{aud_path}`"],
    ]
    print(format_markdown_table(out_headers, out_rows), flush=True)
    print("\n---\n", flush=True)

    if chat:
        start_chat_repl(pipe, sid)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch the FastAPI server and open the web console in the default browser.
    
    Args:
        host: Network interface host to bind to.
        port: Network port to listen on.
    """
    import threading
    import uvicorn
    import webbrowser
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"- **Server**: Starting API Server on `http://{host}:{port}` ...", flush=True)
    print(f"- **Console**: Opening `http://{host}:{port}/console` in browser ...", flush=True)
    # Open browser after a short delay
    threading.Timer(1.5, lambda: webbrowser.open(f"http://{host}:{port}/console")).start()
    uvicorn.run(
        "app.server.main:app",
        host=host,
        port=port,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                },
            },
            "handlers": {
                "file": {
                    "formatter": "default",
                    "class": "logging.FileHandler",
                    "filename": str(LOGS_DIR / "server.log"),
                    "mode": "a",
                    "encoding": "utf-8",
                },
                "console": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["file", "console"],
            },
        }
    )


def main() -> None:
    """Parse CLI arguments and dispatch execution to run_server or run_cli."""
    parser = argparse.ArgumentParser(
        description="Razorpay Autonomous Financial Reconciliation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="*", type=Path, help="CSV/Excel statement files to reconcile (e.g. sample_data/payments.csv sample_data/bank.csv)")
    parser.add_argument("--truth", type=Path, default=None, help="Optional ground truth jsonl file for precision/recall evaluation")
    parser.add_argument("--deterministic", "--no-llm", action="store_true", help="Run in pure deterministic mode without external LLM calls")
    parser.add_argument("--json", action="store_true", help="Output final report as formatted JSON")
    parser.add_argument("--chat", "-i", action="store_true", help="Start continuous interactive chatbot REPL after reconciliation")
    parser.add_argument("--clear-logs", action="store_true", help="Delete all session logs, audit trails, and uploads")
    parser.add_argument("--out-dir", type=Path, default=None, help="Custom directory to save reconciliation outputs (default: data/outputs/<session_id>/)")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI REST/WebSocket server with web console")
    parser.add_argument("--cli", action="store_true", help="Force CLI mode (skip auto-server)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    
    args = parser.parse_args()

    if args.clear_logs:
        for d in [LOGS_DIR, LOGS_DIR.parent / "audit", LOGS_DIR.parent / "uploads", OUTPUT_DIR]:
            if d.exists():
                for f in d.glob("*"):
                    try:
                        if f.is_file():
                            f.unlink()
                        elif f.is_dir():
                            shutil.rmtree(f)
                    except Exception:
                        pass
        print("- **Status**: All session logs, audit files, uploaded datasets, and output directories have been cleared.")
        if not args.server and not args.files:
            return

    if args.server:
        run_server(host=args.host, port=args.port)
    elif args.files:
        run_cli(
            files=args.files,
            truth=args.truth,
            auto_ack=True,
            as_json=args.json,
            deterministic=args.deterministic,
            chat=args.chat,
            out_dir=args.out_dir,
        )
    elif args.cli:
        parser.print_help()
    else:
        # Default: launch web console when no files are provided
        print("# ⚡ Razorpay Reconciliation Agent", flush=True)
        print("No files specified — launching web console...\n", flush=True)
        run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
