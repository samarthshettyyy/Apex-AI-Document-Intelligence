import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from faker import Faker
from psycopg.types.json import Jsonb
from database.connection import get_connection

SEED = 20261017
random.seed(SEED)
Faker.seed(SEED)
fake = Faker("en_IN")
ROOT = Path(__file__).resolve().parents[1]

def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute((ROOT / "database" / "schema.sql").read_text(encoding="utf-8"))
            # Demo-only reset. Never point this script at a real database.
            cur.execute("""
                TRUNCATE TABLE reconciliation_cases, audit_log, documents, transactions,
                loan_approvals, loans, customers RESTART IDENTITY CASCADE
            """)

            customers = []
            for i in range(1, 31):
                customers.append({
                    "customer_id": f"CUST-{i:04d}",
                    "full_name": fake.name(),
                    "email": f"customer{i:03d}@example.test",
                    "phone": f"+91-9{random.randint(100000000, 999999999)}",
                    "city": fake.city(),
                })
            cur.executemany("""
                INSERT INTO customers (customer_id, full_name, email, phone, city)
                VALUES (%(customer_id)s, %(full_name)s, %(email)s, %(phone)s, %(city)s)
            """, customers)

            loans, approvals = [], []
            loan_types = ["Personal Loan", "Home Loan", "Vehicle Loan", "Education Loan", "Business Loan"]
            loan_statuses = ["active", "active", "active", "approved", "closed", "on_hold"]
            for i, customer in enumerate(customers, 1):
                status = loan_statuses[(i - 1) % len(loan_statuses)]
                approved_on = date(2025, 1, 1) + timedelta(days=random.randint(0, 620))
                loans.append({
                    "loan_id": f"LOAN-{i:04d}", "customer_id": customer["customer_id"],
                    "loan_type": random.choice(loan_types),
                    "approved_amount": random.choice([150000, 250000, 400000, 650000, 900000, 1200000]),
                    "interest_rate": round(random.uniform(8.25, 16.5), 2),
                    "tenure_months": random.choice([12, 24, 36, 48, 60, 84, 120]),
                    "loan_status": status, "approved_on": approved_on,
                })
                pending = status == "on_hold"
                approvals.append({
                    "approval_id": f"APR-{i:04d}", "loan_id": f"LOAN-{i:04d}",
                    "approver_ref": f"EMP-{random.randint(100, 125)}",
                    "approval_status": "pending" if pending else "approved",
                    "approved_at": None if pending else datetime.combine(approved_on, datetime.min.time(), tzinfo=timezone.utc),
                    "remarks": "Awaiting supporting documentation" if pending else "Approved under demo lending policy",
                })

            cur.executemany("""
                INSERT INTO loans
                (loan_id, customer_id, loan_type, approved_amount, interest_rate, tenure_months, loan_status, approved_on)
                VALUES (%(loan_id)s, %(customer_id)s, %(loan_type)s, %(approved_amount)s, %(interest_rate)s, %(tenure_months)s, %(loan_status)s, %(approved_on)s)
            """, loans)
            cur.executemany("""
                INSERT INTO loan_approvals
                (approval_id, loan_id, approver_ref, approval_status, approved_at, remarks)
                VALUES (%(approval_id)s, %(loan_id)s, %(approver_ref)s, %(approval_status)s, %(approved_at)s, %(remarks)s)
            """, approvals)

            txns, counter = [], 1
            now = datetime.now(timezone.utc)
            def add_txn(loan_index, kind, amount, status, days_ago, scenario, reversal_of=None):
                nonlocal counter
                loan, customer = loans[loan_index - 1], customers[loan_index - 1]
                txns.append({
                    "transaction_id": f"TXN-{counter:05d}", "loan_id": loan["loan_id"],
                    "customer_id": customer["customer_id"], "transaction_type": kind,
                    "amount": amount, "currency": "INR", "transaction_status": status,
                    "transaction_date": now - timedelta(days=days_ago, hours=random.randint(0, 12)),
                    "reference_number": f"APXREF{counter:08d}",
                    "beneficiary_name": customer["full_name"],
                    "beneficiary_account_ref": f"XXXXXX{random.randint(1000, 9999)}",
                    "reversal_of_transaction_id": reversal_of, "demo_scenario": scenario,
                })
                counter += 1
                return txns[-1]["transaction_id"]

            for i, loan in enumerate(loans, 1):
                amount = round(float(loan["approved_amount"]) * random.choice([0.35, 0.5, 0.7, 1.0]), 2)
                if i == 2:
                    add_txn(i, "disbursement", round(float(loan["approved_amount"]) * .4, 2), "posted", 18, "partial_disbursement")
                    add_txn(i, "disbursement", round(float(loan["approved_amount"]) * .6, 2), "posted", 12, "partial_disbursement")
                elif i == 5:
                    add_txn(i, "disbursement", amount, "pending", 2, "pending_transaction")
                else:
                    add_txn(i, "disbursement", amount, "posted", random.randint(1, 220), "standard_disbursement")

            for i in range(3, 31, 3):
                add_txn(i, "repayment", random.choice([5000, 8500, 12000, 18000]), "posted",
                        random.randint(1, 60), "standard_repayment")

            first_txn_id = txns[0]["transaction_id"]
            txns[0]["transaction_status"] = "reversed"
            add_txn(1, "reversal", txns[0]["amount"], "posted", 3, "reversal_example", first_txn_id)

            cur.executemany("""
                INSERT INTO transactions
                (transaction_id, loan_id, customer_id, transaction_type, amount, currency,
                 transaction_status, transaction_date, reference_number, beneficiary_name,
                 beneficiary_account_ref, reversal_of_transaction_id, demo_scenario)
                VALUES (%(transaction_id)s, %(loan_id)s, %(customer_id)s, %(transaction_type)s,
                 %(amount)s, %(currency)s, %(transaction_status)s, %(transaction_date)s,
                 %(reference_number)s, %(beneficiary_name)s, %(beneficiary_account_ref)s,
                 %(reversal_of_transaction_id)s, %(demo_scenario)s)
            """, txns)

            docs = []
            for i in range(1, 9):
                docs.append({
                    "document_id": f"DOC-{i:04d}", "customer_id": customers[i-1]["customer_id"],
                    "loan_id": loans[i-1]["loan_id"], "document_type": "Loan Disbursement Receipt",
                    "file_name": f"sample_disbursement_receipt_{i:02d}.pdf",
                    "file_sha256": None, "document_status": "registered",
                })
            cur.executemany("""
                INSERT INTO documents
                (document_id, customer_id, loan_id, document_type, file_name, file_sha256, document_status)
                VALUES (%(document_id)s, %(customer_id)s, %(loan_id)s, %(document_type)s, %(file_name)s, %(file_sha256)s, %(document_status)s)
            """, docs)
            cur.execute("""
                INSERT INTO audit_log (entity_type, entity_id, action, actor_ref, details)
                VALUES (%s, %s, %s, %s, %s)
            """, ("system", "SEED-20261017", "DEMO_DATA_SEEDED", "SYSTEM",
                  Jsonb({"customers": len(customers), "loans": len(loans), "transactions": len(txns), "documents": len(docs)})))
        conn.commit()
    print("Demo data created. Customers:", len(customers), "| Loans:", len(loans),
          "| Transactions:", len(txns), "| Registered documents:", len(docs))
    print("All records are fictional.")

if __name__ == "__main__":
    main()
