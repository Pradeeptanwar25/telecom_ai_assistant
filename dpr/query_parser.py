import json
import os
import re

import truststore

truststore.inject_into_ssl()

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda


# ============================================================
# ENVIRONMENT
# ============================================================

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

MODEL_NAME = "openai/gpt-oss-20b"


# ============================================================
# CIRCLE MAPPING
# ============================================================

CIRCLE_MAPPING = {
    "Delhi": "DEL",
    "DEL": "DEL",

    "Andhra Pradesh": "AP",
    "AP": "AP",

    "Rajasthan": "RAJ",
    "RAJ": "RAJ",

    "Odisha": "ORI",
    "Orissa": "ORI",
    "ORI": "ORI",

    "North East": "NESA",
    "North-East": "NESA",
    "NESA": "NESA",

    "Madhya Pradesh": "MP",
    "MP": "MP",

    "Uttar Pradesh East": "UPE",
    "UPE": "UPE",

    "Haryana": "HR",
    "HR": "HR",
}


# ============================================================
# VALID DATABASE FIELDS
# ============================================================

VALID_FIELDS = {
    "record_key",
    "circle",
    "old_site_id",
    "old_toco",
    "allocation_date",
    "issue_closer_date",
    "final_dismantle_survey_date",
    "sreq_creq_raised_date",
    "dismantle_date",
    "material_pickup_date",
    "material_submission_date",
    "oci_done_date",
    "dismantling_status",
    "ideploy_status",
    "circle_remarks",
    "detailed_remarks",
    "circle_remarks_as_on_31_july",
    "short_remarks_as_on_31_july",
    "submission_pending_remarks",
}


# ============================================================
# VALID OPERATORS
# ============================================================

VALID_OPERATORS = {
    "=",
    "contains",
    ">",
    "<",
    ">=",
    "<=",
    "isnull",
}


# ============================================================
# VALID DATA SOURCES
# ============================================================

VALID_DATA_SOURCES = {
    "postgresql",
    "vector_db",
}


# ============================================================
# VALID OPERATIONS
# ============================================================

VALID_OPERATIONS = {
    "count",
    "retrieve",
    "summarize",
}


# ============================================================
# VALID OUTPUT FORMATS
# ============================================================

VALID_OUTPUT_FORMATS = {
    "text",
    "excel",
    "csv",
}


# ============================================================
# QUERY PROMPT
# ============================================================

query_prompt = PromptTemplate.from_template(
    """
You are the Query Understanding AI for a Telecom DPR system.

Your job is to convert an employee's natural-language question
into a STRICT JSON instruction.

You are NOT executing the query.

You are NOT generating SQL.

You are only deciding:

1. What the employee wants
2. Whether PostgreSQL or Vector DB should be used
3. Which filters are required
4. Which operation is required
5. Which output format is required
6. How many semantic results should be requested from Vector DB


============================================================
DATABASE FIELDS
============================================================

Available fields:

- record_key
- circle
- old_site_id
- old_toco
- allocation_date
- issue_closer_date
- final_dismantle_survey_date
- sreq_creq_raised_date
- dismantle_date
- material_pickup_date
- material_submission_date
- oci_done_date
- dismantling_status
- ideploy_status
- circle_remarks
- detailed_remarks
- circle_remarks_as_on_31_july
- short_remarks_as_on_31_july
- submission_pending_remarks


============================================================
CIRCLE MAPPING
============================================================

Always convert circle names to these codes:

Delhi -> DEL
DEL -> DEL

Andhra Pradesh -> AP
AP -> AP

Rajasthan -> RAJ
RAJ -> RAJ

Odisha -> ORI
Orissa -> ORI
ORI -> ORI

North East -> NESA
North-East -> NESA
NESA -> NESA

Madhya Pradesh -> MP
MP -> MP

Uttar Pradesh East -> UPE
UPE -> UPE

Haryana -> HR
HR -> HR


Examples:

"Delhi" -> "DEL"
"Delhi circle" -> "DEL"
"Rajasthan" -> "RAJ"
"Odisha" -> "ORI"
"North East" -> "NESA"
"Madhya Pradesh" -> "MP"


============================================================
DATA SOURCE RULES
============================================================

Use:

"postgresql"

for structured/exact questions involving:

- count
- site ID
- circle
- status
- dates
- missing values
- exact values
- date ranges
- filtering
- listing records
- reports
- combinations of structured filters


Examples:

"Delhi mein kitni sites hain?"
-> postgresql

"Rajasthan ki pending dismantling sites dikhao"
-> postgresql

"DEL circle mein 1 August 2026 ke baad allocate hui sites"
-> postgresql

"OCI done date missing wali sites"
-> postgresql


Use:

"vector_db"

when the question depends on semantic meaning,
remarks, issues, descriptions, problems, reasons,
or natural-language similarity.


Examples:

"material submission ke related issues wali sites batao"
-> vector_db

"kis site par material submission problem hai?"
-> vector_db

"sites jahan shifting ka issue mention hua hai"
-> vector_db

"material submission se related remarks dikhao"
-> vector_db


IMPORTANT:

If the question asks for an exact structured condition,
use PostgreSQL even if remarks are mentioned.

If the question asks for meaning/similarity around an issue,
use Vector DB.


============================================================
INTENT RULES
============================================================

Use:

"count"

when the employee asks:

- how many
- kitni
- total number
- count


Example:

"Delhi mein kitni sites hain?"


Use:

"search"

for normal record retrieval.


Use:

"report"

when the employee explicitly asks:

- report
- Excel report
- Excel file
- download report
- CSV
- export


Use:

"summary"

when the employee asks for:

- issues
- problems
- related remarks
- reasons
- summary
- semantic understanding


============================================================
OPERATION RULES
============================================================

Use:

"count"

for count questions.

Use:

"retrieve"

for normal list/details/search questions.

Use:

"summarize"

for semantic Vector DB questions where the user
wants related/issue/problem information.


============================================================
OUTPUT FORMAT RULES
============================================================

Default:

"text"


If the employee explicitly asks for:

- Excel
- Excel report
- Excel file

use:

"excel"


If explicitly asks for:

- CSV
- CSV file

use:

"csv"


IMPORTANT:

If user only says:

"show"
"show me"
"dikhao"
"batao"
"list do"
"details dikhao"

do NOT automatically choose Excel.

Use:

"text"


============================================================
FILTER RULES
============================================================

Filters must have this structure:

{{
    "field": "circle",
    "operator": "=",
    "value": "DEL"
}}


For text matching:

{{
    "field": "dismantling_status",
    "operator": "contains",
    "value": "pending"
}}


For exact text:

{{
    "field": "circle",
    "operator": "=",
    "value": "DEL"
}}


For dates:

{{
    "field": "allocation_date",
    "operator": ">",
    "value": "2026-08-01"
}}


For missing/null values:

{{
    "field": "oci_done_date",
    "operator": "isnull",
    "value": true
}}


IMPORTANT:

For "missing", "not available", "blank", "null",
use:

"operator": "isnull"
"value": true


For "available", "present", "not missing",
use:

"operator": "isnull"
"value": false


============================================================
SEMANTIC SEARCH TOP_K RULES
============================================================

The "top_k" field controls how many relevant results
should be retrieved from Vector DB.


1. If user explicitly asks for a number:

"show 10 sites"
-> top_k = 10

"give me 20 sites"
-> top_k = 20

"top 5 relevant sites"
-> top_k = 5


2. If user asks for:

"top relevant sites"
"few relevant sites"
"some relevant sites"

-> top_k = 5


3. If user asks:

"all sites"
"all relevant sites"
"all matching sites"
"saari sites"
"saare sites"
"sabhi sites"

-> top_k = 1000


4. If no number is specified:

-> top_k = 5


IMPORTANT:

top_k is mainly relevant for Vector DB.

For PostgreSQL queries:

top_k = 0


============================================================
FIELDS RULES
============================================================

If the employee asks for specific fields,
return those database field names.


Example:

"site id and circle dikhao"

fields:

[
    "old_site_id",
    "circle"
]


If the employee asks for normal details/list,
use:

[]


============================================================
JSON FORMAT
============================================================

Return ONLY valid JSON.

Do not return markdown.

Do not return ```json.

Use exactly this structure:

{{
    "intent": "search",
    "data_source": "postgresql",
    "filters": [],
    "fields": [],
    "operation": "retrieve",
    "output_format": "text",
    "top_k": 0
}}


============================================================
EMPLOYEE QUESTION
============================================================

{user_query}
"""
)


# ============================================================
# HUGGING FACE CALL
# ============================================================

def call_huggingface_chat(prompt):

    prompt_text = prompt.to_string()

    response = client.chat.completions.create(
        model=MODEL_NAME,
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
# LANGCHAIN QUERY CHAIN
# ============================================================

query_chain = (
    query_prompt
    | RunnableLambda(call_huggingface_chat)
    | StrOutputParser()
)


# ============================================================
# CLEAN JSON RESPONSE
# ============================================================

def clean_json_response(response_text):

    if not response_text:
        raise ValueError(
            "LLM returned an empty response."
        )

    response_text = response_text.strip()

    # Remove ```json
    if response_text.startswith("```json"):
        response_text = response_text[7:]

    # Remove ```
    elif response_text.startswith("```"):
        response_text = response_text[3:]

    # Remove ending ```
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    return response_text.strip()


# ============================================================
# NORMALIZE CIRCLE
# ============================================================

def normalize_circle_value(value):

    if value is None:
        return value

    value = str(value).strip()

    # Direct match
    if value in CIRCLE_MAPPING:
        return CIRCLE_MAPPING[value]

    # Case-insensitive match
    value_lower = value.lower()

    for circle_name, circle_code in CIRCLE_MAPPING.items():

        if circle_name.lower() == value_lower:
            return circle_code

    return value


# ============================================================
# NORMALIZE FILTERS
# ============================================================

def normalize_filters(filters):

    if not isinstance(filters, list):
        return []

    normalized_filters = []

    for item in filters:

        if not isinstance(item, dict):
            continue

        field = item.get("field")

        operator = item.get(
            "operator",
            "="
        )

        value = item.get(
            "value"
        )

        if not field:
            continue

        # --------------------------------------------
        # Validate field
        # --------------------------------------------

        if field not in VALID_FIELDS:
            continue

        # --------------------------------------------
        # Validate operator
        # --------------------------------------------

        if operator not in VALID_OPERATORS:
            operator = "="

        # --------------------------------------------
        # Normalize circle
        # --------------------------------------------

        if field == "circle":

            value = normalize_circle_value(
                value
            )

        # --------------------------------------------
        # Normalize isnull
        # --------------------------------------------

        if operator == "isnull":

            if isinstance(value, str):

                value_lower = value.strip().lower()

                if value_lower in [
                    "true",
                    "yes",
                    "null",
                    "missing",
                    "blank",
                    "none"
                ]:

                    value = True

                elif value_lower in [
                    "false",
                    "no",
                    "not null",
                    "notnull",
                    "available",
                    "present"
                ]:

                    value = False

                else:

                    value = True

            elif value is None:

                value = True

            else:

                value = bool(value)

        normalized_filters.append(
            {
                "field": field,
                "operator": operator,
                "value": value
            }
        )

    return normalized_filters


# ============================================================
# NORMALIZE FIELDS
# ============================================================

def normalize_fields(fields):

    if not isinstance(fields, list):
        return []

    normalized_fields = []

    for field in fields:

        if field in VALID_FIELDS:

            normalized_fields.append(
                field
            )

    return normalized_fields


# ============================================================
# EXTRACT NUMBER FROM USER QUERY
# ============================================================

def extract_requested_number(user_query):

    if not user_query:
        return None

    query = user_query.lower()

    patterns = [

        # top 10
        r"\btop\s+(\d+)\b",

        # 10 sites
        r"\b(\d+)\s+sites?\b",

        # 10 records
        r"\b(\d+)\s+records?\b",

        # 10 results
        r"\b(\d+)\s+results?\b",

        # show 10
        r"\bshow\s+(\d+)\b",

        # give me 10
        r"\bgive\s+me\s+(\d+)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query
        )

        if match:

            try:

                number = int(
                    match.group(1)
                )

                if number > 0:

                    return number

            except ValueError:

                pass

    return None


# ============================================================
# DETERMINE TOP_K
# ============================================================

def determine_top_k(
    user_query,
    data_source,
    llm_top_k
):

    # PostgreSQL doesn't need top_k
    if data_source == "postgresql":

        return 0


    # --------------------------------------------------------
    # Explicit number from user query
    # --------------------------------------------------------

    requested_number = extract_requested_number(
        user_query
    )

    if requested_number is not None:

        return min(
            requested_number,
            1000
        )


    # --------------------------------------------------------
    # Check all / saari / sabhi
    # --------------------------------------------------------

    query_lower = user_query.lower()

    all_keywords = [
        "all sites",
        "all relevant sites",
        "all matching sites",
        "all records",
        "saari sites",
        "saare sites",
        "sabhi sites",
        "sabhi records",
        "saari records",
    ]

    for keyword in all_keywords:

        if keyword in query_lower:

            return 1000


    # --------------------------------------------------------
    # Use LLM top_k
    # --------------------------------------------------------

    try:

        llm_top_k = int(
            llm_top_k
        )

    except (
        TypeError,
        ValueError
    ):

        llm_top_k = 5


    # --------------------------------------------------------
    # Invalid / zero / negative
    # --------------------------------------------------------

    if llm_top_k <= 0:

        llm_top_k = 5


    # --------------------------------------------------------
    # Maximum safety limit
    # --------------------------------------------------------

    return min(
        llm_top_k,
        1000
    )


# ============================================================
# NORMALIZE COMPLETE QUERY
# ============================================================

def normalize_parsed_query(
    parsed_query,
    user_query
):

    if not isinstance(
        parsed_query,
        dict
    ):

        raise ValueError(
            "LLM response is not a JSON object."
        )


    # ========================================================
    # INTENT
    # ========================================================

    intent = parsed_query.get(
        "intent",
        "search"
    )

    allowed_intents = {
        "search",
        "count",
        "report",
        "summary"
    }

    if intent not in allowed_intents:

        intent = "search"


    # ========================================================
    # DATA SOURCE
    # ========================================================

    data_source = parsed_query.get(
        "data_source",
        "postgresql"
    )

    if data_source not in VALID_DATA_SOURCES:

        data_source = "postgresql"


    # ========================================================
    # FILTERS
    # ========================================================

    filters = normalize_filters(
        parsed_query.get(
            "filters",
            []
        )
    )


    # ========================================================
    # FIELDS
    # ========================================================

    fields = normalize_fields(
        parsed_query.get(
            "fields",
            []
        )
    )


    # ========================================================
    # OPERATION
    # ========================================================

    operation = parsed_query.get(
        "operation",
        "retrieve"
    )

    if operation not in VALID_OPERATIONS:

        if intent == "count":

            operation = "count"

        elif intent == "summary":

            operation = "summarize"

        else:

            operation = "retrieve"


    # ========================================================
    # OUTPUT FORMAT
    # ========================================================

    output_format = parsed_query.get(
        "output_format",
        "text"
    )

    if output_format not in VALID_OUTPUT_FORMATS:

        output_format = "text"


    # ========================================================
    # TOP_K
    # ========================================================

    llm_top_k = parsed_query.get(
        "top_k",
        5
    )

    top_k = determine_top_k(
        user_query=user_query,
        data_source=data_source,
        llm_top_k=llm_top_k
    )


    # ========================================================
    # FINAL QUERY
    # ========================================================

    final_query = {
        "intent": intent,
        "data_source": data_source,
        "filters": filters,
        "fields": fields,
        "operation": operation,
        "output_format": output_format,
        "top_k": top_k
    }

    return final_query


# ============================================================
# MAIN PARSER FUNCTION
# ============================================================

def parse_user_query(user_query):

    if not user_query:

        raise ValueError(
            "User query cannot be empty."
        )


    user_query = user_query.strip()


    if not user_query:

        raise ValueError(
            "User query cannot be empty."
        )


    # ========================================================
    # LANGCHAIN CHAIN
    # ========================================================

    raw_response = query_chain.invoke(
        {
            "user_query": user_query
        }
    )


    # ========================================================
    # CLEAN RESPONSE
    # ========================================================

    cleaned_response = clean_json_response(
        raw_response
    )


    # ========================================================
    # PARSE JSON
    # ========================================================

    try:

        parsed_query = json.loads(
            cleaned_response
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "LLM returned invalid JSON.\n"
            f"LLM response:\n{cleaned_response}"
        ) from error


    # ========================================================
    # NORMALIZE + VALIDATE
    # ========================================================

    final_query = normalize_parsed_query(
        parsed_query,
        user_query
    )


    return final_query


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("TELECOM DPR QUERY PARSER")
    print("=" * 70)

    while True:

        user_query = input(
            "\nEnter your question "
            "(type exit to quit): "
        ).strip()


        if user_query.lower() == "exit":

            break


        if not user_query:

            continue


        try:

            result = parse_user_query(
                user_query
            )

            print(
                "\nParsed Query:"
            )

            print(
                json.dumps(
                    result,
                    indent=4,
                    default=str
                )
            )


        except Exception as error:

            print(
                f"\nError: {error}"
            )