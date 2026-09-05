"""Generator for 5-Enterprise Ecosystem and 3-File Benchmark Datasets.

Generates:
1. 5-Enterprise Ecosystem Datasets (>=50 data rows, >=5 attributes each):
   - zomato_orders.csv (Food delivery, 5% food GST, failed orders, refund tracking)
   - flipkart_orders.csv (Ecommerce, variable goods tax rates: 18%, 12%, 0%)
   - razorpay_ledger.csv (Transaction & settlement record book, routing to ICICI & HDFC,
                         merchant fee collected, bank charge incurred, razorpay_net_profit,
                         and refund tracking)
   - icici_bank.csv (ICICI settlement statement, ICICI gateway charge rate, credits, refund debits)
   - hdfc_bank.csv (HDFC settlement statement, HDFC gateway charge rate, credits, refund debits)

2. 3-File Benchmark Dataset with Multiple Errors & Variable Tax Rates:
   - merchant_sales.csv (>=50 rows, 7 attributes)
   - gateway_settlements.csv (>=50 rows, 7 attributes)
   - bank_statement.csv (>=50 rows, 7 attributes)
   - benchmark_truth.jsonl (Strictly offline expected truth file - NEVER uploaded to server)
"""

import csv
import json
from pathlib import Path
import random

# Fixed seed for reproducibility
random.seed(42)


def generate_enterprise_ecosystem(dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # --- 1. Zomato Orders (60 rows, 8 attributes) ---
    zomato_rows = []
    base_gross_zomato = [250.0, 420.0, 580.0, 750.0, 920.0, 1150.0, 1380.0, 1650.0]
    methods = ["UPI", "Credit Card", "Debit Card", "NetBanking"]
    
    for i in range(1, 61):
        order_id = f"ZOM_{1000 + i}"
        cust = f"Customer_{100 + i}"
        cat = "Food & Beverages"
        food_gst = 0.05
        gross = random.choice(base_gross_zomato) + round(random.random() * 50, 2)
        gross = round(gross, 2)
        method = random.choice(methods)
        date_str = f"2026-03-{(i % 25) + 1:02d}"
        
        # Specific scenario rows
        if i == 25:
            status = "FAILED"
        elif i == 30:
            status = "REFUND_REQUESTED"
        elif i == 35:
            status = "REFUNDED"
        else:
            status = "COMPLETED"
            
        zomato_rows.append({
            "order_id": order_id,
            "customer_name": cust,
            "category": cat,
            "food_tax_rate": food_gst,
            "gross_amount": gross,
            "order_status": status,
            "payment_method": method,
            "created_at": date_str,
        })
        
    zom_path = dest_dir / "zomato_orders.csv"
    with open(zom_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(zomato_rows[0].keys()))
        w.writeheader()
        w.writerows(zomato_rows)

    # --- 2. Flipkart Orders (60 rows, 8 attributes) ---
    flipkart_rows = []
    categories = [
        ("Electronics", 0.18),
        ("Apparel & Fashion", 0.12),
        ("Books & Publications", 0.00),  # Exempt 0%
        ("Home & Kitchen", 0.18),
    ]
    base_gross_flip = [499.0, 899.0, 1499.0, 2999.0, 4999.0, 8499.0, 12999.0]
    
    for i in range(1, 61):
        order_id = f"FLP_{2000 + i}"
        buyer = f"Buyer_{200 + i}"
        cat_info = categories[i % len(categories)]
        cat = cat_info[0]
        goods_gst = cat_info[1]
        gross = random.choice(base_gross_flip) + round(random.random() * 100, 2)
        gross = round(gross, 2)
        method = random.choice(methods)
        date_str = f"2026-03-{(i % 25) + 1:02d}"
        
        if i == 15:
            status = "CANCELLED"
        elif i == 20:
            status = "RETURNED"
        else:
            status = "DELIVERED"
            
        flipkart_rows.append({
            "order_id": order_id,
            "buyer_name": buyer,
            "goods_category": cat,
            "goods_tax_rate": goods_gst,
            "gross_amount": gross,
            "order_status": status,
            "payment_method": method,
            "ordered_at": date_str,
        })

    flp_path = dest_dir / "flipkart_orders.csv"
    with open(flp_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(flipkart_rows[0].keys()))
        w.writeheader()
        w.writerows(flipkart_rows)

    # --- 3. Razorpay Ledger (120 rows, 11 attributes) ---
    # Intermediary record book routing between merchants and partner banks (ICICI & HDFC)
    razorpay_rows = []
    total_rzr_profit = 0.0
    
    # Combine Zomato (60) + Flipkart (60)
    all_orders = [("Zomato", r) for r in zomato_rows] + [("Flipkart", r) for r in flipkart_rows]
    
    icici_rows = []
    hdfc_rows = []
    
    for idx, (platform, ord_data) in enumerate(all_orders, 1):
        txn_id = f"RZR_TXN_{3000 + idx}"
        order_id = ord_data["order_id"]
        method = ord_data["payment_method"]
        gross = ord_data["gross_amount"]
        
        # Route alternately between ICICI and HDFC
        bank = "ICICI" if (idx % 2 == 1) else "HDFC"
        
        # Merchant fee charged by Razorpay
        # e.g. Credit Card: 2.0% + 18% GST; Debit Card: 1.0% + 18% GST; NetBanking: 1.5% + 18% GST; UPI: 0.2% + 18% GST
        if method == "Credit Card":
            m_fee_rate = 0.02
        elif method == "NetBanking":
            m_fee_rate = 0.015
        elif method == "Debit Card":
            m_fee_rate = 0.01
        else:
            m_fee_rate = 0.002  # UPI
            
        merchant_base_fee = round(gross * m_fee_rate, 2)
        merchant_gst = round(merchant_base_fee * 0.18, 2)
        total_merchant_fee = round(merchant_base_fee + merchant_gst, 2)
        
        # Gateway charge incurred by Razorpay from Bank (interchange + processing)
        if method == "Credit Card":
            bank_fee_rate = 0.012 if bank == "ICICI" else 0.014
        elif method == "NetBanking":
            bank_fee_rate = 0.008 if bank == "ICICI" else 0.009
        elif method == "Debit Card":
            bank_fee_rate = 0.005 if bank == "ICICI" else 0.007
        else: # UPI
            bank_fee_rate = 0.0005 if bank == "ICICI" else 0.0008
            
        bank_base_charge = round(gross * bank_fee_rate, 2)
        bank_gst = round(bank_base_charge * 0.18, 2)
        total_bank_charge = round(bank_base_charge + bank_gst, 2)
        
        # Handling Failed and Refund scenarios
        status = ord_data.get("order_status")
        if status in ("FAILED", "CANCELLED"):
            settle_status = "FAILED_REVERSED"
            total_merchant_fee = 0.0
            total_bank_charge = 0.0
            rzr_profit = 0.0
            net_to_merchant = 0.0
            bank_deposit = 0.0
        elif status in ("REFUNDED", "RETURNED"):
            settle_status = "REFUND_PROCESSED"
            # In a refund, fees are reversed or absorbed
            rzr_profit = 0.0
            net_to_merchant = 0.0
            bank_deposit = -gross  # Debit refund entry at bank
        else:
            settle_status = "SETTLED"
            rzr_profit = round(total_merchant_fee - total_bank_charge, 2)
            net_to_merchant = round(gross - total_merchant_fee, 2)
            bank_deposit = round(gross - total_bank_charge, 2)

        total_rzr_profit += rzr_profit
        
        razorpay_rows.append({
            "transaction_id": txn_id,
            "source_platform": platform,
            "order_id": order_id,
            "payment_method": method,
            "gross_amount": gross,
            "routing_bank": bank,
            "merchant_fee_collected": total_merchant_fee,
            "bank_gateway_charge": total_bank_charge,
            "razorpay_net_profit": rzr_profit,
            "settlement_status": settle_status,
            "created_at": ord_data.get("created_at") or ord_data.get("ordered_at"),
        })

        # Append to Bank Settlement Statements
        bank_entry = {
            "utr": f"UTR_{bank}_{order_id}",
            "order_reference": order_id,
            "account_number": "50200012345678" if bank == "HDFC" else "000405067890",
            "transaction_type": "DEBIT_REFUND" if bank_deposit < 0 else "CREDIT",
            "deposit_amount": bank_deposit,
            "gateway_charge_deducted": total_bank_charge if bank_deposit > 0 else 0.0,
            "clearing_date": ord_data.get("created_at") or ord_data.get("ordered_at"),
            "settlement_status": "PROCESSED" if bank_deposit != 0 else "CANCELLED",
        }
        if bank == "ICICI":
            icici_rows.append(bank_entry)
        else:
            hdfc_rows.append(bank_entry)

    rzr_path = dest_dir / "razorpay_ledger.csv"
    with open(rzr_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(razorpay_rows[0].keys()))
        w.writeheader()
        w.writerows(razorpay_rows)

    icici_path = dest_dir / "icici_bank.csv"
    with open(icici_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(icici_rows[0].keys()))
        w.writeheader()
        w.writerows(icici_rows)

    hdfc_path = dest_dir / "hdfc_bank.csv"
    with open(hdfc_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(hdfc_rows[0].keys()))
        w.writeheader()
        w.writerows(hdfc_rows)

    print(f"Generated 5 enterprise ecosystem files in {dest_dir}:")
    print(f"  - zomato_orders.csv: {len(zomato_rows)} rows")
    print(f"  - flipkart_orders.csv: {len(flipkart_rows)} rows")
    print(f"  - razorpay_ledger.csv: {len(razorpay_rows)} rows (Total Razorpay Net Profit: INR {total_rzr_profit:.2f})")
    print(f"  - icici_bank.csv: {len(icici_rows)} rows")
    print(f"  - hdfc_bank.csv: {len(hdfc_rows)} rows")


def generate_3file_benchmark(dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 55 transactions with variable tax categories
    categories = [
        ("Essentials", 0.05),     # 5% GST
        ("Apparel", 0.12),        # 12% GST
        ("Electronics", 0.18),    # 18% GST
        ("Luxury", 0.28),         # 28% GST
        ("Educational", 0.00),    # 0% GST
    ]
    
    sales_rows = []
    settlement_rows = []
    bank_rows = []
    truth_records = []
    
    amounts = [600.0, 1200.0, 1850.0, 2400.0, 3100.0, 4500.0, 6800.0, 9500.0]
    
    for i in range(1, 56):
        order_ref = f"ORD_BM_{4000 + i}"
        cat, tax_rate = categories[i % len(categories)]
        gross = amounts[i % len(amounts)] + round(random.random() * 20, 2)
        gross = round(gross, 2)
        date_str = f"2026-03-{(i % 24) + 1:02d}"
        channel = "Online" if i % 2 == 0 else "Mobile App"
        customer = f"CUST_{500 + i}"
        
        # 1. Merchant Sales entry
        sales_rows.append({
            "order_ref": order_ref,
            "product_category": cat,
            "goods_gst_rate": tax_rate,
            "gross_inr": gross,
            "channel": channel,
            "sales_date": date_str,
            "customer_id": customer,
        })
        
        # Compute Gateway Deductions (2.0% fee + 18% GST on fee)
        fee_base = round(gross * 0.02, 2)
        fee_gst = round(fee_base * 0.18, 2)
        total_pg_fee = round(fee_base + fee_gst, 2)
        net_settled = round(gross - total_pg_fee, 2)
        
        # 2. Gateway Settlement entry
        settlement_rows.append({
            "order_ref": order_ref,
            "gateway_txn_id": f"TXN_{8000 + i}",
            "gateway_fee_inr": fee_base,
            "gst_on_fee_inr": fee_gst,
            "net_settled_inr": net_settled,
            "settlement_date": date_str,
            "payment_method": "Card" if i % 3 == 0 else "UPI",
        })
        
        # 3. Bank Statement entry (incorporating discrepancies)
        bank_utr = f"UTR_BM_{9000 + i}"
        
        if i == 10:
            # Temporal drift error (settled 6 days later)
            clearing_date = "2026-03-29"
            bank_rows.append({
                "bank_ref": bank_utr,
                "utr": order_ref,
                "credit_inr": net_settled,
                "debit_inr": 0.0,
                "clearing_date": clearing_date,
                "account_number": "9876543210",
                "status": "CLEARED",
            })
            truth_records.append({"order_ref": order_ref, "class": "temporal_drift", "variance": 0.0})
        elif i == 20:
            # Gateway fee variance error (bank deducted 50 INR extra)
            bank_rows.append({
                "bank_ref": bank_utr,
                "utr": order_ref,
                "credit_inr": round(net_settled - 50.0, 2),
                "debit_inr": 0.0,
                "clearing_date": date_str,
                "account_number": "9876543210",
                "status": "CLEARED",
            })
            truth_records.append({"order_ref": order_ref, "class": "fee_variance", "variance": 50.0})
        elif i == 30:
            # Customer refund / negative debit
            bank_rows.append({
                "bank_ref": bank_utr,
                "utr": order_ref,
                "credit_inr": 0.0,
                "debit_inr": gross,
                "clearing_date": date_str,
                "account_number": "9876543210",
                "status": "REFUND_DEBIT",
            })
            truth_records.append({"order_ref": order_ref, "class": "refund_offset", "variance": gross})
        elif i == 40:
            # Missing in bank (omitted from bank statement)
            truth_records.append({"order_ref": order_ref, "class": "missing_bank_credit", "variance": gross})
        elif i == 50:
            # Duplicate bank deposit
            bank_rows.append({
                "bank_ref": bank_utr,
                "utr": order_ref,
                "credit_inr": net_settled,
                "debit_inr": 0.0,
                "clearing_date": date_str,
                "account_number": "9876543210",
                "status": "CLEARED",
            })
            bank_rows.append({
                "bank_ref": f"{bank_utr}_DUP",
                "utr": order_ref,
                "credit_inr": net_settled,
                "debit_inr": 0.0,
                "clearing_date": date_str,
                "account_number": "9876543210",
                "status": "DUPLICATE_CREDIT",
            })
            truth_records.append({"order_ref": order_ref, "class": "duplicate", "variance": 0.0})
        else:
            # Standard reconciled match
            bank_rows.append({
                "bank_ref": bank_utr,
                "utr": order_ref,
                "credit_inr": net_settled,
                "debit_inr": 0.0,
                "clearing_date": date_str,
                "account_number": "9876543210",
                "status": "CLEARED",
            })
            truth_records.append({"order_ref": order_ref, "class": "matched", "variance": 0.0})

    sales_p = dest_dir / "merchant_sales.csv"
    with open(sales_p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sales_rows[0].keys()))
        w.writeheader()
        w.writerows(sales_rows)

    gw_p = dest_dir / "gateway_settlements.csv"
    with open(gw_p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(settlement_rows[0].keys()))
        w.writeheader()
        w.writerows(settlement_rows)

    bank_p = dest_dir / "bank_statement.csv"
    with open(bank_p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(bank_rows[0].keys()))
        w.writeheader()
        w.writerows(bank_rows)

    # OFFLINE TRUTH FILE: Must NEVER be uploaded to server
    truth_p = dest_dir / "benchmark_truth.jsonl"
    with open(truth_p, "w", encoding="utf-8") as f:
        for rec in truth_records:
            f.write(json.dumps(rec) + "\n")

    print(f"Generated 3-file benchmark set in {dest_dir}:")
    print(f"  - merchant_sales.csv: {len(sales_rows)} rows")
    print(f"  - gateway_settlements.csv: {len(settlement_rows)} rows")
    print(f"  - bank_statement.csv: {len(bank_rows)} rows")
    print(f"  - benchmark_truth.jsonl (OFFLINE ONLY): {len(truth_records)} verified records")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent.parent / "sample_data"
    generate_enterprise_ecosystem(base / "enterprise_ecosystem")
    generate_3file_benchmark(base / "benchmark_3file")
