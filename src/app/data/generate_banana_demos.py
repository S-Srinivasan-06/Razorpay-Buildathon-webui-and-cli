"""Generator for Banana Supply & Inventory 3-Way Reconciliation Demo Datasets.

Produces two distinct benchmark demos:
1. banana_supply_inventory (3 files):
   - banana_orders.csv (100 orders across quick-commerce platforms)
   - banana_gateway_ledger.csv (100 settled gateway records with standard 2% fee + 18% GST)
   - banana_bank_statement.csv (100 matching bank statement credits)
   -> 100% matched, 0 discrepancies in 3-way chaining.

2. banana_supply_inventory_standard_tax (3 files):
   - banana_orders.csv (100 orders)
   - banana_gateway_ledger.csv (100 records: 79 standard settled, 11 non-standard 5% fee, 10 pending)
   - banana_bank_statement.csv (90 credits: 79 standard, 11 fee variance, 10 missing/in-transit)
   -> Exactly 21 discrepancies (11 fee deductions + 10 missing/in-transit) when standard tax policy is applied.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd

VARIETIES: List[Tuple[str, float]] = [
    ("Robusta Bananas (Crate)", 50.0),
    ("Cavendish Bananas (Box)", 65.0),
    ("Yellaki Bananas (Crate)", 90.0),
    ("Red Bananas (Box)", 110.0),
    ("Nendran Bananas (Crate)", 85.0),
    ("G9 Bananas (Crate)", 60.0),
    ("Poovan Bananas (Box)", 75.0),
    ("Rasthali Bananas (Box)", 95.0),
]

PLATFORMS: List[str] = ["Zomato", "BigBasket", "Blinkit", "Flipkart"]
CRATE_COUNTS: List[int] = [20, 30, 40, 50, 60, 75, 80, 100, 35, 45, 55, 65, 70, 85]
BANKS: List[str] = ["HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank"]


def generate_85pct_demo(out_dir: Path) -> None:
    """Generate Demo 1: Banana Supply & Inventory dataset with crisp 85% match rate.
    
    5 Distinct Irregularity Categories (15 total exceptions across 100 orders):
    1. Temporal Drift (3 orders: 86-88) - clearing delayed by 19 business days (> window_days=3).
    2. Value Error / Fee Variance (3 orders: 89-91) - gateway overcharged 6% MDR instead of standard 2%.
    3. Counterparty Mismatch (3 orders: 92-94) - fuzzy identifier typo in clearing reference + lag.
    4. Duplicate Submission (3 orders: 95-97) - duplicate order dispatches for previously fulfilled orders.
    5. Missing in Bank (3 orders: 98-100) - dispatched orders pending gateway settlement, absent in bank.
    
    Result: Exactly 85 matched orders (85.0% match rate) and 15 honest exceptions across 5 distinct categories.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    orders: List[Dict[str, Any]] = []
    ledger: List[Dict[str, Any]] = []
    bank: List[Dict[str, Any]] = []

    running_balance = 500000.0

    # 1. First 85 Clean Standard Orders (T+1 settlement, 2% fee + 18% GST)
    for i in range(1, 86):
        oid = f"BNN_{1000+i}"
        prod, rate = VARIETIES[(i - 1) % len(VARIETIES)]
        crates = CRATE_COUNTS[(i - 1) % len(CRATE_COUNTS)]
        amt = round(crates * rate, 2)
        plat = PLATFORMS[(i - 1) % len(PLATFORMS)]
        b_name = BANKS[(i - 1) % len(BANKS)]
        utr = f"UTR_BNN_{1000+i}"
        pay_id = f"pay_BNN_{1000+i}"

        day = (i % 20) + 1
        d_order = f"2026-03-{day:02d}"
        d_settle = f"2026-03-{day+1:02d}"

        fee = round(amt * 0.02, 2)
        gst = round(fee * 0.18, 2)
        net = round(amt - fee - gst, 2)
        running_balance += net

        orders.append({
            "order_id": oid,
            "platform": plat,
            "product": prod,
            "crates": crates,
            "unit_price": rate,
            "amount": amt,
            "date": d_order,
        })

        ledger.append({
            "order_id": oid,
            "rzp_payment_id": pay_id,
            "platform": plat,
            "gross_amount": amt,
            "gateway_fee": fee,
            "gst_on_fee": gst,
            "net_settled": net,
            "settlement_utr": utr,
            "settlement_date": d_settle,
            "status": "SETTLED",
        })

        bank.append({
            "order_id": oid,
            "date": d_settle,
            "utr": utr,
            "bank": b_name,
            "credit": net,
            "debit": 0.0,
            "balance": round(running_balance, 2),
            "narration": f"CMS/RZP/{utr}/{oid}/{plat.upper()}",
        })

    # 2. Irregularity 1: Temporal Drift (Orders 86 to 88 - 3 orders)
    # Settlement delayed by 19 business days (> window_days=3), gross matches deposit
    for i in range(86, 89):
        oid = f"BNN_{1000+i}"
        prod, rate = VARIETIES[(i - 1) % len(VARIETIES)]
        crates = CRATE_COUNTS[(i - 1) % len(CRATE_COUNTS)]
        amt = round(crates * rate, 2)
        plat = PLATFORMS[(i - 1) % len(PLATFORMS)]
        b_name = BANKS[(i - 1) % len(BANKS)]
        utr = f"UTR_BNN_{1000+i}"
        pay_id = f"pay_BNN_{1000+i}"
        d_order = "2026-03-02"
        d_settle = "2026-03-27"  # 19 business days clearing hold

        orders.append({
            "order_id": oid,
            "platform": plat,
            "product": prod,
            "crates": crates,
            "unit_price": rate,
            "amount": amt,
            "date": d_order,
        })

        ledger.append({
            "order_id": oid,
            "rzp_payment_id": pay_id,
            "platform": plat,
            "gross_amount": amt,
            "gateway_fee": 0.0,
            "gst_on_fee": 0.0,
            "net_settled": amt,
            "settlement_utr": utr,
            "settlement_date": d_settle,
            "status": "SETTLED",
        })

        running_balance += amt
        bank.append({
            "order_id": oid,
            "date": d_settle,
            "utr": utr,
            "bank": b_name,
            "credit": amt,
            "debit": 0.0,
            "balance": round(running_balance, 2),
            "narration": f"CMS/RZP/{utr}/{oid}/{plat.upper()}/HELD_CLEARING",
        })

    # 3. Irregularity 2: Value Error / Fee Variance (Orders 89 to 91 - 3 orders)
    # Gateway charged 6% MDR instead of standard 2%, creating unexplained fee variance
    for i in range(89, 92):
        oid = f"BNN_{1000+i}"
        prod, rate = VARIETIES[(i - 1) % len(VARIETIES)]
        crates = CRATE_COUNTS[(i - 1) % len(CRATE_COUNTS)]
        amt = round(crates * rate, 2)
        plat = PLATFORMS[(i - 1) % len(PLATFORMS)]
        b_name = BANKS[(i - 1) % len(BANKS)]
        utr = f"UTR_BNN_{1000+i}"
        pay_id = f"pay_BNN_{1000+i}"
        d_order = "2026-03-10"
        d_settle = "2026-03-11"

        fee_6pct = round(amt * 0.06, 2)
        gst_6pct = round(fee_6pct * 0.18, 2)
        net_bad = round(amt - fee_6pct - gst_6pct, 2)
        running_balance += net_bad

        orders.append({
            "order_id": oid,
            "platform": plat,
            "product": prod,
            "crates": crates,
            "unit_price": rate,
            "amount": amt,
            "date": d_order,
        })

        ledger.append({
            "order_id": oid,
            "rzp_payment_id": pay_id,
            "platform": plat,
            "gross_amount": amt,
            "gateway_fee": fee_6pct,
            "gst_on_fee": gst_6pct,
            "net_settled": net_bad,
            "settlement_utr": utr,
            "settlement_date": d_settle,
            "status": "SETTLED",
        })

        bank.append({
            "order_id": oid,
            "date": d_settle,
            "utr": utr,
            "bank": b_name,
            "credit": net_bad,
            "debit": 0.0,
            "balance": round(running_balance, 2),
            "narration": f"CMS/RZP/{utr}/{oid}/{plat.upper()}/NON_STD_FEE",
        })

    # 4. Irregularity 3: Counterparty Reference Typo (Orders 92 to 94 - 3 orders)
    # Typo in settlement reference ID + clearing lag prevents auto-match
    for i in range(92, 95):
        oid = f"BNN_{1000+i}"
        typo_oid = f"{oid}_TYPO"
        prod, rate = VARIETIES[(i - 1) % len(VARIETIES)]
        crates = CRATE_COUNTS[(i - 1) % len(CRATE_COUNTS)]
        amt = round(crates * rate, 2)
        plat = PLATFORMS[(i - 1) % len(PLATFORMS)]
        b_name = BANKS[(i - 1) % len(BANKS)]
        utr = f"UTR_{typo_oid}"
        pay_id = f"pay_{typo_oid}"
        d_order = "2026-03-12"
        d_settle = "2026-03-25"

        fee = round(amt * 0.02, 2)
        gst = round(fee * 0.18, 2)
        net = round(amt - fee - gst, 2)
        running_balance += net

        orders.append({
            "order_id": oid,
            "platform": plat,
            "product": prod,
            "crates": crates,
            "unit_price": rate,
            "amount": amt,
            "date": d_order,
        })

        ledger.append({
            "order_id": typo_oid,
            "rzp_payment_id": pay_id,
            "platform": plat,
            "gross_amount": amt,
            "gateway_fee": fee,
            "gst_on_fee": gst,
            "net_settled": net,
            "settlement_utr": utr,
            "settlement_date": d_settle,
            "status": "SETTLED",
        })

        bank.append({
            "order_id": typo_oid,
            "date": d_settle,
            "utr": utr,
            "bank": b_name,
            "credit": net,
            "debit": 0.0,
            "balance": round(running_balance, 2),
            "narration": f"CMS/RZP/{utr}/{typo_oid}/{plat.upper()}/REF_MISMATCH",
        })

    # 5. Irregularity 4: Duplicate Order Submissions (Orders 95 to 97 - 3 orders)
    # Dispatch duplicate entries for previously fulfilled orders (15, 25, 35)
    dup_sources = [15, 25, 35]
    for target in dup_sources:
        dup_oid = f"BNN_{1000+target}"
        prod, rate = VARIETIES[(target - 1) % len(VARIETIES)]
        crates = CRATE_COUNTS[(target - 1) % len(CRATE_COUNTS)]
        amt = round(crates * rate, 2)
        plat = PLATFORMS[(target - 1) % len(PLATFORMS)]

        orders.append({
            "order_id": dup_oid,
            "platform": plat,
            "product": prod,
            "crates": crates,
            "unit_price": rate,
            "amount": amt,
            "date": "2026-03-15",
        })
        # Not settled again in bank -> flags as duplicate dispatch exception

    # 6. Irregularity 5: Missing in Bank / In-Transit Settlement (Orders 98 to 100 - 3 orders)
    # Placed & dispatched, pending settlement in gateway, completely omitted from bank
    for i in range(98, 101):
        oid = f"BNN_{1000+i}"
        prod, rate = VARIETIES[(i - 1) % len(VARIETIES)]
        crates = CRATE_COUNTS[(i - 1) % len(CRATE_COUNTS)]
        amt = round(crates * rate, 2)
        plat = PLATFORMS[(i - 1) % len(PLATFORMS)]
        pay_id = f"pay_BNN_{1000+i}"

        orders.append({
            "order_id": oid,
            "platform": plat,
            "product": prod,
            "crates": crates,
            "unit_price": rate,
            "amount": amt,
            "date": "2026-03-18",
        })

        ledger.append({
            "order_id": oid,
            "rzp_payment_id": pay_id,
            "platform": plat,
            "gross_amount": amt,
            "gateway_fee": 0.0,
            "gst_on_fee": 0.0,
            "net_settled": 0.0,
            "settlement_utr": "",
            "settlement_date": "",
            "status": "PENDING",
        })
        # Omitted from bank -> flags as missing bank settlement

    pd.DataFrame(orders).to_csv(out_dir / "banana_orders.csv", index=False)
    pd.DataFrame(ledger).to_csv(out_dir / "banana_gateway_ledger.csv", index=False)
    pd.DataFrame(bank).to_csv(out_dir / "banana_bank_statement.csv", index=False)


def generate_standard_tax_demo(out_dir: Path) -> None:
    """Generate Demo 2: Banana Supply & Inventory with Standard Tax (100 orders, exactly 21 discrepancies).
    
    Discrepancy Breakdown:
    - 79 clean matching orders (standard 2% fee + 18% GST).
    - 11 fee variance orders (gateway deducted 5% fee + 18% GST instead of standard 2%).
    - 10 missing bank orders (customer placed order, pending settlement, omitted from bank).
    Total discrepancies = 11 + 10 = 21.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    orders: List[Dict[str, Any]] = []
    ledger: List[Dict[str, Any]] = []
    bank: List[Dict[str, Any]] = []

    running_balance = 500000.0

    for i in range(1, 101):
        oid = f"BNN_{1000+i}"
        prod, rate = VARIETIES[(i - 1) % len(VARIETIES)]
        crates = CRATE_COUNTS[(i - 1) % len(CRATE_COUNTS)]
        amt = round(crates * rate, 2)
        plat = PLATFORMS[(i - 1) % len(PLATFORMS)]
        b_name = BANKS[(i - 1) % len(BANKS)]
        utr = f"UTR_BNN_{1000+i}"
        pay_id = f"pay_BNN_{1000+i}"

        day = (i % 25) + 1
        d_order = f"2026-03-{day:02d}"
        d_settle = f"2026-03-{day+1:02d}"

        orders.append({
            "order_id": oid,
            "platform": plat,
            "product": prod,
            "crates": crates,
            "unit_price": rate,
            "amount": amt,
            "date": d_order,
        })

        if i <= 79:
            # 79 Clean Standard Matches (2% fee + 18% GST)
            fee = round(amt * 0.02, 2)
            gst = round(fee * 0.18, 2)
            net = round(amt - fee - gst, 2)
            running_balance += net

            ledger.append({
                "order_id": oid,
                "rzp_payment_id": pay_id,
                "platform": plat,
                "gross_amount": amt,
                "gateway_fee": fee,
                "gst_on_fee": gst,
                "net_settled": net,
                "settlement_utr": utr,
                "settlement_date": d_settle,
                "status": "SETTLED",
            })

            bank.append({
                "order_id": oid,
                "date": d_settle,
                "utr": utr,
                "bank": b_name,
                "credit": net,
                "debit": 0.0,
                "balance": round(running_balance, 2),
                "narration": f"CMS/RZP/{utr}/{oid}/{plat.upper()}",
            })

        elif i <= 90:
            # 11 Fee Variance Discrepancies (Gateway charged 5% fee instead of standard 2%)
            fee = round(amt * 0.05, 2)
            gst = round(fee * 0.18, 2)
            net = round(amt - fee - gst, 2)
            running_balance += net

            ledger.append({
                "order_id": oid,
                "rzp_payment_id": pay_id,
                "platform": plat,
                "gross_amount": amt,
                "gateway_fee": fee,
                "gst_on_fee": gst,
                "net_settled": net,
                "settlement_utr": utr,
                "settlement_date": d_settle,
                "status": "SETTLED",
            })

            bank.append({
                "order_id": oid,
                "date": d_settle,
                "utr": utr,
                "bank": b_name,
                "credit": net,
                "debit": 0.0,
                "balance": round(running_balance, 2),
                "narration": f"CMS/RZP/{utr}/{oid}/{plat.upper()}",
            })

        else:
            # 10 Missing / In-Transit Discrepancies (Orders placed, pending in gateway, absent in bank)
            ledger.append({
                "order_id": oid,
                "rzp_payment_id": pay_id,
                "platform": plat,
                "gross_amount": amt,
                "gateway_fee": 0.0,
                "gst_on_fee": 0.0,
                "net_settled": 0.0,
                "settlement_utr": "",
                "settlement_date": "",
                "status": "PENDING",
            })
            # Intentionally omitted from bank.csv -> yields missing exception

    pd.DataFrame(orders).to_csv(out_dir / "banana_orders.csv", index=False)
    pd.DataFrame(ledger).to_csv(out_dir / "banana_gateway_ledger.csv", index=False)
    pd.DataFrame(bank).to_csv(out_dir / "banana_bank_statement.csv", index=False)


def generate_all(base_datasets_dir: Path) -> None:
    """Generate both banana demo suites and update legacy root dataset files."""
    clean_dir = base_datasets_dir / "banana_supply_inventory"
    std_tax_dir = base_datasets_dir / "banana_supply_inventory_standard_tax"

    print(f"Generating 85% match rate 3-file demo (5 irregularities) in {clean_dir}...")
    generate_85pct_demo(clean_dir)

    print(f"Generating standard tax 3-file demo (21 discrepancies) in {std_tax_dir}...")
    generate_standard_tax_demo(std_tax_dir)

    # Maintain root payments.csv and bank.csv for backwards compatibility
    print("Updating root datasets/payments.csv and datasets/bank.csv...")
    (base_datasets_dir / "payments.csv").write_bytes((clean_dir / "banana_orders.csv").read_bytes())
    (base_datasets_dir / "bank.csv").write_bytes((clean_dir / "banana_bank_statement.csv").read_bytes())
    print("Dataset generation complete!")


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    ds_dir = root_dir / "datasets"
    generate_all(ds_dir)
