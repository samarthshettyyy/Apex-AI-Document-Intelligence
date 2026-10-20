CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    city TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    loan_type TEXT NOT NULL,
    approved_amount NUMERIC(14,2) NOT NULL CHECK (approved_amount > 0),
    interest_rate NUMERIC(5,2) NOT NULL CHECK (interest_rate >= 0),
    tenure_months INTEGER NOT NULL CHECK (tenure_months > 0),
    loan_status TEXT NOT NULL CHECK (loan_status IN ('approved','active','closed','on_hold')),
    approved_on DATE NOT NULL
);
CREATE TABLE IF NOT EXISTS loan_approvals (
    approval_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL REFERENCES loans(loan_id),
    approver_ref TEXT NOT NULL,
    approval_status TEXT NOT NULL CHECK (approval_status IN ('approved','rejected','pending')),
    approved_at TIMESTAMPTZ,
    remarks TEXT
);
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL REFERENCES loans(loan_id),
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('disbursement','repayment','reversal','adjustment')),
    amount NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    transaction_status TEXT NOT NULL CHECK (transaction_status IN ('posted','pending','failed','reversed')),
    transaction_date TIMESTAMPTZ NOT NULL,
    reference_number TEXT NOT NULL UNIQUE,
    beneficiary_name TEXT NOT NULL,
    beneficiary_account_ref TEXT NOT NULL,
    reversal_of_transaction_id TEXT REFERENCES transactions(transaction_id),
    demo_scenario TEXT
);
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    loan_id TEXT REFERENCES loans(loan_id),
    document_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_sha256 TEXT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    document_status TEXT NOT NULL DEFAULT 'registered'
        CHECK (document_status IN ('registered','processed','under_review','cleared'))
);
CREATE TABLE IF NOT EXISTS reconciliation_cases (
    case_id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(document_id),
    transaction_id TEXT REFERENCES transactions(transaction_id),
    extracted_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    findings JSONB NOT NULL DEFAULT '{}'::jsonb,
    review_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending','in_review','cleared','escalated')),
    reviewer_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_loans_customer ON loans(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_loan ON transactions(loan_id);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_reconciliation_status ON reconciliation_cases(review_status);
