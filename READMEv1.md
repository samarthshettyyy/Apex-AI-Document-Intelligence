# Apex — AI Document Intelligence

An AI-powered financial document processing prototype that extracts structured transaction details from bank receipts and supports human review through a Streamlit interface.

Apex combines vision-based language-model extraction with traditional OCR to help reviewers inspect document-derived transaction data before verification. It is a proof of concept for financial operations workflows—not a production banking system.

## Why Apex?

Financial operations teams often need to review information contained in receipts and transaction documents. Manually transcribing these details can be repetitive, and scanned or low-quality documents can be difficult to process consistently.

Apex explores an AI-assisted workflow that turns a receipt into structured fields, validates the output, and gives a reviewer a place to inspect the result.

## Features

- **Vision-based extraction:** Uses a vision-capable language model to interpret financial receipt images or rendered document pages.
- **OCR comparison:** Uses Tesseract OCR alongside the vision-based extraction workflow to provide an additional text-recognition path.
- **Structured output:** Organizes extracted transaction information into machine-readable fields for downstream review.
- **Validation and human review:** Supports checking extracted details before they are treated as verified records.
- **Banking operations portal:** Streamlit interface for document management and review-related workflows.
- **PostgreSQL integration:** Stores application data, including document and transaction-related records.
- **Document extraction records:** Includes a database migration for storing extraction results.

> **Current scope:** This is a prototype. Handwritten-receipt performance has not yet been established through a formal evaluation. Extraction results should be reviewed by a human and must not be treated as proof of fraud or as a final financial decision.

## How it works

1. A reviewer uploads a financial document through the portal.
2. The document is processed for AI-based extraction, with OCR available as a complementary text-recognition path.
3. Extracted details are returned in a structured format and checked for validity.
4. The reviewer inspects the result and resolves uncertain or inconsistent information before using it.
5. Application records are managed through the Streamlit portal and PostgreSQL database.

## Tech stack

- **Language:** Python
- **AI extraction:** Groq API with a vision-capable model configured through environment variables
- **OCR:** Tesseract
- **Web application:** Streamlit
- **Database:** PostgreSQL
- **Data validation:** Structured validation in the extraction workflow

## Project structure

```text
apex_bank_portal/
├── app.py
├── appv1.py
├── ocr_service.py
├── requirements.txt
├── .env.example
├── database/
│   ├── 001_document_extractions.sql
│   ├── connection.py
│   ├── schema.sql
│   └── seed_data.py
├── uploads/                 # Local document uploads; excluded from Git
└── README.md
```

## Getting started

These instructions assume Windows and PowerShell.

### 1. Clone the repository

```powershell
git clone https://github.com/samarthshettyyy/Apex-AI-Document-Intelligence.git
cd Apex-AI-Document-Intelligence
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python executable directly or adjust your local execution policy according to your organization's security guidance.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and fill in the configuration values required by the application, such as your Groq API key, model setting, database connection details, and Tesseract executable path if required.

**Never commit `.env` or publish API keys.** Keep secrets in your local environment and use `.env.example` only for placeholder configuration names.

### 5. Configure PostgreSQL

Install and start PostgreSQL, then create a database for the prototype. Configure the connection details in `.env`.

Apply the schema and extraction migration using your PostgreSQL tools. For example, if `psql` is available on your PATH:

```powershell
psql -U <your_postgres_user> -d <your_database_name> -f database/schema.sql
psql -U <your_postgres_user> -d <your_database_name> -f database/001_document_extractions.sql
```

If the project requires sample data, review `database/seed_data.py` and run it using the project's configured Python environment. Do not run seed scripts against a real banking database.

### 6. Install and configure Tesseract OCR

Install Tesseract OCR for Windows if it is not already installed. If the executable is not available on your PATH, set the path in `.env` according to the variable name documented in `.env.example` and used by the application.

### 7. Run the application

```powershell
streamlit run app.py
```

If your local setup uses a different entry point, check the project code and README configuration before running it.

## Configuration

Check `.env.example` for the exact environment-variable names expected by this version of the project. Typical configuration includes:

- Groq API key
- Vision model identifier
- PostgreSQL connection settings
- Tesseract executable path (if needed)

Do not put real credentials in this README, screenshots, issues, or commit history.

## Responsible use and limitations

- **Human review is required.** Extracted fields can be missing, incorrect, or ambiguous.
- **A discrepancy is a review signal, not proof of fraud.** Confirm findings against reliable source records and established procedures.
- **No production claim.** This project is a learning and demonstration prototype and has not been represented as a production banking system.
- **Handwriting needs evaluation.** Performance on handwritten receipts should be tested using a representative dataset before making accuracy claims.
- **Use synthetic data for demos.** Do not upload real customer documents or sensitive financial information to a public repository or third-party service without appropriate authorization and safeguards.

## Roadmap

- Evaluate extraction quality on a representative set of printed and handwritten receipts.
- Measure field-level accuracy, missing-field rate, and reviewer correction rate.
- Improve handling of low-quality scans, ambiguous handwriting, and multi-page documents.
- Add clearer confidence indicators and exception-review states.
- Add demo screenshots or a short walkthrough using fictional sample documents.

## Demo data

Use fictional or synthetic receipts when demonstrating the project. Any sample document should be clearly marked as fictional and must not contain real account numbers, personal data, or transaction details.

## Contributing and feedback

Suggestions and issues are welcome. Please do not include API keys, private documents, personal information, or real financial records in public issues.

## Disclaimer

Apex is an experimental AI document-processing prototype intended for demonstration and learning. It does not provide financial, legal, compliance, or fraud determinations. All extracted information requires appropriate verification.
