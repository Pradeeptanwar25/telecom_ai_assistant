# integration/answer_generator.py

import json
import os
from typing import Any, Dict

import truststore
from huggingface_hub import InferenceClient


# ============================================================
# SSL
# ============================================================

truststore.inject_into_ssl()


# ============================================================
# HF TOKEN
# ============================================================

try:
    from django.conf import settings

    HF_TOKEN = getattr(
        settings,
        "HF_TOKEN",
        None,
    )

except Exception:
    HF_TOKEN = None


if not HF_TOKEN:
    HF_TOKEN = os.getenv(
        "HUGGINGFACEHUB_API_TOKEN"
    )

if not HF_TOKEN:
    HF_TOKEN = os.getenv(
        "HF_TOKEN"
    )


if not HF_TOKEN:
    raise ValueError(
        "HF token not found. "
        "Set HF_TOKEN or HUGGINGFACEHUB_API_TOKEN."
    )


# ============================================================
# MODEL
# ============================================================

HF_MODEL = "openai/gpt-oss-20b"


client = InferenceClient(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)


# ============================================================
# EXACT VALUE FORMATTER
# ============================================================

def _format_exact_value(value: Any) -> str:
    """
    Convert database values into readable text.

    Important:
    We do not change the actual value.
    """

    if value is None:
        return "N/A"

    if isinstance(value, float):

        if value.is_integer():
            return str(int(value))

        return str(value)

    return str(value)


# ============================================================
# DETERMINISTIC COUNT ANSWER
# ============================================================

def _count_answer(
    user_question: str,
    query_plan: Dict[str, Any],
    result: Dict[str, Any],
) -> str:
    """
    Generate count answer directly from database result.

    No LLM is used here.

    This is intentional because numerical answers must
    never be hallucinated or modified by the LLM.
    """

    count = result.get("count", 0)

    count_text = _format_exact_value(count)

    return (
        f"Total matching records: {count_text}"
    )


# ============================================================
# DETERMINISTIC EMPTY ANSWER
# ============================================================

def _empty_answer(
    user_question: str,
    query_plan: Dict[str, Any],
    result: Dict[str, Any],
) -> str:
    """
    Exact answer for empty database result.
    """

    return (
        "No matching records found for the given conditions."
    )


# ============================================================
# DETERMINISTIC AGGREGATE ANSWER
# ============================================================

def _aggregate_answer(
    user_question: str,
    query_plan: Dict[str, Any],
    result: Dict[str, Any],
) -> str:
    """
    Format aggregate results.

    The values come directly from PostgreSQL.
    """

    records = result.get(
        "records",
        [],
    )

    if not records:
        return (
            "No matching records found for "
            "the given conditions."
        )

    lines = []

    for row in records:

        if not isinstance(row, dict):
            lines.append(
                _format_exact_value(row)
            )
            continue

        parts = []

        for key, value in row.items():

            if value is None:
                value_text = "N/A"
            else:
                value_text = _format_exact_value(
                    value
                )

            parts.append(
                f"{key}: {value_text}"
            )

        lines.append(
            " | ".join(parts)
        )

    return "\n".join(lines)


# ============================================================
# RECORD ANSWER PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are the final natural-language answer formatter
for a telecom Integration Tracker.

The database result supplied to you is authoritative.

Your job is ONLY to explain the supplied result
in a clear and concise way.

============================================================
STRICT RULES
============================================================

1. NEVER invent a record.

2. NEVER invent a field value.

3. NEVER change a number.

4. NEVER change a date.

5. NEVER change a site ID.

6. NEVER change an activity name.

7. NEVER change an OEM.

8. NEVER change a circle.

9. NEVER infer information that is not present.

10. If the database result contains a value, preserve
    that value exactly.

11. If a value is null, treat it as N/A.

12. If there are multiple records, clearly separate them.

13. If the user asks in Hinglish, answer in simple Hinglish.

14. If the user asks in English, answer in English.

15. Keep the response concise but useful.

16. Do not mention:
    - Django
    - Python
    - PostgreSQL
    - ORM
    - query parser
    - validator
    - internal architecture
    - LLM
    - model
    - database implementation

17. Do not say that the information came from Excel
    unless the user specifically asks about the source.

18. The DATABASE RESULT is the source of truth.

19. If the DATABASE RESULT does not contain enough
    information to answer the question, say that the
    available result does not contain enough information.

20. Do not perform your own calculations unless the
    calculation is directly represented by the supplied
    result.

============================================================
"""


# ============================================================
# RETRIEVE ANSWER
# ============================================================

def _retrieve_answer(
    user_question: str,
    query_plan: Dict[str, Any],
    result: Dict[str, Any],
) -> str:
    """
    Use LLM only for natural-language presentation
    of retrieved records.

    Factual values remain inside the supplied result.
    """

    records = result.get(
        "records",
        [],
    )

    count = result.get(
        "count",
        len(records),
    )

    if not records:
        return _empty_answer(
            user_question=user_question,
            query_plan=query_plan,
            result=result,
        )

    # --------------------------------------------------------
    # Limit the context sent to LLM.
    #
    # Important:
    # This does NOT change the actual DB result.
    # It only prevents an extremely large prompt.
    # --------------------------------------------------------

    preview_records = records[:100]

    result_payload = {
        "count": count,
        "records": preview_records,
    }

    user_prompt = f"""
USER QUESTION:
{user_question}

QUERY PLAN:
{json.dumps(
    query_plan,
    ensure_ascii=False,
    default=str,
)}

DATABASE RESULT:
{json.dumps(
    result_payload,
    ensure_ascii=False,
    default=str,
)}

Generate the final answer using ONLY the
DATABASE RESULT.

Preserve all factual values exactly.
"""

    response = client.chat.completions.create(
        model=HF_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        max_tokens=1600,
        temperature=0.0,
        extra_body={
            "reasoning_effort": "low"
        },
    )

    if not response.choices:
        raise ValueError(
            "LLM returned no answer."
        )

    answer = response.choices[0].message.content

    if not answer:
        raise ValueError(
            "LLM returned an empty answer."
        )

    return answer.strip()


# ============================================================
# MAIN ANSWER GENERATOR
# ============================================================

def generate_answer(
    user_question: str,
    query_plan: Dict[str, Any],
    result: Dict[str, Any],
) -> str:
    """
    Generate final user-facing answer.

    Flow:

        Query Result
             ↓
        operation?
             ↓
        count       → deterministic Python answer
        aggregate   → deterministic Python answer
        retrieve    → LLM presentation
    """

    if not isinstance(
        query_plan,
        dict,
    ):
        raise ValueError(
            "query_plan must be a dictionary."
        )

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError(
            "result must be a dictionary."
        )

    operation = str(
        query_plan.get(
            "operation",
            "retrieve",
        )
    ).strip().lower()

    # ========================================================
    # COUNT
    # ========================================================
    #
    # IMPORTANT:
    #
    # Do NOT send count to LLM.
    #
    # This prevents:
    #
    # DB → 3952
    # LLM → 89691 ❌
    #
    # ========================================================

    if operation == "count":

        return _count_answer(
            user_question=user_question,
            query_plan=query_plan,
            result=result,
        )

    # ========================================================
    # AGGREGATE
    # ========================================================

    if operation == "aggregate":

        return _aggregate_answer(
            user_question=user_question,
            query_plan=query_plan,
            result=result,
        )

    # ========================================================
    # RETRIEVE
    # ========================================================

    if operation == "retrieve":

        return _retrieve_answer(
            user_question=user_question,
            query_plan=query_plan,
            result=result,
        )

    # ========================================================
    # UNKNOWN
    # ========================================================

    raise ValueError(
        f"Unsupported operation: {operation}"
    )