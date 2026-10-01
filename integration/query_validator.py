
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# DATABASE FIELDS
# ============================================================

DATA_FIELDS = [
    "unique_key",
    "oem",
    "integration_date",
    "circle",
    "activity_name",
    "site_id",
    "mo_name",
    "lnbts_id",
    "new_nrbts_id",
    "technology_siwa",
    "configuration_5g",
    "oss_details",
    "cell_id",
    "cell_count",
    "bsc_name",
    "bcf",
    "trx_count",
    "pre_alarm",
    "gps_ip_clk",
    "ret",
    "post_vswr",
    "post_alarms",
    "activity_mode_sa_nsa",
    "activity_type_siwa",
    "band_siwa",
    "cell_status",
    "ctr_status",
    "integration_remark",
    "t2t4r",
    "bbu_type",
    "bb_card",
    "rru_type",
    "media_status",
    "mplane_ip",
    "scf_prepared_by",
    "site_integrate_by",
    "site_status",
    "external_alarm_confirmation",
    "soft_at_status",
    "licence_status",
    "esn_no",
    "responsibility_for_alarm_clearance",
    "tac",
    "pci_tdd_20",
    "pci_tdd_10_20",
    "pci_fdd_2100",
    "pci_fdd_1800",
    "pci_l900",
    "pci_5g",
    "rsi_tdd_20",
    "rsi_tdd_10_20",
    "rsi_fdd_2100",
    "rsi_fdd_1800",
    "rsi_l900",
    "rsi_5g",
    "gpl",
    "pre_post_check",
    "crq",
    "customer_approval",
    "old_site_id",
    "old_site_lnbts",
    "old_nrbts_id",
    "old_site_oss",
    "old_site_mplane_ip",
    "old_site_tech",
    "allocated_tech",
    "deployed_tech",
    "no_of_bbu",
    "mids_id",
    "uploaded_by",
    "upload_date",
]


# ============================================================
# SPECIAL FIELD TYPES
# ============================================================

DATE_FIELDS = {
    "integration_date",
    "upload_date",
}


NUMERIC_FIELDS = {
    "cell_count",
    "trx_count",
    "no_of_bbu",
}


# ============================================================
# OPERATORS
# ============================================================

ALLOWED_OPERATORS = {
    "exact",
    "iexact",
    "contains",
    "icontains",
    "startswith",
    "istartswith",
    "gt",
    "gte",
    "lt",
    "lte",
    "isnull",
}


# ============================================================
# OPERATIONS
# ============================================================

ALLOWED_OPERATIONS = {
    "retrieve",
    "count",
    "aggregate",
}


# ============================================================
# AGGREGATIONS
# ============================================================

ALLOWED_AGGREGATIONS = {
    "count",
    "count_distinct",
    "sum",
    "avg",
    "min",
    "max",
}


# ============================================================
# OUTPUT FORMATS
# ============================================================

ALLOWED_OUTPUT_FORMATS = {
    "text",
    "table",
    "excel",
    "csv",
}


# ============================================================
# INTENTS
# ============================================================

ALLOWED_INTENTS = {
    "search",
}


# ============================================================
# SORT DIRECTIONS
# ============================================================

ALLOWED_SORT_DIRECTIONS = {
    "asc",
    "desc",
}


# ============================================================
# ERROR CLASS
# ============================================================

class QueryValidationError(ValueError):
    """
    Raised when the LLM generated an invalid query plan.
    """
    pass


# ============================================================
# BASIC HELPERS
# ============================================================

def _is_empty(value: Any) -> bool:
    """
    Check whether a value should be treated as empty.
    """

    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    return False


def _normalize_string(value: Any) -> Any:
    """
    Safely strip strings.

    Does not modify non-string values.
    """

    if isinstance(value, str):
        return value.strip()

    return value


def _normalize_field_name(field: Any) -> str:
    """
    Convert field name to normalized form.
    """

    if field is None:
        return ""

    return str(field).strip().lower()


# ============================================================
# DATE HELPERS
# ============================================================

def _is_valid_date(value: Any) -> bool:
    """
    Check YYYY-MM-DD date.
    """

    if not isinstance(value, str):
        return False

    value = value.strip()

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True

    except ValueError:
        return False


def _is_valid_datetime(value: Any) -> bool:
    """
    Check common datetime formats.
    """

    if not isinstance(value, str):
        return False

    value = value.strip()

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]

    for fmt in formats:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue

    return False


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_exact_date(question: str) -> Optional[str]:
    """
    Extract an exact date from natural-language question.

    Supported examples:

        2025-09-12
        12-09-2025
        12 September 2025
        12 Sep 2025

    Returns:

        YYYY-MM-DD

    or None.
    """

    if not question:
        return None

    text = str(question).strip()

    # --------------------------------------------------------
    # YYYY-MM-DD
    # --------------------------------------------------------

    match = re.search(
        r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b",
        text,
    )

    if match:
        year, month, day = map(int, match.groups())

        try:
            date_obj = datetime(year, month, day)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None

    # --------------------------------------------------------
    # DD-MM-YYYY
    # --------------------------------------------------------

    match = re.search(
        r"\b(\d{1,2})-(\d{1,2})-(20\d{2})\b",
        text,
    )

    if match:
        day, month, year = map(int, match.groups())

        try:
            date_obj = datetime(year, month, day)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None

    # --------------------------------------------------------
    # DD/MM/YYYY
    # --------------------------------------------------------

    match = re.search(
        r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b",
        text,
    )

    if match:
        day, month, year = map(int, match.groups())

        try:
            date_obj = datetime(year, month, day)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None

    # --------------------------------------------------------
    # Month names
    # --------------------------------------------------------

    month_pattern = (
        r"\b"
        r"(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
        r"\s+"
        r"(20\d{2})"
        r"\b"
    )

    match = re.search(
        month_pattern,
        text,
        flags=re.IGNORECASE,
    )

    if match:
        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))

        month_formats = [
            "%d %B %Y",
            "%d %b %Y",
        ]

        for fmt in month_formats:
            try:
                date_obj = datetime.strptime(
                    f"{day} {month_name} {year}",
                    fmt,
                )

                return date_obj.strftime("%Y-%m-%d")

            except ValueError:
                continue

    return None


# ============================================================
# DATE FIELD VALIDATION
# ============================================================

def _validate_date_filter(
    field: str,
    operator: str,
    value: Any,
) -> None:

    if field not in DATE_FIELDS:
        return

    if operator == "isnull":
        return

    if not isinstance(value, str):
        raise QueryValidationError(
            f"Date filter for '{field}' must contain a string value."
        )

    if not _is_valid_datetime(value):
        raise QueryValidationError(
            f"Invalid date value '{value}' for field '{field}'. "
            f"Expected YYYY-MM-DD or a valid datetime."
        )


# ============================================================
# NUMERIC FIELD VALIDATION
# ============================================================

def _validate_numeric_filter(
    field: str,
    operator: str,
    value: Any,
) -> None:

    if field not in NUMERIC_FIELDS:
        return

    if operator == "isnull":
        return

    try:
        float(value)
    except (TypeError, ValueError):
        raise QueryValidationError(
            f"Field '{field}' requires a numeric value. "
            f"Received: {value!r}"
        )


# ============================================================
# FILTER VALIDATION
# ============================================================

def _validate_filter(
    filter_item: Any,
    allowed_fields: set,
) -> Dict[str, Any]:

    if not isinstance(filter_item, dict):
        raise QueryValidationError(
            "Each filter must be an object."
        )

    field = _normalize_field_name(
        filter_item.get("field")
    )

    operator = str(
        filter_item.get("operator", "iexact")
    ).strip().lower()

    value = filter_item.get("value")

    # --------------------------------------------------------
    # Field
    # --------------------------------------------------------

    if not field:
        raise QueryValidationError(
            "Filter field cannot be empty."
        )

    if field not in allowed_fields:
        raise QueryValidationError(
            f"Unknown filter field: '{field}'"
        )

    # --------------------------------------------------------
    # Operator
    # --------------------------------------------------------

    if operator not in ALLOWED_OPERATORS:
        raise QueryValidationError(
            f"Unsupported filter operator: '{operator}'"
        )

    # --------------------------------------------------------
    # Value
    # --------------------------------------------------------

    if operator == "isnull":

        if isinstance(value, str):

            normalized = value.strip().lower()

            if normalized in {"true", "1", "yes"}:
                value = True

            elif normalized in {"false", "0", "no"}:
                value = False

            else:
                raise QueryValidationError(
                    f"isnull requires true/false, got '{value}'."
                )

        elif not isinstance(value, bool):
            raise QueryValidationError(
                "isnull requires a boolean value."
            )

    else:

        if _is_empty(value):
            raise QueryValidationError(
                f"Filter value for '{field}' cannot be empty."
            )

        value = _normalize_string(value)

    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    _validate_date_filter(
        field=field,
        operator=operator,
        value=value,
    )

    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    _validate_numeric_filter(
        field=field,
        operator=operator,
        value=value,
    )

    return {
        "field": field,
        "operator": operator,
        "value": value,
    }


# ============================================================
# SORT VALIDATION
# ============================================================

def _validate_sort(
    sort_value: Any,
    allowed_fields: set,
) -> List[Any]:

    if sort_value is None:
        return []

    if not isinstance(sort_value, list):
        sort_value = [sort_value]

    validated = []

    for item in sort_value:

        # ----------------------------------------------------
        # String format:
        #
        # "circle"
        # "-integration_date"
        # ----------------------------------------------------

        if isinstance(item, str):

            item = item.strip()

            if not item:
                continue

            direction = "asc"

            if item.startswith("-"):
                direction = "desc"
                field = item[1:].strip()
            else:
                field = item

            field = _normalize_field_name(field)

            if field not in allowed_fields:
                raise QueryValidationError(
                    f"Unknown sort field: '{field}'"
                )

            validated.append(
                {
                    "field": field,
                    "direction": direction,
                }
            )

            continue

        # ----------------------------------------------------
        # Dict format
        # ----------------------------------------------------

        if isinstance(item, dict):

            field = _normalize_field_name(
                item.get("field")
            )

            direction = str(
                item.get("direction", "asc")
            ).strip().lower()

            if field not in allowed_fields:
                raise QueryValidationError(
                    f"Unknown sort field: '{field}'"
                )

            if direction not in ALLOWED_SORT_DIRECTIONS:
                raise QueryValidationError(
                    f"Invalid sort direction: '{direction}'"
                )

            validated.append(
                {
                    "field": field,
                    "direction": direction,
                }
            )

            continue

        raise QueryValidationError(
            "Each sort item must be a string or object."
        )

    return validated


# ============================================================
# AGGREGATION VALIDATION
# ============================================================

def _validate_aggregation(
    operation: str,
    aggregation: Any,
    aggregation_field: Any,
    group_by: List[str],
    allowed_fields: set,
) -> Dict[str, Any]:

    aggregation = (
        str(aggregation).strip().lower()
        if aggregation is not None
        else None
    )

    if aggregation is not None:
        if aggregation not in ALLOWED_AGGREGATIONS:
            raise QueryValidationError(
                f"Unsupported aggregation: '{aggregation}'"
            )

    # --------------------------------------------------------
    # Aggregate operation requires aggregation
    # --------------------------------------------------------

    if operation == "aggregate" and aggregation is None:
        raise QueryValidationError(
            "Aggregate operation requires an aggregation."
        )

    # --------------------------------------------------------
    # Group by validation
    # --------------------------------------------------------

    validated_group_by = []

    for field in group_by:

        field = _normalize_field_name(field)

        if field not in allowed_fields:
            raise QueryValidationError(
                f"Unknown group_by field: '{field}'"
            )

        if field not in validated_group_by:
            validated_group_by.append(field)

    # --------------------------------------------------------
    # Aggregation field
    # --------------------------------------------------------

    if aggregation_field is not None:

        aggregation_field = _normalize_field_name(
            aggregation_field
        )

        if aggregation_field not in allowed_fields:
            raise QueryValidationError(
                f"Unknown aggregation field: "
                f"'{aggregation_field}'"
            )

    # --------------------------------------------------------
    # Numeric aggregations
    # --------------------------------------------------------

    if aggregation in {
        "sum",
        "avg",
        "min",
        "max",
    }:

        if not aggregation_field:
            raise QueryValidationError(
                f"Aggregation '{aggregation}' requires "
                f"aggregation_field."
            )

        if aggregation_field not in NUMERIC_FIELDS:
            raise QueryValidationError(
                f"Aggregation '{aggregation}' can only be "
                f"used on numeric fields."
            )

    # --------------------------------------------------------
    # Count distinct
    # --------------------------------------------------------

    if aggregation == "count_distinct":

        if not aggregation_field:
            raise QueryValidationError(
                "count_distinct requires aggregation_field."
            )

    return {
        "aggregation": aggregation,
        "aggregation_field": aggregation_field,
        "group_by": validated_group_by,
    }


# ============================================================
# MAIN QUERY PLAN VALIDATOR
# ============================================================

def validate_query_plan(
    query_plan: Dict[str, Any],
    allowed_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate and normalize an LLM-generated query plan.

    This function does NOT know actual database values.

    Example:
        RET
        AP
        NOKIA

    are NOT hard-coded here.

    Only field names, operators and query structure
    are validated.
    """

    if not isinstance(query_plan, dict):
        raise QueryValidationError(
            "Query plan must be a dictionary/object."
        )

    if allowed_fields is None:
        allowed_fields = DATA_FIELDS

    allowed_fields = {
        _normalize_field_name(field)
        for field in allowed_fields
    }

    plan = dict(query_plan)

    # ========================================================
    # DEFAULTS
    # ========================================================

    plan.setdefault("intent", "search")
    plan.setdefault("filters", [])
    plan.setdefault("operation", "retrieve")
    plan.setdefault("fields", [])
    plan.setdefault("group_by", [])
    plan.setdefault("aggregation", None)
    plan.setdefault("aggregation_field", None)
    plan.setdefault("sort", [])
    plan.setdefault("limit", 500)
    plan.setdefault("output_format", "text")

    # ========================================================
    # INTENT
    # ========================================================

    intent = str(
        plan["intent"]
    ).strip().lower()

    # Some LLMs may incorrectly use:
    #
    # "intent": "count"
    #
    # Correct it structurally.
    if intent == "count":
        intent = "search"
        plan["operation"] = "count"

    if intent not in ALLOWED_INTENTS:
        raise QueryValidationError(
            f"Unsupported intent: '{intent}'"
        )

    plan["intent"] = intent

    # ========================================================
    # OPERATION
    # ========================================================

    operation = str(
        plan["operation"]
    ).strip().lower()

    if operation not in ALLOWED_OPERATIONS:
        raise QueryValidationError(
            f"Unsupported operation: '{operation}'"
        )

    plan["operation"] = operation

    # ========================================================
    # FIELDS
    # ========================================================

    fields = plan.get("fields")

    if fields is None:
        fields = []

    if not isinstance(fields, list):
        fields = [fields]

    validated_fields = []

    for field in fields:

        field = _normalize_field_name(field)

        if not field:
            continue

        if field not in allowed_fields:
            raise QueryValidationError(
                f"Unknown field: '{field}'"
            )

        if field not in validated_fields:
            validated_fields.append(field)

    plan["fields"] = validated_fields

    # ========================================================
    # FILTERS
    # ========================================================

    filters = plan.get("filters")

    if filters is None:
        filters = []

    if not isinstance(filters, list):
        filters = [filters]

    validated_filters = []

    for filter_item in filters:

        validated_filters.append(
            _validate_filter(
                filter_item=filter_item,
                allowed_fields=allowed_fields,
            )
        )

    plan["filters"] = validated_filters

    # ========================================================
    # GROUP BY
    # ========================================================

    group_by = plan.get("group_by")

    if group_by is None:
        group_by = []

    if not isinstance(group_by, list):
        group_by = [group_by]

    validated_group_by = []

    for field in group_by:

        field = _normalize_field_name(field)

        if not field:
            continue

        if field not in allowed_fields:
            raise QueryValidationError(
                f"Unknown group_by field: '{field}'"
            )

        if field not in validated_group_by:
            validated_group_by.append(field)

    plan["group_by"] = validated_group_by

    # ========================================================
    # AGGREGATION
    # ========================================================

    aggregation_info = _validate_aggregation(
        operation=operation,
        aggregation=plan.get("aggregation"),
        aggregation_field=plan.get("aggregation_field"),
        group_by=plan["group_by"],
        allowed_fields=allowed_fields,
    )

    plan["aggregation"] = aggregation_info["aggregation"]

    plan["aggregation_field"] = (
        aggregation_info["aggregation_field"]
    )

    # ========================================================
    # COUNT OPERATION
    # ========================================================

    if operation == "count":

        # A simple count does not need aggregation.
        #
        # If LLM unnecessarily supplied aggregation=count,
        # we can normalize it.
        if plan["aggregation"] == "count":
            plan["aggregation"] = None

        plan["aggregation_field"] = None

        # Count does not need selected fields.
        plan["fields"] = []

    # ========================================================
    # RETRIEVE OPERATION
    # ========================================================

    if operation == "retrieve":

        # Retrieve normally does not need aggregation.
        if plan["aggregation"] is not None:
            raise QueryValidationError(
                "Retrieve operation cannot contain aggregation."
            )

        if plan["aggregation_field"] is not None:
            raise QueryValidationError(
                "Retrieve operation cannot contain "
                "aggregation_field."
            )

        if plan["group_by"]:
            raise QueryValidationError(
                "Retrieve operation cannot contain group_by."
            )

    # ========================================================
    # AGGREGATE OPERATION
    # ========================================================

    if operation == "aggregate":

        if plan["aggregation"] is None:
            raise QueryValidationError(
                "Aggregate operation requires aggregation."
            )

    # ========================================================
    # SORT
    # ========================================================

    plan["sort"] = _validate_sort(
        sort_value=plan.get("sort"),
        allowed_fields=allowed_fields,
    )

    # ========================================================
    # LIMIT
    # ========================================================

    try:
        limit = int(plan.get("limit", 500))
    except (TypeError, ValueError):
        raise QueryValidationError(
            "limit must be an integer."
        )

    if limit < 1:
        raise QueryValidationError(
            "limit must be at least 1."
        )

    # Prevent accidental huge result retrieval.
    if limit > 5000:
        limit = 5000

    plan["limit"] = limit

    # ========================================================
    # OUTPUT FORMAT
    # ========================================================

    output_format = str(
        plan.get("output_format", "text")
    ).strip().lower()

    if output_format not in ALLOWED_OUTPUT_FORMATS:
        raise QueryValidationError(
            f"Unsupported output format: "
            f"'{output_format}'"
        )

    plan["output_format"] = output_format

    # ========================================================
    # FINAL NORMALIZATION
    # ========================================================

    return plan


# ============================================================
# QUESTION-AWARE VALIDATION (✅ FIXED FOR DATE RANGES)
# ============================================================

def validate_against_question(
    query_plan: Dict[str, Any],
    question: str,
    allowed_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate query plan and perform safe structural repairs.

    ✅ FIXED: Handles date ranges (gte/lte) correctly
    
    Does NOT contain question-specific rules.
    Only checks whether the LLM's interpretation is
    structurally reasonable.

    Actual database values are never hard-coded.
    """

    if not question or not str(question).strip():
        raise QueryValidationError(
            "Question cannot be empty."
        )

    question = str(question).strip()

    plan = dict(query_plan)

    # ========================================================
    # DEFAULT MISSING VALUES
    # ========================================================

    plan.setdefault("intent", "search")
    plan.setdefault("filters", [])
    plan.setdefault("operation", "retrieve")
    plan.setdefault("fields", [])
    plan.setdefault("group_by", [])
    plan.setdefault("aggregation", None)
    plan.setdefault("aggregation_field", None)
    plan.setdefault("sort", [])
    plan.setdefault("limit", 500)
    plan.setdefault("output_format", "text")

    # ========================================================
    # INTENT NORMALIZATION
    # ========================================================

    intent = str(
        plan.get("intent", "search")
    ).strip().lower()

    if intent == "count":
        plan["intent"] = "search"
        plan["operation"] = "count"

    # ========================================================
    # OPERATION NORMALIZATION
    # ========================================================

    operation = str(
        plan.get("operation", "retrieve")
    ).strip().lower()

    # Natural language count indicators.
    #
    # This is NOT a question-specific answer.
    # It is generic intent detection used only to repair
    # an obviously inconsistent LLM plan.
    count_patterns = [
        r"\bhow many\b",
        r"\bnumber of\b",
        r"\btotal\b",
        r"\bcount\b",
        r"\bkitne\b",
        r"\bkitna\b",
        r"\bkitni\b",
        r"\bkul\b",
    ]

    asks_count = any(
        re.search(
            pattern,
            question,
            flags=re.IGNORECASE,
        )
        for pattern in count_patterns
    )

    if asks_count and operation == "retrieve":

        # If the LLM clearly missed an explicit count request,
        # repair the operation.
        plan["operation"] = "count"

    # ========================================================
    # GROUPED COUNT REPAIR
    # ========================================================

    grouping_patterns = [
        r"\bwise\b",
        r"\bcircle wise\b",
        r"\bactivity wise\b",
        r"\bgroup by\b",
        r"\bgrouped by\b",
        r"\bcircle[- ]wise\b",
        r"\bactivity[- ]wise\b",
    ]

    asks_grouping = any(
        re.search(
            pattern,
            question,
            flags=re.IGNORECASE,
        )
        for pattern in grouping_patterns
    )

    if asks_grouping:

        if plan.get("group_by"):
            plan["operation"] = "aggregate"

            if not plan.get("aggregation"):
                plan["aggregation"] = "count"

    # ========================================================
    # DATE RANGE SAFETY (✅ FIXED)
    # ========================================================
    #
    # ✅ Allow gte/lte operators for date ranges
    # ✅ Only validate exact matches for "exact" operator
    # ✅ Don't reject filters just because they don't match
    #    the first extracted date
    # ========================================================

    exact_date = extract_exact_date(question)

    if exact_date:

        filters = plan.get("filters", [])

        if not isinstance(filters, list):
            filters = []

        date_filters = [
            item
            for item in filters
            if isinstance(item, dict)
            and item.get("field") in DATE_FIELDS
        ]

        # ✅ FIXED: Only validate exact operator
        for item in date_filters:

            operator = item.get("operator", "exact")
            value = item.get("value")

            # ✅ Skip range operators (gte, lte, gt, lt)
            # They are allowed to have different dates
            if operator in {"gte", "lte", "gt", "lt"}:
                continue

            # ✅ Only validate exact/iexact operators
            if operator not in {"exact", "iexact"}:
                continue

            if isinstance(value, str):

                normalized_value = value.strip()

                # ✅ Allow if it matches the extracted date
                if normalized_value.startswith(exact_date):
                    continue

                # ✅ FIXED: Don't reject date ranges!
                # If it's a range query, this is expected
                # Just skip the strict validation
                range_pattern = (
                    r"to|se|till|tak|between|and|through|"
                    r"aur|ke beech|-"
                )

                if re.search(range_pattern, question, flags=re.IGNORECASE):
                    # This is a range query, allow it
                    continue

                # Only reject if it's clearly not a range
                raise QueryValidationError(
                    "The query plan contains a date filter "
                    f"'{value}' but the question explicitly "
                    f"mentions '{exact_date}'."
                )

    # ========================================================
    # UNIQUE KEY SAFETY
    # ========================================================
    #
    # Unique keys can contain date-like strings.
    #
    # Example:
    #
    # 2025-09-12 00:00:00DE-GROW...
    #
    # Therefore we must NOT interpret a date-looking part
    # of a unique_key as integration_date automatically.
    # ========================================================

    for item in plan.get("filters", []):

        if not isinstance(item, dict):
            continue

        if item.get("field") == "unique_key":

            value = item.get("value")

            if not value:
                raise QueryValidationError(
                    "unique_key filter cannot be empty."
                )

            # Preserve the complete unique key exactly.
            item["value"] = str(value).strip()

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    return validate_query_plan(
        query_plan=plan,
        allowed_fields=allowed_fields,
    )
