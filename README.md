# Telecom AI Assistant

A Streamlit app for asking natural-language questions about a telecom Integration Tracker. It uses a Hugging Face model to turn questions into structured filters, validates the query, runs it against PostgreSQL, and presents results from the tracker.

Designed for English, Hindi, and Hinglish questions, including record lookup, counts, combined filters, grouped summaries, date ranges, sorting, and pagination. Answers should be checked against the source tracker, especially when a question is ambiguous.

## How It Works

1. Streamlit collects the user's question.
2. The Hugging Face model proposes a structured query plan.
3. The parser and validator normalize and check the plan.
4. Django queries the PostgreSQL `integration` database.
5. The app displays the result and can export retrieved records.

Counts and aggregate values are formatted from query results. Natural-language interpretation still depends on the model and the wording of the question.

## Requirements

- Python 3.13
- PostgreSQL
- A Hugging Face Inference API token with available credits
- The tracker CSV file

## Setup (Windows PowerShell)

Create and activate a virtual environment, then install the app dependencies:

```powershell
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install django streamlit pandas huggingface_hub python-dotenv truststore "psycopg[binary]" openpyxl
```

Create or update `.env` in the project root using `.env.example`. Preserve any existing values, and set the following locally:

```dotenv
HUGGINGFACEHUB_API_TOKEN=your_token_here
DJANGO_SECRET_KEY=your_private_random_key
DJANGO_DEBUG=True
DEFAULT_DB_NAME=telecom_ai_db
DEFAULT_DB_USER=postgres
DEFAULT_DB_PASSWORD=your_default_database_password
DEFAULT_DB_HOST=localhost
DEFAULT_DB_PORT=5432
INTEGRATION_DB_NAME=telecom_integration_db
INTEGRATION_DB_USER=postgres
INTEGRATION_DB_PASSWORD=your_integration_database_password
INTEGRATION_DB_HOST=localhost
INTEGRATION_DB_PORT=5432
```

Generate a Django secret key locally with `python -c "import secrets; print(secrets.token_urlsafe(50))"`. Do not commit `.env` or share its contents. The app reads tracker records from the `integration` PostgreSQL database; that database and its tables must be available before launching the app.

Apply migrations to the integration database:

```powershell
python manage.py migrate --database integration
```

Import the tracker CSV once into an empty integration database:

```powershell
python manage.py import_integration "integration/Range_Wise_Integration_Tracker (1).csv"
```

The import command appends records; it does not clear or replace existing rows. Re-running it can create duplicate records.

## Run

```powershell
streamlit run app.py
```

Streamlit prints the local URL when the server starts.

## Tests

Run the focused parser and import tests:

```powershell
python manage.py test integration.tests
```

The live AI integration tests make requests to Hugging Face and require working inference credits:

```powershell
python test_integration_ai.py
```

## Data and Credential Safety

- Do not commit `.env`, API tokens, database passwords, Django secret keys, or private tracker data.
- Keep credentials in `.env` and rotate any credentials that were previously hard-coded in the source before publishing this project.
- Keep private CSV files, vector databases, and generated reports out of a public repository unless you have confirmed they are safe to share.
