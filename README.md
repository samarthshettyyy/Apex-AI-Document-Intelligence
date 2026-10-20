# Apex Bank — Dummy Bank Portal

A local Streamlit + PostgreSQL prototype for an AI-assisted loan reconciliation demo. All records are synthetic.

## 1. Create the PostgreSQL database
Open PowerShell and run `psql -U postgres -h localhost`. At the PostgreSQL prompt:
```sql
CREATE DATABASE apex_bank;
\q
```
If `psql` is not recognized, open **SQL Shell (psql)** from the Windows Start menu.

## 2. Set up Python
Run these commands from the extracted project folder:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
If activation is blocked, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Configure the database connection
```powershell
Copy-Item .env.example .env
```
Open `.env` and replace `YOUR_POSTGRES_PASSWORD` with your local PostgreSQL password. Keep `.env` private.

## 4. Seed synthetic records
```powershell
python -m database.seed_data
```
**Warning:** the seed script truncates and recreates data in this demo database. Never run it against a real or important database.

## 5. Start the portal
```powershell
python -m streamlit run app.py
```
Open the local URL printed in the terminal, usually `http://localhost:8501`.

## Pages
Dashboard, Customers, Loan Management, Approvals, Transaction Ledger, and Document Registry.

## Next milestone
Receipt upload, SHA-256 hashing, OCR/structured extraction, deterministic reconciliation rules, and human-review outcomes. A discrepancy is a review signal, not proof of fraud.
