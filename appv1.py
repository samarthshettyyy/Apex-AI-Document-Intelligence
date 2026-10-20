import hashlib
import uuid
from pathlib import Path
import os
from ocr_service import process_document
import pandas as pd
import streamlit as st
from psycopg.types.json import Jsonb
from database.connection import get_connection

st.set_page_config(page_title="Apex Bank | Operations", page_icon="🏦", layout="wide")
PROJECT_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = PROJECT_ROOT / "uploads"
MAX_UPLOAD_MB = 15
ALLOWED_TYPES = ["pdf", "png", "jpg", "jpeg"]

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #f5f7fb; padding: 16px 18px; border-radius: 12px; border: 1px solid #e5eaf2;}
[data-testid="stSidebar"] {border-right: 1px solid #e5eaf2;}
</style>
""", unsafe_allow_html=True)

def query_df(sql, params=None):
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def money(value):
    return f"₹{float(value or 0):,.0f}"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def register_document(customer_id, loan_id, document_type, original_name, file_bytes):
    """Save an upload locally and register its metadata in PostgreSQL."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg"}:
        raise ValueError("Unsupported file extension.")
    if len(file_bytes) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"File exceeds the {MAX_UPLOAD_MB} MB limit.")

    digest = sha256_bytes(file_bytes)
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    storage_path = UPLOAD_DIR / stored_name
    storage_path.write_bytes(file_bytes)
    document_id = f"DOC-{uuid.uuid4().hex[:10].upper()}"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO documents
                    (document_id, customer_id, loan_id, document_type, file_name, file_sha256, document_status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'registered')
                """, (document_id, customer_id, loan_id or None, document_type, stored_name, digest))
                cur.execute("""
                    INSERT INTO audit_log (entity_type, entity_id, action, actor_ref, details)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("document", document_id, "DOCUMENT_UPLOADED", "DEMO_REVIEWER", Jsonb({
                    "original_filename": original_name,
                    "stored_filename": stored_name,
                    "sha256": digest,
                    "size_bytes": len(file_bytes),
                    "document_type": document_type,
                })))
            conn.commit()
    except Exception:
        storage_path.unlink(missing_ok=True)
        raise
    return document_id, digest, stored_name

st.sidebar.markdown("# 🏦 Apex Bank")
st.sidebar.caption("Internal Operations Portal · DEMO")
page = st.sidebar.radio("Navigation", [
    "Dashboard", "Customers", "Loan Management", "Approvals",
    "Transaction Ledger", "Document Registry"
])
st.sidebar.divider()
st.sidebar.caption("Fictional data for demonstration only.")

try:
    if page == "Dashboard":
        st.title("Operations Dashboard")
        st.caption("Overview of lending activity and transaction operations.")
        m = query_df("""
          SELECT (SELECT COUNT(*) FROM customers) customers,
                 (SELECT COUNT(*) FROM loans) loans,
                 (SELECT COUNT(*) FROM transactions) transactions,
                 (SELECT COUNT(*) FROM transactions WHERE transaction_status='pending') pending_txns,
                 (SELECT COUNT(*) FROM loan_approvals WHERE approval_status='pending') pending_approvals,
                 (SELECT COALESCE(SUM(amount),0) FROM transactions
                  WHERE transaction_type='disbursement' AND transaction_status='posted') posted_disbursements
        """).iloc[0]
        a, b, c = st.columns(3)
        a.metric("Customers", f"{int(m['customers']):,}")
        b.metric("Loan Accounts", f"{int(m['loans']):,}")
        c.metric("Transactions", f"{int(m['transactions']):,}")
        a, b, c = st.columns(3)
        a.metric("Pending Transactions", f"{int(m['pending_txns']):,}")
        b.metric("Pending Approvals", f"{int(m['pending_approvals']):,}")
        c.metric("Posted Disbursements", money(m["posted_disbursements"]))
        left, right = st.columns(2)
        with left:
            st.subheader("Transaction status")
            d = query_df("SELECT transaction_status status, COUNT(*) count FROM transactions GROUP BY 1 ORDER BY 2 DESC")
            if not d.empty:
                st.bar_chart(d.set_index("status"))
        with right:
            st.subheader("Loan portfolio by type")
            d = query_df("SELECT loan_type, COUNT(*) accounts FROM loans GROUP BY 1 ORDER BY 2 DESC")
            if not d.empty:
                st.bar_chart(d.set_index("loan_type"))
        st.subheader("Recent transactions")
        d = query_df("""
          SELECT t.transaction_id, t.reference_number, c.full_name customer, t.loan_id,
                 t.transaction_type, t.amount, t.currency, t.transaction_status, t.transaction_date
          FROM transactions t JOIN customers c USING(customer_id)
          ORDER BY t.transaction_date DESC LIMIT 12
        """)
        st.dataframe(d, use_container_width=True, hide_index=True)

    elif page == "Customers":
        st.title("Customer Directory")
        st.caption("Fictional customer records held by Apex Bank.")
        q = st.text_input("Search by customer ID, name, email, or city")
        term = f"%{q}%"
        d = query_df("""
          SELECT customer_id, full_name, email, phone, city, created_at FROM customers
          WHERE (%s='' OR customer_id ILIKE %s OR full_name ILIKE %s OR email ILIKE %s OR city ILIKE %s)
          ORDER BY customer_id
        """, (q, term, term, term, term))
        st.dataframe(d, use_container_width=True, hide_index=True)
        st.caption(f"{len(d)} customer record(s) shown.")

    elif page == "Loan Management":
        st.title("Loan Management")
        a, b = st.columns(2)
        with a:
            sf = st.selectbox("Loan status", ["All", "active", "approved", "closed", "on_hold"])
        with b:
            tf = st.selectbox("Loan type", ["All", "Personal Loan", "Home Loan", "Vehicle Loan", "Education Loan", "Business Loan"])
        d = query_df("""
          SELECT l.loan_id, c.full_name customer, l.loan_type, l.approved_amount, l.interest_rate,
                 l.tenure_months, l.loan_status, l.approved_on
          FROM loans l JOIN customers c USING(customer_id)
          WHERE (%s='All' OR l.loan_status=%s) AND (%s='All' OR l.loan_type=%s)
          ORDER BY l.approved_on DESC
        """, (sf, sf, tf, tf))
        st.dataframe(d, use_container_width=True, hide_index=True)
        total = pd.to_numeric(d["approved_amount"]).sum() if not d.empty else 0
        st.caption(f"{len(d)} loan(s) · Approved amount in current view: {money(total)}")

    elif page == "Approvals":
        st.title("Loan Approvals")
        sf = st.selectbox("Approval status", ["All", "approved", "rejected", "pending"])
        d = query_df("""
          SELECT a.approval_id, a.loan_id, c.full_name customer, a.approver_ref,
                 a.approval_status, a.approved_at, a.remarks
          FROM loan_approvals a JOIN loans l USING(loan_id) JOIN customers c USING(customer_id)
          WHERE (%s='All' OR a.approval_status=%s)
          ORDER BY CASE a.approval_status WHEN 'pending' THEN 0 ELSE 1 END, a.approval_id
        """, (sf, sf))
        st.dataframe(d, use_container_width=True, hide_index=True)

    elif page == "Transaction Ledger":
        st.title("Transaction Ledger")
        st.caption("Reference numbers and masked account references are fictional.")
        a, b, c = st.columns(3)
        with a:
            sf = st.selectbox("Status", ["All", "posted", "pending", "failed", "reversed"])
        with b:
            tf = st.selectbox("Transaction type", ["All", "disbursement", "repayment", "reversal", "adjustment"])
        with c:
            q = st.text_input("Search transaction / loan / reference")
        term = f"%{q}%"
        d = query_df("""
          SELECT t.transaction_id, t.reference_number, t.loan_id, c.full_name customer,
                 t.transaction_type, t.amount, t.currency, t.transaction_status, t.transaction_date,
                 t.beneficiary_name, t.beneficiary_account_ref, t.reversal_of_transaction_id
          FROM transactions t JOIN customers c USING(customer_id)
          WHERE (%s='All' OR t.transaction_status=%s) AND (%s='All' OR t.transaction_type=%s)
            AND (%s='' OR t.transaction_id ILIKE %s OR t.loan_id ILIKE %s
                 OR t.reference_number ILIKE %s OR c.full_name ILIKE %s)
          ORDER BY t.transaction_date DESC
        """, (sf, sf, tf, tf, q, term, term, term, term))
        st.dataframe(d, use_container_width=True, hide_index=True)
        st.caption(f"{len(d)} transaction(s) match the selected filters.")

    elif page == "Document Registry":
        st.title("Document Upload & Registry")
        st.caption("Upload a PDF or image. The file is stored locally; metadata is saved to PostgreSQL.")
        st.warning("Prototype only: use synthetic or sanitized documents. Do not upload real customer or banking records.")
        customers = query_df("SELECT customer_id, full_name FROM customers ORDER BY customer_id")
        loans = query_df("""
            SELECT l.loan_id, l.customer_id, c.full_name
            FROM loans l JOIN customers c USING(customer_id) ORDER BY l.loan_id
        """)
        if customers.empty:
            st.info("No customers found. Run the seed script first.")
        else:
            customer_options = {
                f"{r.customer_id} — {r.full_name}": r.customer_id
                for r in customers.itertuples(index=False)
            }
            with st.form("document_upload_form", clear_on_submit=True):
                customer_label = st.selectbox("Customer", list(customer_options.keys()))
                customer_id = customer_options[customer_label]
                eligible_loans = loans[loans["customer_id"] == customer_id]
                loan_options = {"No linked loan": None}
                for r in eligible_loans.itertuples(index=False):
                    loan_options[f"{r.loan_id} — {r.full_name}"] = r.loan_id
                loan_label = st.selectbox("Linked loan (optional)", list(loan_options.keys()))
                document_type = st.selectbox("Document category", [
                    "Loan Disbursement Receipt", "Loan Sanction Letter",
                    "Repayment Receipt", "Bank Statement", "Other"
                ])
                uploaded = st.file_uploader("Choose a document", type=ALLOWED_TYPES,
                    help=f"PDF or image; maximum {MAX_UPLOAD_MB} MB.")
                submitted = st.form_submit_button("Upload and register", type="primary")

            if submitted:
                if uploaded is None:
                    st.error("Choose a PDF or image first.")
                elif uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
                    st.error(f"File exceeds the {MAX_UPLOAD_MB} MB limit.")
                else:
                    try:
                        doc_id, digest, stored_name = register_document(
                            customer_id, loan_options[loan_label], document_type,
                            uploaded.name, uploaded.getvalue()
                        )
                        st.success(f"Document registered: {doc_id}")
                        st.write(f"**Stored file:** `uploads/{stored_name}`")
                        st.write(f"**SHA-256:** `{digest}`")
                        st.info("OCR is not enabled yet. Next, we'll extract fields and show evidence for review.")
                    except Exception as exc:
                        st.error("Upload could not be registered.")
                        with st.expander("Technical details"):
                            st.code(str(exc))

        st.divider()
        st.subheader("Registered documents")
        d = query_df("""
          SELECT d.document_id, d.file_name AS stored_filename, d.document_type,
                 d.customer_id, c.full_name customer, d.loan_id, d.file_sha256,
                 d.document_status, d.uploaded_at
          FROM documents d JOIN customers c USING(customer_id)
          ORDER BY d.uploaded_at DESC, d.document_id
        """)
        st.dataframe(d, use_container_width=True, hide_index=True)
        st.caption(f"{len(d)} document(s) registered. Original filenames are recorded in the audit log.")

except Exception as exc:
    st.error("Could not connect to the Apex Bank database or load this page.")
    st.markdown("Check PostgreSQL, the `apex_bank` database, and your `.env` settings.")
    with st.expander("Technical details"):
        st.code(str(exc))
