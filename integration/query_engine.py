from typing import Any, Dict, List, Optional
from decimal import Decimal

from django.db.models import (
    Avg,
    Count,
    Max,
    Min,
    Q,
    Sum,
    FloatField,
    Case,
    When,
    Value,
)
from django.db.models.functions import Cast, TruncMonth, TruncYear, TruncWeek, TruncDay
from django.db import models

from .models import IntegrationRecord


# ============================================================
# DATABASE
# ============================================================

DB_ALIAS = "integration"


# ============================================================
# FIELDS
# ============================================================

DATA_FIELDS = [
    "unique_key", "oem", "integration_date", "circle", "activity_name",
    "site_id", "mo_name", "lnbts_id", "new_nrbts_id", "technology_siwa",
    "configuration_5g", "oss_details", "cell_id", "cell_count", "bsc_name",
    "bcf", "trx_count", "pre_alarm", "gps_ip_clk", "ret", "post_vswr",
    "post_alarms", "activity_mode_sa_nsa", "activity_type_siwa", "band_siwa",
    "cell_status", "ctr_status", "integration_remark", "t2t4r", "bbu_type",
    "bb_card", "rru_type", "media_status", "mplane_ip", "scf_prepared_by",
    "site_integrate_by", "site_status", "external_alarm_confirmation",
    "soft_at_status", "licence_status", "esn_no",
    "responsibility_for_alarm_clearance", "tac", "pci_tdd_20", "pci_tdd_10_20",
    "pci_fdd_2100", "pci_fdd_1800", "pci_l900", "pci_5g", "rsi_tdd_20",
    "rsi_tdd_10_20", "rsi_fdd_2100", "rsi_fdd_1800", "rsi_l900", "rsi_5g",
    "gpl", "pre_post_check", "crq", "customer_approval", "old_site_id",
    "old_site_lnbts", "old_nrbts_id", "old_site_oss", "old_site_mplane_ip",
    "old_site_tech", "allocated_tech", "deployed_tech", "no_of_bbu", "mids_id",
    "uploaded_by", "upload_date",
]


# ============================================================
# SPECIAL FIELD TYPES
# ============================================================

NUMERIC_FIELDS = {
    "cell_count",
    "trx_count",
    "no_of_bbu",
}


DATE_FIELDS = {
    "integration_date",
    "upload_date",
}


# ============================================================
# FILTER OPERATORS
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
# BASIC HELPERS
# ============================================================

def _field_exists(field: str) -> bool:
    return field in DATA_FIELDS


def _get_model_field(field_name: str):
    """
    Return the actual Django model field.
    """
    return IntegrationRecord._meta.get_field(field_name)


# ============================================================
# NUMERIC VALUE CONVERSION
# ============================================================

def _convert_numeric_value(value: Any) -> Any:
    """
    Convert user/LLM numeric value into int/float.

    Examples:

        "12"   -> 12
        "12.5" -> 12.5
        12     -> 12
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value

    value_str = str(value).strip()

    if not value_str:
        return value

    try:
        number = Decimal(value_str)

        if number == number.to_integral_value():
            return int(number)

        return float(number)

    except Exception:
        return value


# ============================================================
# GENERAL VALUE CONVERSION
# ============================================================

def _convert_value(
    field: str,
    value: Any,
) -> Any:
    """
    Convert a filter value according to field type.
    """

    if value is None:
        return None

    # --------------------------------------------------------
    # Numeric fields
    # --------------------------------------------------------

    if field in NUMERIC_FIELDS:

        return _convert_numeric_value(
            value
        )

    # --------------------------------------------------------
    # isnull
    # --------------------------------------------------------

    if isinstance(value, str):

        lowered = value.strip().lower()

        if lowered == "true":
            return True

        if lowered == "false":
            return False

    return value


# ============================================================
# FILTER BUILDING
# ============================================================

def _build_filter_q(
    filter_item: Dict[str, Any],
) -> Q:
    """
    Convert one structured filter into Django Q.

    Numeric fields are handled separately so Django/PostgreSQL
    does not apply text operations such as UPPER() to numeric
    database columns.
    """

    if not isinstance(filter_item, dict):
        raise ValueError(
            "Each filter must be a dictionary."
        )

    field = str(
        filter_item.get(
            "field",
            "",
        )
    ).strip()

    operator = str(
        filter_item.get(
            "operator",
            "iexact",
        )
    ).strip().lower()

    value = filter_item.get(
        "value"
    )

    # --------------------------------------------------------
    # Field validation
    # --------------------------------------------------------

    if not field:
        raise ValueError(
            "Filter field cannot be empty."
        )

    if not _field_exists(field):
        raise ValueError(
            f"Unknown filter field: {field}"
        )

    # --------------------------------------------------------
    # Operator validation
    # --------------------------------------------------------

    if operator not in ALLOWED_OPERATORS:
        raise ValueError(
            f"Unsupported filter operator: {operator}"
        )

    # --------------------------------------------------------
    # isnull
    # --------------------------------------------------------

    if operator == "isnull":

        if isinstance(value, str):

            lowered = value.strip().lower()

            if lowered == "true":
                value = True

            elif lowered == "false":
                value = False

            else:
                raise ValueError(
                    "isnull value must be true or false."
                )

        else:
            value = bool(value)

        return Q(
            **{
                f"{field}__isnull": value
            }
        )

    # ========================================================
    # NUMERIC FIELD
    # ========================================================

    if field in NUMERIC_FIELDS:

        numeric_value = _convert_numeric_value(
            value
        )

        # ----------------------------------------------------
        # Numeric comparison operators
        # ----------------------------------------------------

        if operator in {
            "exact",
            "iexact",
        }:

            return Q(
                **{
                    f"{field}__exact":
                        numeric_value
                }
            )

        if operator == "gt":

            return Q(
                **{
                    f"{field}__gt":
                        numeric_value
                }
            )

        if operator == "gte":

            return Q(
                **{
                    f"{field}__gte":
                        numeric_value
                }
            )

        if operator == "lt":

            return Q(
                **{
                    f"{field}__lt":
                        numeric_value
                }
            )

        if operator == "lte":

            return Q(
                **{
                    f"{field}__lte":
                        numeric_value
                }
            )

        # ----------------------------------------------------
        # Text-style operators on numeric fields
        #
        # Since numeric fields should not use UPPER(),
        # CAST the database value to text.
        # ----------------------------------------------------

        if operator in {
            "contains",
            "icontains",
            "startswith",
            "istartswith",
        }:

            text_value = str(
                value
            )

            cast_expression = Cast(
                field,
                output_field=FloatField(),
            )

            # Django Q cannot directly use a Cast expression
            # as a normal lookup key.
            #
            # Numeric fields therefore use a numeric equality
            # for exact matching and reject unsupported
            # text-style searches.
            raise ValueError(
                f"Operator '{operator}' is not supported "
                f"for numeric field '{field}'. "
                f"Use exact, gt, gte, lt or lte."
            )

        raise ValueError(
            f"Unsupported numeric operator '{operator}' "
            f"for field '{field}'."
        )

    # ========================================================
    # NORMAL TEXT FIELD
    # ========================================================

    converted_value = _convert_value(
        field=field,
        value=value,
    )

    return Q(
        **{
            f"{field}__{operator}":
                converted_value
        }
    )


# ============================================================
# APPLY FILTERS
# ============================================================

def _apply_filters(
    queryset,
    filters: Optional[List[Dict[str, Any]]],
):
    """
    Apply all filters using AND logic.
    """

    if not filters:
        return queryset

    combined_q = Q()

    for filter_item in filters:

        current_q = _build_filter_q(
            filter_item
        )

        combined_q &= current_q

    return queryset.filter(
        combined_q
    )


# ============================================================
# SAFE VALUE CONVERSION
# ============================================================

def _serialize_value(
    value: Any,
) -> Any:
    """
    Convert Django/Python values into JSON-friendly values.
    """

    if value is None:
        return None

    # Date / datetime
    if hasattr(
        value,
        "isoformat",
    ):

        try:
            return value.isoformat()

        except Exception:
            pass

    # Decimal
    if isinstance(
        value,
        Decimal,
    ):

        return float(value)

    return value


# ============================================================
# MODEL INSTANCE → DICT
# ============================================================

def _record_to_dict(
    record: IntegrationRecord,
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]:

    if not fields:
        fields = DATA_FIELDS

    result = {}

    for field in fields:

        if not _field_exists(field):
            continue

        value = getattr(
            record,
            field,
            None,
        )

        result[field] = _serialize_value(
            value
        )

    return result


# ============================================================
# RETRIEVE
# ============================================================

def _execute_retrieve(
    queryset,
    fields: Optional[List[str]],
    limit: int,
    offset: int,
) -> Dict[str, Any]:

    total_count = queryset.count()

    queryset = queryset[offset : offset + limit]

    records = []

    for record in queryset:

        records.append(
            _record_to_dict(
                record=record,
                fields=fields,
            )
        )

    return {
        "count": total_count,
        "records": records,
    }


# ============================================================
# COUNT
# ============================================================

def _execute_count(
    queryset,
) -> Dict[str, Any]:

    total_count = queryset.count()

    return {
        "count": total_count,
        "records": [],
    }


# ============================================================
# ✅ NUMERIC EXPRESSION WITH REGEX VALIDATION
# ============================================================

def _numeric_expression(field: str):
    """
    ✅ Convert VARCHAR numeric column to FloatField
    
    IMPORTANT: Uses REGEX to validate ONLY valid numbers!
    
    Pattern: ^-?\\d+(\\.\\d+)?$
    - Optional minus sign
    - One or more digits
    - Optional decimal part
    
    Converts:
    - "NA", "", NULL → NULL
    - "3+3+3", expressions → NULL
    - "abc", invalid → NULL
    - "123", "45.67", "-789" → FLOAT
    
    Valid inputs:
    - 123
    - -456
    - 789.01
    - -0.5
    
    Invalid inputs (converted to NULL):
    - 3+3+3 (expression)
    - NA (marker)
    - "" (empty)
    - abc (non-numeric)
    - 12x (partial)
    """
    
    return Case(
        # Handle NULL
        When(**{f"{field}__isnull": True}, then=Value(None)),
        # Handle empty strings and markers
        When(**{f"{field}__in": ["", "NA", "na", "N/A", "n/a"]}, then=Value(None)),
        # Use regex to validate numeric format ONLY
        # Pattern: ^-?\d+(\.\d+)?$ matches valid numbers
        When(**{f"{field}__regex": r"^-?\d+(\.\d+)?$"}, then=Cast(field, output_field=FloatField())),
        # Everything else (expressions, invalid formats) → NULL
        default=Value(None),
        output_field=FloatField(),
    )


# ============================================================
# AGGREGATION EXPRESSION
# ============================================================

def _build_aggregation_expression(
    aggregation: str,
    aggregation_field: Optional[str],
):

    aggregation = str(
        aggregation
    ).strip().lower()

    # --------------------------------------------------------
    # COUNT
    # --------------------------------------------------------

    if aggregation == "count":

        return Count("id")

    # --------------------------------------------------------
    # COUNT DISTINCT
    # --------------------------------------------------------

    if aggregation == "count_distinct":

        if not aggregation_field:
            raise ValueError(
                "count_distinct requires aggregation_field."
            )

        return Count(
            aggregation_field,
            distinct=True,
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
            raise ValueError(
                f"{aggregation} requires "
                f"aggregation_field."
            )

        if aggregation_field not in NUMERIC_FIELDS:
            raise ValueError(
                f"{aggregation} is only supported "
                f"for numeric fields: "
                f"{sorted(NUMERIC_FIELDS)}"
            )

        # ✅ USE NEW _numeric_expression WITH REGEX VALIDATION
        numeric_field = _numeric_expression(
            aggregation_field
        )

        if aggregation == "sum":

            return Sum(
                numeric_field
            )

        if aggregation == "avg":

            return Avg(
                numeric_field
            )

        if aggregation == "min":

            return Min(
                numeric_field
            )

        if aggregation == "max":

            return Max(
                numeric_field
            )

    raise ValueError(
        f"Unsupported aggregation: "
        f"{aggregation}"
    )


# ============================================================
# GLOBAL AGGREGATION
# ============================================================

def _execute_global_aggregation(
    queryset,
    aggregation: str,
    aggregation_field: Optional[str],
) -> Dict[str, Any]:

    expression = _build_aggregation_expression(
        aggregation=aggregation,
        aggregation_field=aggregation_field,
    )

    annotation_name = "result"

    data = queryset.aggregate(
        **{
            annotation_name:
                expression
        }
    )

    result_value = data.get(
        annotation_name
    )

    return {
        "count": queryset.count(),
        "records": [
            {
                "result":
                    _serialize_value(
                        result_value
                    )
            }
        ],
    }


# ============================================================
# TEMPORAL AGGREGATION
# ============================================================

def _execute_temporal_aggregation(
    queryset,
    temporal_group: str,
    aggregation: str,
    aggregation_field: Optional[str],
    limit: int,
) -> Dict[str, Any]:
    """✅ Handle month-wise, year-wise, week-wise grouping"""
    
    date_field = "integration_date"
    
    if temporal_group == "month":
        queryset = queryset.annotate(
            time_group=TruncMonth(date_field)
        ).values("time_group")
    elif temporal_group == "year":
        queryset = queryset.annotate(
            time_group=TruncYear(date_field)
        ).values("time_group")
    elif temporal_group == "week":
        queryset = queryset.annotate(
            time_group=TruncWeek(date_field)
        ).values("time_group")
    elif temporal_group == "day":
        queryset = queryset.annotate(
            time_group=TruncDay(date_field)
        ).values("time_group")
    
    expression = _build_aggregation_expression(
        aggregation=aggregation,
        aggregation_field=aggregation_field,
    )
    
    annotation_name = "result"
    
    queryset = queryset.annotate(
        **{
            annotation_name: expression
        }
    ).order_by("time_group")
    
    queryset = queryset[:limit]
    
    records = []
    for row in queryset:
        clean_row = {
            "time_group": _serialize_value(row.get("time_group")),
            annotation_name: _serialize_value(row.get(annotation_name)),
        }
        records.append(clean_row)
    
    return {
        "count": len(records),
        "records": records,
    }


# ============================================================
# GROUPED AGGREGATION
# ============================================================

def _execute_grouped_aggregation(
    queryset,
    group_by: List[str],
    aggregation: str,
    aggregation_field: Optional[str],
    limit: int,
) -> Dict[str, Any]:

    if not group_by:

        return _execute_global_aggregation(
            queryset=queryset,
            aggregation=aggregation,
            aggregation_field=aggregation_field,
        )

    # --------------------------------------------------------
    # Validate group fields
    # --------------------------------------------------------

    for field in group_by:

        if not _field_exists(field):
            raise ValueError(
                f"Unknown group_by field: "
                f"{field}"
            )

    # --------------------------------------------------------
    # Aggregation
    # --------------------------------------------------------

    expression = _build_aggregation_expression(
        aggregation=aggregation,
        aggregation_field=aggregation_field,
    )

    annotation_name = "result"

    grouped_queryset = (
        queryset
        .values(*group_by)
        .annotate(
            **{
                annotation_name:
                    expression
            }
        )
    )

    grouped_queryset = grouped_queryset[:limit]

    records = []

    for row in grouped_queryset:

        clean_row = {}

        for field in group_by:

            clean_row[field] = _serialize_value(
                row.get(field)
            )

        clean_row[
            annotation_name
        ] = _serialize_value(
            row.get(
                annotation_name
            )
        )

        records.append(
            clean_row
        )

    return {
        "count": len(records),
        "records": records,
    }


# ============================================================
# SORTING
# ============================================================

def _apply_sort(
    queryset,
    sort: Optional[List[Any]],
):

    if not sort:
        return queryset

    ordering = []

    for item in sort:

        # ----------------------------------------------------
        # String
        # ----------------------------------------------------

        if isinstance(
            item,
            str,
        ):

            item = item.strip()

            if not item:
                continue

            if item.startswith("-"):

                field = item[1:].strip()

                if not _field_exists(
                    field
                ):
                    raise ValueError(
                        f"Unknown sort field: "
                        f"{field}"
                    )

                ordering.append(
                    f"-{field}"
                )

            else:

                field = item

                if not _field_exists(
                    field
                ):
                    raise ValueError(
                        f"Unknown sort field: "
                        f"{field}"
                    )

                ordering.append(
                    field
                )

            continue

        # ----------------------------------------------------
        # Dictionary
        # ----------------------------------------------------

        if isinstance(
            item,
            dict,
        ):

            field = str(
                item.get(
                    "field",
                    "",
                )
            ).strip()

            direction = str(
                item.get(
                    "direction",
                    "asc",
                )
            ).strip().lower()

            if not _field_exists(
                field
            ):
                raise ValueError(
                    f"Unknown sort field: "
                    f"{field}"
                )

            if direction == "desc":

                ordering.append(
                    f"-{field}"
                )

            else:

                ordering.append(
                    field
                )

            continue

        raise ValueError(
            "Invalid sort format."
        )

    if ordering:

        queryset = queryset.order_by(
            *ordering
        )

    return queryset


# ============================================================
# APPLY DISTINCT
# ============================================================

def _apply_distinct(queryset, distinct: bool, fields: Optional[List[str]] = None, group_by: Optional[List[str]] = None):
    """✅ Apply DISTINCT to queryset"""
    
    if not distinct:
        return queryset
    
    if fields and len(fields) > 0:
        queryset = queryset.values(*fields).distinct()
    elif group_by and len(group_by) > 0:
        queryset = queryset.values(*group_by).distinct()
    else:
        queryset = queryset.distinct()
    
    return queryset


# ============================================================
# MAIN QUERY EXECUTOR
# ============================================================

def execute_query(
    filters=None,
    operation="retrieve",
    limit=500,
    offset=0,
    fields=None,
    group_by=None,
    aggregation=None,
    sort=None,
    aggregation_field=None,
    distinct=False,
    temporal_group=None,
):
    """
    ✅ ENHANCED: Added offset, distinct, temporal_group
    ✅ FIXED: Regex validation for numeric expressions like "3+3+3"
    """

    queryset = (
        IntegrationRecord
        .objects
        .using(DB_ALIAS)
        .all()
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    filters = filters or []
    fields = fields or []
    group_by = group_by or []
    sort = sort or []

    operation = str(
        operation or "retrieve"
    ).strip().lower()

    if aggregation is not None:

        aggregation = str(
            aggregation
        ).strip().lower()

    # --------------------------------------------------------
    # Limit & Offset
    # --------------------------------------------------------

    try:

        limit = int(limit)

    except (
        TypeError,
        ValueError,
    ):

        limit = 500

    if limit < 1:
        limit = 1

    if limit > 5000:
        limit = 5000

    try:
        offset = int(offset)
    except (TypeError, ValueError):
        offset = 0
    
    if offset < 0:
        offset = 0

    # --------------------------------------------------------
    # Validate fields
    # --------------------------------------------------------

    for field in fields:

        if not _field_exists(
            field
        ):
            raise ValueError(
                f"Unknown requested field: "
                f"{field}"
            )

    for field in group_by:

        if not _field_exists(
            field
        ):
            raise ValueError(
                f"Unknown group_by field: "
                f"{field}"
            )

    if aggregation_field:

        if not _field_exists(
            aggregation_field
        ):
            raise ValueError(
                f"Unknown aggregation field: "
                f"{aggregation_field}"
            )

    # ========================================================
    # FILTER
    # ========================================================

    queryset = _apply_filters(
        queryset=queryset,
        filters=filters,
    )

    # ========================================================
    # DISTINCT
    # ========================================================

    if operation == "retrieve":
        queryset = _apply_distinct(
            queryset=queryset,
            distinct=distinct,
            fields=fields,
            group_by=group_by,
        )

    # ========================================================
    # SORT
    # ========================================================

    if operation == "retrieve":

        queryset = _apply_sort(
            queryset=queryset,
            sort=sort,
        )

    # ========================================================
    # RETRIEVE
    # ========================================================

    if operation == "retrieve":

        return _execute_retrieve(
            queryset=queryset,
            fields=fields,
            limit=limit,
            offset=offset,
        )

    # ========================================================
    # COUNT
    # ========================================================

    if operation == "count":

        return _execute_count(
            queryset=queryset
        )

    # ========================================================
    # AGGREGATE
    # ========================================================

    if operation == "aggregate":

        if not aggregation:

            raise ValueError(
                "Aggregation is required "
                "for aggregate operation."
            )

        # ✅ TEMPORAL GROUPING
        if temporal_group:
            return _execute_temporal_aggregation(
                queryset=queryset,
                temporal_group=temporal_group,
                aggregation=aggregation,
                aggregation_field=aggregation_field,
                limit=limit,
            )

        # ✅ GROUPED AGGREGATION
        if group_by:

            return _execute_grouped_aggregation(
                queryset=queryset,
                group_by=group_by,
                aggregation=aggregation,
                aggregation_field=aggregation_field,
                limit=limit,
            )

        # ✅ GLOBAL AGGREGATION
        return _execute_global_aggregation(
            queryset=queryset,
            aggregation=aggregation,
            aggregation_field=aggregation_field,
        )

    # ========================================================
    # INVALID OPERATION
    # ========================================================

    raise ValueError(
        f"Unsupported operation: "
        f"{operation}"
    )


# ============================================================
# COMPATIBILITY WRAPPER
# ============================================================

def execute_integration_query(
    filters=None,
    operation="retrieve",
    limit=500,
    offset=0,
    fields=None,
    group_by=None,
    aggregation=None,
    sort=None,
    aggregation_field=None,
    distinct=False,
    temporal_group=None,
):
    """✅ ENHANCED: Added offset, distinct, temporal_group"""

    return execute_query(
        filters=filters,
        operation=operation,
        limit=limit,
        offset=offset,
        fields=fields,
        group_by=group_by,
        aggregation=aggregation,
        sort=sort,
        aggregation_field=aggregation_field,
        distinct=distinct,
        temporal_group=temporal_group,
    )