import os
import sys
import json
import traceback
import io

import django
import pandas as pd
import streamlit as st


# ============================================================
# DJANGO SETUP (Must be FIRST, before any integration imports)
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django.setup()


# ============================================================
# INTEGRATION IMPORTS (After Django setup)
# ============================================================

from integration.query_parser import (
    parse_user_query,
    execute_parsed_query,
    _call_llm,
)

from integration.query_validator import (
    QueryValidationError,
)

from integration.query_engine import (
    execute_integration_query,
)

from integration.answer_generator import (
    generate_answer,
)


# ============================================================
# ✅ MODEL WARMUP - Load on startup
# ============================================================

@st.cache_resource
def load_llm_model():
    """
    ✅ Load HuggingFace LLM model at Streamlit startup
    
    Uses @st.cache_resource so it loads ONLY ONCE
    across all reruns
    
    Returns:
        True if model loaded successfully
        False if there was an error
    """
    
    try:
        print("🔄 Loading HuggingFace LLM model...")
        
        # Warmup query to initialize the model
        result = _call_llm("test")
        
        print("✅ Model loaded successfully!")
        return True
        
    except Exception as e:
        print(f"⚠️ Model loading error: {e}")
        return False


# ============================================================
# PAGE CONFIG (Call ONLY ONCE)
# ============================================================

st.set_page_config(
    page_title="📡 Telecom AI Assistant",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ✅ LOAD MODEL ON STARTUP
# ============================================================

if "model_loaded" not in st.session_state:
    with st.spinner("🔄 Loading HuggingFace LLM model... (This happens only once)"):
        st.session_state.model_loaded = load_llm_model()

if st.session_state.model_loaded:
    st.success("✅ Model loaded successfully!", icon="✅")
else:
    st.warning("⚠️ Model loading took longer than expected. First query might be slow.")


# ============================================================
# TITLE & CAPTION
# ============================================================

st.title("📡 Telecom AI Assistant")

st.caption(
    "Ask questions about the Integration Tracker "
    "using natural language."
)


# ============================================================
# SESSION STATE
# ============================================================

if "integration_history" not in st.session_state:
    st.session_state.integration_history = []


# ============================================================
# HELPER: RUN INTEGRATION QUERY
# ============================================================

def run_integration_query(
    user_question: str,
):
    """
    Complete Integration Tracker pipeline:

        User Question
              ↓
        LLM Query Parser
              ↓
        Validator (optional)
              ↓
        Query Engine (PostgreSQL)
              ↓
        Exact Result

    Parameters:
        user_question (str): Natural language question from user

    Returns:
        tuple: (query_plan, result)
            query_plan (dict): The parsed and validated query plan
            result (dict): Database query result with records and count
    """

    # --------------------------------------------------------
    # STEP 1: Natural language → query plan
    # --------------------------------------------------------

    query_plan = parse_user_query(
        user_question
    )

    # --------------------------------------------------------
    # STEP 2: Extract all parameters from query plan
    # --------------------------------------------------------

    filters = query_plan.get(
        "filters",
        [],
    )

    operation = query_plan.get(
        "operation",
        "retrieve",
    )

    limit = query_plan.get(
        "limit",
        500,
    )

    offset = query_plan.get(
        "offset",
        0,
    )

    fields = query_plan.get(
        "fields",
        [],
    )

    group_by = query_plan.get(
        "group_by",
        [],
    )

    aggregation = query_plan.get(
        "aggregation",
        None,
    )

    aggregation_field = query_plan.get(
        "aggregation_field",
        None,
    )

    sort = query_plan.get(
        "sort",
        [],
    )

    distinct = query_plan.get(
        "distinct",
        False,
    )

    temporal_group = query_plan.get(
        "temporal_group",
        None,
    )

    # --------------------------------------------------------
    # STEP 3: Validate and normalize limit
    # --------------------------------------------------------

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 500

    if limit < 1:
        limit = 1

    if limit > 5000:
        limit = 5000

    # --------------------------------------------------------
    # STEP 4: Validate and normalize offset
    # --------------------------------------------------------

    try:
        offset = int(offset)
    except (TypeError, ValueError):
        offset = 0

    if offset < 0:
        offset = 0

    # --------------------------------------------------------
    # STEP 5: PostgreSQL execution
    # ✅ execute_parsed_query handles all parameters
    # --------------------------------------------------------

    result = execute_parsed_query(
        query_plan
    )

    return query_plan, result


# ============================================================
# HELPER: DISPLAY QUERY PLAN
# ============================================================

def display_query_plan(
    query_plan,
):
    """
    Show the dynamic query plan generated by the AI LLM.
    
    The query plan includes:
    - Filters (field, operator, value)
    - Operation (retrieve, count, aggregate)
    - Fields to return
    - Grouping and aggregation
    - Sorting preferences
    - Limit and offset for pagination
    - Distinct flag
    - Temporal grouping (month-wise, year-wise, etc.)
    
    Parameters:
        query_plan (dict): The parsed query plan from LLM
    """

    with st.expander(
        "🔍 Query Plan",
        expanded=False,
    ):

        st.json(
            query_plan
        )


# ============================================================
# HELPER: DISPLAY RESULT
# ============================================================

def display_result(
    result,
    query_plan,
):
    """
    Display exact PostgreSQL result in appropriate format.
    
    Three output formats:
    1. Count operation → show single metric
    2. Aggregate operation → show table (grouped) or metric (single)
    3. Retrieve operation → show full DataFrame
    
    Parameters:
        result (dict): Database query result with 'records' and 'count'
        query_plan (dict): Query plan to determine operation type
    """

    records = result.get(
        "records",
        [],
    )

    count = result.get(
        "count",
        0,
    )

    operation = query_plan.get(
        "operation",
        "retrieve",
    )

    # ========================================================
    # COUNT OPERATION
    # ========================================================

    if operation == "count":

        st.metric(
            label="Total Matching Records",
            value=count,
        )

        return

    # ========================================================
    # AGGREGATE OPERATION
    # ========================================================

    if operation == "aggregate":

        # --------------------------------------------------------
        # Grouped aggregation (multiple rows)
        # --------------------------------------------------------

        if len(records) > 1:
            
            df = pd.DataFrame(
                records
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                f"Showing {len(records)} group(s)"
            )

            return

        # --------------------------------------------------------
        # Single aggregation result (no grouping)
        # --------------------------------------------------------

        if records:

            result_value = records[0].get(
                "result",
                0,
            )

            st.metric(
                label="Aggregation Result",
                value=result_value,
            )

        else:

            st.info(
                "No aggregation result found."
            )

        return

    # ========================================================
    # NO RECORDS FOUND
    # ========================================================

    if not records:

        st.info(
            "No matching records found."
        )

        return

    # ========================================================
    # RETRIEVE OPERATION (DataFrame)
    # ========================================================

    df = pd.DataFrame(
        records
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Show record count
    # --------------------------------------------------------

    st.caption(
        f"Showing {len(records)} result(s). "
        f"Total matching records: {count}"
    )


# ============================================================
# HELPER: CREATE RESULT DATAFRAME
# ============================================================

def create_result_dataframe(
    result,
):
    """
    Convert database result into pandas DataFrame.
    
    Parameters:
        result (dict): Database query result with 'records' list
    
    Returns:
        DataFrame or None if no records
    """

    records = result.get(
        "records",
        [],
    )

    if not records:
        return None

    df = pd.DataFrame(
        records
    )

    return df


# ============================================================
# HELPER: ADD DOWNLOAD BUTTONS
# ============================================================

def add_download_buttons(
    result,
):
    """
    Add CSV and Excel download buttons for query results.
    
    Users can download results in:
    - CSV (comma-separated values)
    - Excel (XLSX format with OpenPyXL)
    
    Parameters:
        result (dict): Database query result
    """

    df = create_result_dataframe(
        result
    )

    if df is None or df.empty:
        return

    # ========================================================
    # Create two columns for download buttons
    # ========================================================

    col1, col2 = st.columns(2)

    # ========================================================
    # CSV DOWNLOAD BUTTON
    # ========================================================

    with col1:

        csv_data = df.to_csv(
            index=False
        ).encode(
            "utf-8"
        )

        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name="integration_result.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ========================================================
    # EXCEL DOWNLOAD BUTTON
    # ========================================================

    with col2:

        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl",
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Integration",
            )

        excel_data = (
            excel_buffer.getvalue()
        )

        st.download_button(
            label="⬇️ Download Excel",
            data=excel_data,
            file_name="integration_result.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )


# ============================================================
# MAIN UI - HEADER
# ============================================================

st.header(
    "🤖 Integration Tracker AI"
)

st.write(
    "Ask your question in English or Hinglish."
)

# ============================================================
# MAIN UI - EXAMPLES
# ============================================================

st.write(
    "Examples:"
)

st.markdown(
    """
- `AP me kitne records hain?`
- `RET ka total count batao`
- `circle wise integration count batao`
- `circle aur activity wise count batao`
- `LNBTS 911968 ki complete details do`
- `AP ke 12 September 2025 se 15 September 2025 ke records`
- `Nokia ke MAH records dikhao`
- `Highest cell count`
- `Month-wise integration count`
"""
)


# ============================================================
# MAIN UI - QUESTION INPUT
# ============================================================

user_question = st.text_area(
    label="Ask your question",
    placeholder=(
        "Example: AP ke 12 September 2025 se 15 September 2025 ke records"
    ),
    height=100,
)


# ============================================================
# MAIN UI - SEARCH BUTTON
# ============================================================

search_clicked = st.button(
    label="🔎 Ask AI",
    type="primary",
    use_container_width=True,
)


# ============================================================
# MAIN UI - PROCESS QUESTION
# ============================================================

if search_clicked:

    # ============================================================
    # Check if question is empty
    # ============================================================

    if not user_question.strip():

        st.warning(
            "Please enter a question."
        )

    # ============================================================
    # Question is not empty - Process it
    # ============================================================

    else:

        try:

            # ==================================================
            # STEP 1: Parse & Execute query
            # ==================================================

            with st.spinner(
                "Understanding your question..."
            ):

                query_plan, result = (
                    run_integration_query(
                        user_question.strip()
                    )
                )

            # ==================================================
            # STEP 2: Show Query Plan (expandable)
            # ==================================================

            display_query_plan(
                query_plan
            )

            # ==================================================
            # STEP 3: Generate human-readable answer
            # ==================================================

            with st.spinner(
                "Preparing answer..."
            ):

                employee_answer = (
                    generate_answer(
                        user_question.strip(),
                        query_plan,
                        result,
                    )
                )

            # ==================================================
            # STEP 4: Show the answer
            # ==================================================

            st.subheader(
                "💬 Answer"
            )

            st.success(
                employee_answer
            )

            # ==================================================
            # STEP 5: Show database result
            # ==================================================

            st.subheader(
                "📊 Database Result"
            )

            display_result(
                result,
                query_plan,
            )

            # ==================================================
            # STEP 6: Add download buttons
            # ==================================================

            add_download_buttons(
                result
            )

            # ==================================================
            # STEP 7: Add to query history
            # ==================================================

            st.session_state.integration_history.append(
                {
                    "question": user_question.strip(),
                    "query_plan": query_plan,
                    "result": result,
                    "answer": employee_answer,
                }
            )

        # ======================================================
        # ERROR HANDLING: QueryValidationError
        # ======================================================

        except QueryValidationError as exc:

            st.error(
                f"Query validation error: {exc}"
            )

        # ======================================================
        # ERROR HANDLING: All other exceptions
        # ======================================================

        except Exception as exc:

            st.error(
                f"Something went wrong: {exc}"
            )

            with st.expander(
                "🔧 Technical details"
            ):

                st.code(
                    traceback.format_exc()
                )


# ============================================================
# QUERY HISTORY
# ============================================================

if st.session_state.integration_history:

    st.divider()

    st.subheader(
        "🕘 Recent Questions"
    )

    # ========================================================
    # Display last 10 questions in reverse order
    # ========================================================

    for index, item in enumerate(
        reversed(
            st.session_state.integration_history[-10:]
        ),
        start=1,
    ):

        with st.expander(
            f"{index}. {item['question']}"
        ):

            # ================================================
            # Show answer
            # ================================================

            st.write(
                "**Answer:**"
            )

            st.write(
                item["answer"]
            )

            # ================================================
            # Show query plan
            # ================================================

            st.write(
                "**Query Plan:**"
            )

            st.json(
                item["query_plan"]
            )