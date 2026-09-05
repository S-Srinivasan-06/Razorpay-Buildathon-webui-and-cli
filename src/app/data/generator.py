import json
import sys
from pathlib import Path


def generate(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    P = [  # order_id, amount, date  (l_rid = row order)
        ("ORD_1", 1000.00, "2026-03-01"),   # 1 exact
        ("ORD_2", 2000.00, "2026-03-01"),   # 2 fee deduction (net 1952.80)
        ("ORD_3", 3000.00, "2026-03-06"),   # 3 temporal drift (5 business days)
        ("ORD_4", 500.00,  "2026-03-02"),   # 4 duplicate key pair
        ("ORD_4", 500.00,  "2026-03-02"),   # 5
        ("ORD_6", 400.00,  "2026-03-02"),   # 6 split pair
        ("ORD_7", 700.00,  "2026-03-02"),   # 7
        ("MIS_800", 900.00, "2026-03-03"),  # 8 missing counterparty
    ]
    B = [  # utr, credit, date  (r_rid = row order)
        ("ORD_1", 1000.00, "2026-03-02"),   # 1
        ("ORD_2", 1952.80, "2026-03-02"),   # 2
        ("ORD_3", 3000.00, "2026-03-13"),   # 3
        ("ORD_4", 500.00,  "2026-03-03"),   # 4
        ("BATCH", 1074.04, "2026-03-03"),   # 5 = net(400)+net(700)
        ("ORD_9", 850.00,  "2026-03-05"),   # 6 unmatched inflow
        ("REFUND", -250.00, "2026-03-05"),  # 7 refund offset
    ]
    (out / "payments.csv").write_text(
        "order_id,amount,date\n" + "".join(f"{o},{a},{d}\n" for o, a, d in P))
    (out / "bank.csv").write_text(
        "utr,credit,date\n" + "".join(f"{u},{c},{d}\n" for u, c, d in B))
    # truth = pairs the ideal 1:1 matcher should land (dup first instance included);
    # drift/split/refund/inflow/missing are exception-honesty fixtures, NOT in truth.
    (out / "ground_truth.jsonl").write_text("".join(
        json.dumps({"l_rid": l, "r_rid": r, "class": c}) + "\n"
        for l, r, c in [(1, 1, "exact"), (2, 2, "fee_deduction"), (4, 4, "duplicate_first")]))


if __name__ == "__main__":
    generate(Path(sys.argv[1] if len(sys.argv) > 1 else "sample_data"))
