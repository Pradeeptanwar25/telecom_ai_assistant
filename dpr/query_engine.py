import json
from datetime import datetime

from django.db.models import Q

from .models import DprRecord


# ============================================================
# DATABASE SCHEMA
# ============================================================

def get_dpr_schema():
    """
    Django model se automatically database schema banata hai.
    LLM isi schema ko use karke valid fields identify karega.
    """

    schema = []

    for field in DprRecord._meta.fields:

        # Internal fields ko LLM se hide karna hai
        if field.name in ["id", "created_at", "updated_at"]:
            continue

        schema.append(
            {
                "field": field.name,
                "type": field.get_internal_type(),
                "description": field.verbose_name,
            }
        )

    return schema


def get_schema_text():
    """
    Schema ko JSON string mein convert karta hai.
    """

    return json.dumps(
        get_dpr_schema(),
        indent=2,
        default=str
    )


# ============================================================
# VALID DATABASE FIELDS
# ============================================================

def get_valid_fields():
    """
    Sirf wahi fields return karta hai jo DprRecord model mein hain.
    """

    return {
        field.name
        for field in DprRecord._meta.fields
        if field.name not in ["id", "created_at", "updated_at"]
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
# GET MODEL FIELD
# ============================================================

def get_model_field(field_name):
    """
    Django model se field information nikalta hai.
    """

    try:
        return DprRecord._meta.get_field(field_name)

    except Exception as error:
        raise ValueError(
            f"Invalid database field: {field_name}"
        ) from error


# ============================================================
# DATE FIELD CHECK
# ============================================================

def is_date_field(field_name):
    """
    Check karta hai ki field DateField ya DateTimeField hai.
    """

    field = get_model_field(field_name)

    return field.get_internal_type() in [
        "DateField",
        "DateTimeField",
    ]


# ============================================================
# CONVERT FILTER VALUE
# ============================================================

def convert_filter_value(field_name, value):
    """
    User/LLM ke string value ko database field ke
    appropriate Python type mein convert karta hai.
    """

    if value is None:
        return None

    field = get_model_field(field_name)

    field_type = field.get_internal_type()

    value = str(value).strip()

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if field_type == "DateField":

        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d"
            ).date()

        except ValueError as error:

            raise ValueError(
                f"Invalid date '{value}' for field "
                f"'{field_name}'. Expected YYYY-MM-DD."
            ) from error

    # --------------------------------------------------------
    # DATETIME
    # --------------------------------------------------------

    if field_type == "DateTimeField":

        try:
            return datetime.fromisoformat(value)

        except ValueError as error:

            raise ValueError(
                f"Invalid datetime '{value}' "
                f"for field '{field_name}'."
            ) from error

    # --------------------------------------------------------
    # INTEGER
    # --------------------------------------------------------

    if field_type in [
        "IntegerField",
        "BigIntegerField",
        "PositiveIntegerField",
    ]:

        try:
            return int(value)

        except ValueError as error:

            raise ValueError(
                f"Invalid integer '{value}' "
                f"for field '{field_name}'."
            ) from error

    # --------------------------------------------------------
    # FLOAT / DECIMAL
    # --------------------------------------------------------

    if field_type in [
        "FloatField",
        "DecimalField",
    ]:

        try:
            return float(value)

        except ValueError as error:

            raise ValueError(
                f"Invalid numeric value '{value}' "
                f"for field '{field_name}'."
            ) from error

    # --------------------------------------------------------
    # TEXT / CHAR FIELD
    # --------------------------------------------------------

    return value


# ============================================================
# NORMALIZE FILTERS
# ============================================================

def normalize_filters(filters):
    """
    LLM filters ko ek standard format mein convert karta hai.

    Supported formats:

    1.
    {
        "field": "circle",
        "operator": "=",
        "value": "DEL"
    }

    2.
    {
        "circle": "DEL"
    }

    3.
    [
        {
            "field": "circle",
            "operator": "=",
            "value": "DEL"
        }
    ]
    """

    normalized = []

    # --------------------------------------------------------
    # FILTER IS DICTIONARY
    # --------------------------------------------------------

    if isinstance(filters, dict):

        # Standard filter format
        if "field" in filters:

            field = filters.get("field")

            operator = filters.get(
                "operator",
                "="
            )

            value = filters.get("value")

            if field:

                normalized.append(
                    {
                        "field": field,
                        "operator": operator,
                        "value": value,
                    }
                )

        # Simple dictionary format
        else:

            for field, value in filters.items():

                normalized.append(
                    {
                        "field": field,
                        "operator": "=",
                        "value": value,
                    }
                )

        return normalized

    # --------------------------------------------------------
    # FILTER IS LIST
    # --------------------------------------------------------

    if isinstance(filters, list):

        for item in filters:

            if not isinstance(item, dict):
                continue

            # Standard format
            if "field" in item:

                field = item.get("field")

                operator = item.get(
                    "operator",
                    "="
                )

                value = item.get("value")

                if field:

                    normalized.append(
                        {
                            "field": field,
                            "operator": operator,
                            "value": value,
                        }
                    )

                continue

            # Simple dictionary inside list
            for field, value in item.items():

                normalized.append(
                    {
                        "field": field,
                        "operator": "=",
                        "value": value,
                    }
                )

        return normalized

    return normalized


# ============================================================
# APPLY ONE FILTER
# ============================================================

def apply_filter(
    queryset,
    field,
    operator,
    value
):
    """
    Ek filter ko Django QuerySet par apply karta hai.
    """

    # --------------------------------------------------------
    # CHECK OPERATOR
    # --------------------------------------------------------

    if operator not in VALID_OPERATORS:

        raise ValueError(
            f"Invalid operator: {operator}. "
            f"Allowed operators: "
            f"{sorted(VALID_OPERATORS)}"
        )

    # ========================================================
    # ISNULL
    # ========================================================

    if operator == "isnull":

        """
        Examples:

        Missing OCI date
            ↓
        oci_done_date IS NULL

        Available OCI date
            ↓
        oci_done_date IS NOT NULL
        """

        # ----------------------------------------------------
        # Empty / None value
        # ----------------------------------------------------

        if value is None or str(value).strip() == "":

            # Empty value for "missing" means NULL
            is_null = True

        # ----------------------------------------------------
        # Boolean
        # ----------------------------------------------------

        elif isinstance(value, bool):

            is_null = value

        # ----------------------------------------------------
        # String
        # ----------------------------------------------------

        else:

            value_string = str(
                value
            ).strip().lower()

            # Means NULL
            if value_string in [
                "true",
                "yes",
                "null",
                "missing",
                "blank",
            ]:

                is_null = True

            # Means NOT NULL
            elif value_string in [
                "false",
                "no",
                "not null",
                "notnull",
                "available",
                "present",
            ]:

                is_null = False

            else:

                raise ValueError(
                    f"Invalid isnull value: {value}"
                )

        # ----------------------------------------------------
        # Apply IS NULL / IS NOT NULL
        # ----------------------------------------------------

        return queryset.filter(
            **{
                f"{field}__isnull": is_null
            }
        )

    # ========================================================
    # NONE VALUE
    # ========================================================

    if value is None:
        return queryset

    value = str(value).strip()

    # Empty normal filter
    if not value:
        return queryset

    # ========================================================
    # CONTAINS
    # ========================================================

    if operator == "contains":

        return queryset.filter(
            **{
                f"{field}__icontains": value
            }
        )

    # ========================================================
    # EXACT MATCH
    # ========================================================

    if operator == "=":

        model_field = get_model_field(
            field
        )

        field_type = model_field.get_internal_type()

        # ----------------------------------------------------
        # TEXT FIELDS
        # ----------------------------------------------------

        if field_type in [
            "CharField",
            "TextField",
            "EmailField",
            "SlugField",
        ]:

            return queryset.filter(
                **{
                    f"{field}__iexact": value
                }
            )

        # ----------------------------------------------------
        # DATE / NUMBER / OTHER FIELDS
        # ----------------------------------------------------

        converted_value = convert_filter_value(
            field,
            value
        )

        return queryset.filter(
            **{
                field: converted_value
            }
        )

    # ========================================================
    # COMPARISON OPERATORS
    # ========================================================

    converted_value = convert_filter_value(
        field,
        value
    )

    lookup_map = {
        ">": "gt",
        "<": "lt",
        ">=": "gte",
        "<=": "lte",
    }

    lookup = lookup_map[operator]

    return queryset.filter(
        **{
            f"{field}__{lookup}": converted_value
        }
    )


# ============================================================
# APPLY ALL FILTERS
# ============================================================

def apply_filters(
    queryset,
    filters
):
    """
    Multiple filters ko sequentially apply karta hai.

    Example:

    circle = DEL
    AND
    dismantling_status contains pending

    Result:

    DEL
       ↓
    pending
    """

    for filter_item in filters:

        field = filter_item["field"]

        operator = filter_item.get(
            "operator",
            "="
        )

        value = filter_item.get(
            "value"
        )

        # ----------------------------------------------------
        # Validate field
        # ----------------------------------------------------

        if field not in get_valid_fields():

            raise ValueError(
                f"Invalid database field: {field}"
            )

        # ----------------------------------------------------
        # Apply filter
        # ----------------------------------------------------

        queryset = apply_filter(
            queryset,
            field,
            operator,
            value
        )

    return queryset


# ============================================================
# APPLY REQUESTED FIELDS
# ============================================================

def apply_requested_fields(
    queryset,
    fields
):
    """
    Agar user specific columns maangta hai,
    to sirf wahi columns return karega.

    Example:

    "site id aur circle dikhao"

    fields:

    [
        "old_site_id",
        "circle"
    ]
    """

    # --------------------------------------------------------
    # No specific fields
    # --------------------------------------------------------

    if not fields:

        return queryset.values()

    valid_fields = get_valid_fields()

    selected_fields = []

    # --------------------------------------------------------
    # Validate requested fields
    # --------------------------------------------------------

    for field in fields:

        if field not in valid_fields:

            raise ValueError(
                f"Invalid requested field: {field}"
            )

        selected_fields.append(field)

    # --------------------------------------------------------
    # Return selected fields
    # --------------------------------------------------------

    return queryset.values(
        *selected_fields
    )


# ============================================================
# EXECUTE QUERY
# ============================================================

def execute_query(parsed_query):
    """
    LLM ke structured query ko actual Django ORM query
    mein convert karke PostgreSQL se exact data nikalta hai.
    """

    # --------------------------------------------------------
    # Start with all DPR records
    # --------------------------------------------------------

    queryset = DprRecord.objects.all()

    # --------------------------------------------------------
    # Get filters from LLM
    # --------------------------------------------------------

    raw_filters = parsed_query.get(
        "filters",
        []
    )

    # --------------------------------------------------------
    # Normalize filters
    # --------------------------------------------------------

    filters = normalize_filters(
        raw_filters
    )

    # --------------------------------------------------------
    # Apply filters
    # --------------------------------------------------------

    queryset = apply_filters(
        queryset,
        filters
    )

    # --------------------------------------------------------
    # Get operation
    # --------------------------------------------------------

    operation = parsed_query.get(
        "operation",
        "retrieve"
    )

    # ========================================================
    # COUNT
    # ========================================================

    if operation == "count":

        return {
            "count": queryset.count(),
            "records": [],
        }

    # ========================================================
    # TOTAL COUNT
    # ========================================================

    total_count = queryset.count()

    # ========================================================
    # REQUESTED FIELDS
    # ========================================================

    fields = parsed_query.get(
        "fields",
        []
    )

    values_queryset = apply_requested_fields(
        queryset,
        fields
    )

    # ========================================================
    # LIMIT RECORDS
    # ========================================================

    # Maximum 500 records preview/download
    records = list(
        values_queryset[:500]
    )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {
        "count": total_count,
        "records": records,
    }