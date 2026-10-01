import json
import os

import truststore
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda


# ============================================================
# SSL / ENVIRONMENT SETUP
# ============================================================

truststore.inject_into_ssl()

load_dotenv(override=True)

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if not HF_TOKEN:
    raise ValueError(
        "HUGGINGFACEHUB_API_TOKEN is not set in .env"
    )


# ============================================================
# HUGGING FACE CLIENT
# ============================================================

client = InferenceClient(
    api_key=HF_TOKEN
)


# ============================================================
# ANSWER PROMPT
# ============================================================

answer_prompt = PromptTemplate.from_template(
    """
You are the final response assistant for a telecom DPR system.

The database/search system has already executed the user's request.

Your job is ONLY to explain the provided result to the employee
in simple, short and clear language.

IMPORTANT RULES:

1. Use ONLY the information present in DATABASE RESULT.
2. Do NOT invent information.
3. Do NOT change database values.
4. Do NOT create or modify records.
5. Do NOT make assumptions about records that are not provided.
6. Do NOT mention internal implementation such as:
   - PostgreSQL
   - ChromaDB
   - Django
   - Python
   - LangChain
   - Hugging Face
   - LLM
   - embeddings
   - vector database

REPORT RULE:

- Check the value of "report_requested".
- If report_requested is false:
  NEVER mention Excel, CSV, report download, or report readiness.
- If report_requested is true:
  You may mention that the requested report is ready for download.

COUNT RULE:

- Use the exact value of "total_matching_records"
  when mentioning the number of records.
- Never invent or estimate a count.

IF NO RECORDS:

- Clearly say that no matching records were found.

IF RECORDS ARE FOUND:

- Clearly mention the number of records found.
- Keep the answer concise.
- The detailed records are already shown separately in the UI.

SEMANTIC SEARCH RULE:

If this is a semantic search, describe the results as
relevant/matching records based on the user's query.
Do not claim that every record in the database matches.

USER QUERY
{user_query}

DATABASE RESULT
{context}

REPORT REQUESTED
{report_requested}

Return ONLY the employee-facing answer.
"""
)


# ============================================================
# HUGGING FACE CALL
# ============================================================

def call_huggingface_chat(prompt):
    prompt_text = prompt.to_string()

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt_text
            }
        ],
        max_tokens=1000,
        extra_body={
            "reasoning_effort": "low"
        }
    )

    return response.choices[0].message.content


# ============================================================
# LANGCHAIN ANSWER CHAIN
# ============================================================

answer_chain = (
    answer_prompt
    | RunnableLambda(call_huggingface_chat)
    | StrOutputParser()
)


# ============================================================
# FINAL EMPLOYEE ANSWER
# ============================================================

def generate_employee_answer(
    user_query,
    parsed_query,
    record_count,
    records
):
    """
    Generate the final employee-facing answer.

    LLM #2 receives:
    - Original user question
    - Parsed query
    - Exact number of retrieved records
    - Sample records
    - Whether a report was actually requested
    """

    # --------------------------------------------------------
    # Determine whether user actually requested a report
    # --------------------------------------------------------

    intent = parsed_query.get("intent", "")
    output_format = parsed_query.get("output_format", "")

    report_requested = (
        intent == "report"
        or output_format in ["excel", "csv"]
    )

    # --------------------------------------------------------
    # Send only a small sample of records to LLM
    # --------------------------------------------------------

    sample_records = records[:10]

    context = {
        "parsed_query": parsed_query,
        "total_matching_records": record_count,
        "sample_records": sample_records,
    }

    context_text = json.dumps(
        context,
        default=str,
        indent=2
    )

    # --------------------------------------------------------
    # Generate answer
    # --------------------------------------------------------

    answer = answer_chain.invoke(
        {
            "user_query": user_query,
            "context": context_text,
            "report_requested": report_requested,
        }
    )

    answer = answer.strip()

    return answer