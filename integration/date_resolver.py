from __future__ import annotations

from datetime import date, datetime, timedelta
import calendar
import re


# ============================================================
# BASIC DATE PARSER
# ============================================================

def parse_date_value(value):
    """
    Convert common date representations into a Python date.

    Supported examples:
        2025-09-12
        2025-09-12 00:00:00
        12 September 2025
        12 September, 2025
        12-09-2025
        12/09/2025
        2025/09/12
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    if not text:
        return None

    # --------------------------------------------------------
    # Remove unnecessary timestamp
    # --------------------------------------------------------

    text = re.sub(
        r"\s+00:00:00(?:\.\d+)?$",
        "",
        text
    ).strip()

    # --------------------------------------------------------
    # Common formats
    # --------------------------------------------------------

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%b %d %Y",
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                text,
                fmt
            ).date()

        except ValueError:
            continue

    # --------------------------------------------------------
    # Remove comma from:
    # 12 September, 2025
    # --------------------------------------------------------

    text_without_comma = text.replace(
        ",",
        ""
    )

    if text_without_comma != text:

        for fmt in formats:

            try:
                return datetime.strptime(
                    text_without_comma,
                    fmt
                ).date()

            except ValueError:
                continue

    return None


# ============================================================
# MONTH/YEAR RESOLVER
# ============================================================

def parse_month_year(value):
    """
    Convert:
        September 2025
        Sep 2025
        2025-09

    into:
        (2025, 9)
    """

    text = str(value).strip()

    month_year_formats = [
        "%B %Y",
        "%b %Y",
        "%Y-%m",
        "%m-%Y",
    ]

    for fmt in month_year_formats:

        try:

            parsed = datetime.strptime(
                text,
                fmt
            )

            return (
                parsed.year,
                parsed.month
            )

        except ValueError:
            continue

    return None


# ============================================================
# MONTH RANGE
# ============================================================

def month_date_range(
    year,
    month
):
    """
    Return:
        start_date
        next_month_date
    """

    start_date = date(
        year,
        month,
        1
    )

    if month == 12:

        next_month = date(
            year + 1,
            1,
            1
        )

    else:

        next_month = date(
            year,
            month + 1,
            1
        )

    return (
        start_date,
        next_month
    )


# ============================================================
# RELATIVE DATE RANGE
# ============================================================

def resolve_relative_date_range(
    phrase,
    today=None
):
    """
    Resolve natural language date ranges.

    Examples:

        today
        yesterday
        this week
        last week
        this month
        last month
        this year
        last year
    """

    if today is None:
        today = date.today()

    text = str(
        phrase
    ).strip().lower()

    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    if text in {
        "today",
        "aaj"
    }:

        return (
            today,
            today + timedelta(days=1)
        )

    # --------------------------------------------------------
    # YESTERDAY
    # --------------------------------------------------------

    if text in {
        "yesterday",
        "kal"
    }:

        start = today - timedelta(
            days=1
        )

        return (
            start,
            today
        )

    # --------------------------------------------------------
    # THIS WEEK
    # Monday = 0
    # --------------------------------------------------------

    if text in {
        "this week",
        "current week",
        "is week",
        "iss week",
        "yeh week",
        "ye week"
    }:

        start = today - timedelta(
            days=today.weekday()
        )

        end = start + timedelta(
            days=7
        )

        return (
            start,
            end
        )

    # --------------------------------------------------------
    # LAST WEEK
    # --------------------------------------------------------

    if text in {
        "last week",
        "previous week",
        "pichle week",
        "pichhle week"
    }:

        this_week_start = (
            today
            - timedelta(
                days=today.weekday()
            )
        )

        start = (
            this_week_start
            - timedelta(days=7)
        )

        end = this_week_start

        return (
            start,
            end
        )

    # --------------------------------------------------------
    # THIS MONTH
    # --------------------------------------------------------

    if text in {
        "this month",
        "current month",
        "is month",
        "iss month",
        "yeh month",
        "ye month"
    }:

        start = date(
            today.year,
            today.month,
            1
        )

        if today.month == 12:

            end = date(
                today.year + 1,
                1,
                1
            )

        else:

            end = date(
                today.year,
                today.month + 1,
                1
            )

        return (
            start,
            end
        )

    # --------------------------------------------------------
    # LAST MONTH
    # --------------------------------------------------------

    if text in {
        "last month",
        "previous month",
        "pichle month",
        "pichhle month"
    }:

        if today.month == 1:

            start = date(
                today.year - 1,
                12,
                1
            )

            end = date(
                today.year,
                1,
                1
            )

        else:

            start = date(
                today.year,
                today.month - 1,
                1
            )

            end = date(
                today.year,
                today.month,
                1
            )

        return (
            start,
            end
        )

    # --------------------------------------------------------
    # THIS YEAR
    # --------------------------------------------------------

    if text in {
        "this year",
        "current year",
        "is year",
        "iss year",
        "this saal",
        "is saal"
    }:

        start = date(
            today.year,
            1,
            1
        )

        end = date(
            today.year + 1,
            1,
            1
        )

        return (
            start,
            end
        )

    # --------------------------------------------------------
    # LAST YEAR
    # --------------------------------------------------------

    if text in {
        "last year",
        "previous year",
        "pichle year",
        "pichhle year",
        "pichla saal",
        "pichhle saal"
    }:

        start = date(
            today.year - 1,
            1,
            1
        )

        end = date(
            today.year,
            1,
            1
        )

        return (
            start,
            end
        )

    return None


# ============================================================
# NORMALIZE DATE FILTERS
# ============================================================

def normalize_date_filters(
    filters
):
    """
    Normalize date filter values.

    Important:
    This function does NOT convert the actual Django
    lookup into __date.

    It only converts values into ISO date strings.
    """

    normalized = []

    for item in filters or []:

        if not isinstance(
            item,
            dict
        ):
            continue

        current = dict(
            item
        )

        field = current.get(
            "field"
        )

        value = current.get(
            "value"
        )

        if field in {
            "integration_date",
            "upload_date"
        }:

            parsed = parse_date_value(
                value
            )

            if parsed:

                current["value"] = (
                    parsed.isoformat()
                )

        normalized.append(
            current
        )

    return normalized