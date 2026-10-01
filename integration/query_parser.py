from __future__ import annotations

from datetime import date, datetime, timedelta
import calendar
import re
import json
import os
from functools import lru_cache
from datetime import datetime
from difflib import SequenceMatcher

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from integration.models import IntegrationRecord
from integration.query_validator import validate_against_question


load_dotenv()

HF_TOKEN = (
    os.getenv("HUGGINGFACEHUB_API_TOKEN")
    or os.getenv("HF_TOKEN")
)

HF_MODEL = os.getenv(
    "HF_MODEL",
    "openai/gpt-oss-20b"
)

HF_BASE_URL = os.getenv(
    "HF_BASE_URL",
    "https://router.huggingface.co/v1"
)

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

DATE_FIELDS = ["integration_date", "upload_date"]
NUMERIC_FIELDS = ["cell_count", "trx_count", "no_of_bbu", "tac"]
TEXT_FIELDS = ["integration_remark", "post_alarms", "oss_details", "site_status"]

FIELD_DESCRIPTIONS = {
    "unique_key": "Unique Key", "oem": "OEM/vendor", "integration_date": "Integration Date",
    "circle": "Circle", "activity_name": "Activity Name", "site_id": "Site ID",
    "mo_name": "MO NAME", "lnbts_id": "LNBTS ID", "new_nrbts_id": "New NRBTS ID",
    "technology_siwa": "Technology SIWA", "configuration_5g": "5G Configuration",
    "oss_details": "OSS Details", "cell_id": "Cell ID", "cell_count": "Cell Count",
    "bsc_name": "BSC NAME", "bcf": "BCF", "trx_count": "TRX Count", "pre_alarm": "Pre Alarm",
    "gps_ip_clk": "GPS IP CLK", "ret": "RET", "post_vswr": "Post VSWR",
    "post_alarms": "Post Alarms", "activity_mode_sa_nsa": "Activity Mode SA/NSA",
    "activity_type_siwa": "Activity Type SIWA", "band_siwa": "Band SIWA",
    "cell_status": "Cell Status", "ctr_status": "CTR Status",
    "integration_remark": "Integration Remark", "t2t4r": "T2T4R", "bbu_type": "BBU Type",
    "bb_card": "BB Card", "rru_type": "RRU Type", "media_status": "Media Status",
    "mplane_ip": "MPlane IP", "scf_prepared_by": "SCF Prepared By",
    "site_integrate_by": "Site Integrate By", "site_status": "Site Status",
    "external_alarm_confirmation": "External Alarm Confirmation", "soft_at_status": "Soft AT Status",
    "licence_status": "Licence Status", "esn_no": "ESN No",
    "responsibility_for_alarm_clearance": "Responsibility for Alarm Clearance", "tac": "TAC",
    "pci_tdd_20": "PCI TDD 20", "pci_tdd_10_20": "PCI TDD 10/20", "pci_fdd_2100": "PCI FDD 2100",
    "pci_fdd_1800": "PCI FDD 1800", "pci_l900": "PCI L900", "pci_5g": "PCI 5G",
    "rsi_tdd_20": "RSI TDD 20", "rsi_tdd_10_20": "RSI TDD 10/20", "rsi_fdd_2100": "RSI FDD 2100",
    "rsi_fdd_1800": "RSI FDD 1800", "rsi_l900": "RSI L900", "rsi_5g": "RSI 5G", "gpl": "GPL",
    "pre_post_check": "Pre/Post Check", "crq": "CRQ", "customer_approval": "Customer Approval",
    "old_site_id": "Old Site ID", "old_site_lnbts": "Old Site LNBTS", "old_nrbts_id": "Old NRBTS ID",
    "old_site_oss": "Old Site OSS", "old_site_mplane_ip": "Old Site MPlane IP",
    "old_site_tech": "Old Site Technology", "allocated_tech": "Allocated Technology",
    "deployed_tech": "Deployed Technology", "no_of_bbu": "Number of BBU", "mids_id": "MIDS ID",
    "uploaded_by": "Uploaded By", "upload_date": "Upload Date",
}

FIELD_ALIASES = {
    "unique_key": ["unique key", "unique_key", "record key", "record_key", "key"],
    "oem": ["oem", "vendor", "vendor name"],
    "integration_date": ["integration date", "integrated date", "integration_date"],
    "circle": ["circle", "region", "circle name"],
    "activity_name": ["activity name", "activity", "activity_name", "activity type"],
    "site_id": ["site id", "site_id", "site"],
    "mo_name": ["mo name", "mo_name", "mo"],
    "lnbts_id": ["lnbts id", "lnbts_id", "lnbts"],
    "new_nrbts_id": ["new nrbts id", "new_nrbts_id", "new nrbts"],
    "technology_siwa": ["technology siwa", "technology", "tech", "technology_siwa"],
    "configuration_5g": ["5g configuration", "5g config", "configuration 5g", "configuration_5g"],
    "cell_id": ["cell id", "cell_id"],
    "cell_count": ["cell count", "cell_count", "number of cells", "cells", "no of cells"],
    "trx_count": ["trx count", "trx_count", "number of trx", "trx"],
    "ret": ["ret"],
    "activity_mode_sa_nsa": ["activity mode", "sa nsa", "sa/nsa", "activity_mode_sa_nsa"],
    "activity_type_siwa": ["activity type siwa", "activity_type_siwa"],
    "band_siwa": ["band siwa", "band", "band_siwa"],
    "cell_status": ["cell status", "cell_status"],
    "ctr_status": ["ctr status", "ctr_status"],
    "site_status": ["site status", "site_status"],
    "mplane_ip": ["mplane ip", "m plane ip", "mplane_ip"],
    "crq": ["crq"],
    "old_site_id": ["old site id", "old_site_id", "old site"],
    "old_site_lnbts": ["old site lnbts", "old_site_lnbts"],
    "old_nrbts_id": ["old nrbts id", "old_nrbts_id"],
    "allocated_tech": ["allocated tech", "allocated technology", "allocated_tech"],
    "deployed_tech": ["deployed tech", "deployed technology", "deployed_tech"],
    "no_of_bbu": ["no of bbu", "number of bbu", "bbu count", "no_of_bbu"],
    "upload_date": ["upload date", "uploaded date", "upload_date"],
    "integration_remark": ["remark", "remarks", "comment", "comments", "integration_remark"],
    "post_alarms": ["alarms", "alarm", "post_alarms"],
}

SYSTEM_PROMPT = f"""
You are a SUPER-INTELLIGENT query-planning AI for a telecom Integration Tracker database.

HANDLE ALL COMPLEXITY LEVELS including pagination, distinct, and temporal grouping.

Available database fields:

{json.dumps(FIELD_DESCRIPTIONS, indent=2)}

Field aliases:

{json.dumps(FIELD_ALIASES, indent=2)}

Return ONLY valid JSON.

JSON structure:

{{
    "intent": "search",
    "filters": [
        {{
            "field": "circle",
            "operator": "exact",
            "value": "AP"
        }}
    ],
    "operation": "retrieve",
    "fields": [],
    "group_by": [],
    "aggregation": null,
    "aggregation_field": null,
    "sort": [
        {{"field": "cell_count", "order": "desc"}},
        {{"field": "integration_date", "order": "asc"}}
    ],
    "limit": 500,
    "offset": 0,
    "output_format": "text",
    "distinct": false,
    "temporal_group": null
}}

Allowed operations: retrieve, count, aggregate
Allowed aggregations: count, count_distinct, sum, avg, min, max
Allowed operators: exact, iexact, contains, icontains, startswith, istartswith, gt, gte, lt, lte, isnull
Allowed temporal_group: year, month, week, day, null

CRITICAL RULES:

1. For pagination: Set offset (skip N) and limit
2. For distinct: Set distinct=true
3. For temporal: Set temporal_group and operation="aggregate"
4. For month-wise: temporal_group="month", aggregation="count"
5. NEVER invent field names
"""

def _normalize_text(value):
    if value is None:
        return ""
    value = str(value).strip().casefold()
    value = re.sub(r"[^\w]+", " ", value)
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()

def _fuzzy_match(query_term, value_list, threshold=0.8):
    """✅ FUZZY MATCHING for typos"""
    query_norm = _normalize_text(query_term)
    best_match = None
    best_score = 0
    
    for value in value_list:
        value_norm = _normalize_text(value)
        score = SequenceMatcher(None, query_norm, value_norm).ratio()
        
        if score > best_score:
            best_score = score
            best_match = value
    
    if best_score >= threshold:
        return best_match
    
    return None

@lru_cache(maxsize=1)
def _get_value_catalog():
    catalog = {}
    queryset = IntegrationRecord.objects.using("integration").all()

    for field_name in DATA_FIELDS:
        try:
            values = (
                queryset
                .values_list(field_name, flat=True)
                .exclude(**{f"{field_name}__isnull": True})
                .distinct()[:501]
            )
            values = list(values)

            if len(values) > 500:
                continue

            cleaned = []
            for value in values:
                if value is None:
                    continue
                value = str(value).strip()
                if not value:
                    continue
                cleaned.append(value)

            if cleaned:
                catalog[field_name] = cleaned

        except Exception:
            continue

    return catalog

def _resolve_database_values(question, query_plan):
    question_normalized = _normalize_text(question)

    if not question_normalized:
        return query_plan

    skip_keywords = {
        'integration', 'records', 'count', 'batao', 'dikhao',
        'wise', 'ka', 'ke', 'se', 'tak', 'to', 'till',
        'show', 'give', 'how', 'many', 'total', 'number',
        'kitne', 'kitna', 'kitni', 'kul', 'details', 
        'and', 'or', 'from', 'between', 'the', 'a', 'an',
        'aur', 'ki', 'do', 'dikho', 'batao', 'kya', 'ya',
        'highest', 'lowest', 'top', 'bottom', 'max', 'min',
        'without', 'empty', 'null', 'blank', 'containing',
        'page', 'skip', 'unique', 'distinct', 'month', 'year',
    }

    existing_filters = query_plan.get("filters", [])
    catalog = _get_value_catalog()

    for item in existing_filters:
        if not isinstance(item, dict):
            continue

        field_name = item.get("field")
        normalized_value = _normalize_text(item.get("value"))
        if field_name not in catalog or not normalized_value:
            continue

        matching_fields = [
            candidate_field
            for candidate_field, values in catalog.items()
            if any(_normalize_text(value) == normalized_value for value in values)
        ]
        if field_name in matching_fields:
            continue

        if (
            query_plan.get("operation") == "count"
            and "activity_name" in matching_fields
        ):
            corrected_field = "activity_name"
        elif len(matching_fields) == 1:
            corrected_field = matching_fields[0]
        else:
            continue

        item["field"] = corrected_field
        item["operator"] = "iexact"
        item["value"] = next(
            value
            for value in catalog[corrected_field]
            if _normalize_text(value) == normalized_value
        )

    existing_pairs = set()

    for item in existing_filters:
        if not isinstance(item, dict):
            continue
        field = item.get("field")
        value = item.get("value")
        if field:
            existing_pairs.add((field, _normalize_text(value)))

    eligible_fields = {
        item.get("field")
        for item in existing_filters
        if isinstance(item, dict) and item.get("field")
    }
    for field_name in DATA_FIELDS:
        aliases = FIELD_ALIASES.get(field_name)
        if aliases is None:
            aliases = [
                FIELD_DESCRIPTIONS.get(field_name, ""),
                field_name.replace("_", " "),
            ]

        for alias in aliases:
            alias_normalized = _normalize_text(alias)
            if alias_normalized and re.search(
                r"(?<!\w)" + re.escape(alias_normalized) + r"(?!\w)",
                question_normalized,
            ):
                eligible_fields.add(field_name)
                break

    if query_plan.get("operation") == "count":
        planned_fields = {
            item.get("field")
            for item in existing_filters
            if isinstance(item, dict) and item.get("field")
        }
        existing_values = {
            _normalize_text(item.get("value"))
            for item in existing_filters
            if isinstance(item, dict) and item.get("value") is not None
        }
        activity_value_matches = any(
            normalized_value not in existing_values
            and normalized_value not in skip_keywords
            and len(normalized_value) >= 2
            and re.search(
                r"(?<!\w)" + re.escape(normalized_value) + r"(?!\w)",
                question_normalized,
            )
            for normalized_value in (
                _normalize_text(value)
                for value in catalog.get("activity_name", [])
            )
            if normalized_value
        )

        if activity_value_matches:
            eligible_fields.add("activity_name")
            if "ret" not in planned_fields:
                eligible_fields.discard("ret")
        elif not eligible_fields:
            eligible_fields.add("activity_name")

    candidates = []

    for field_name, values in catalog.items():
        if field_name not in eligible_fields:
            continue

        for db_value in values:
            normalized_value = _normalize_text(db_value)

            if not normalized_value:
                continue
            if normalized_value.isdigit():
                continue
            if normalized_value in skip_keywords:
                continue
            if len(normalized_value) < 2:
                continue

            pattern = (
                r"(?<!\w)"
                + re.escape(normalized_value)
                + r"(?!\w)"
            )

            if not re.search(pattern, question_normalized):
                if _fuzzy_match(normalized_value, [question_normalized], threshold=0.75):
                    candidates.append(
                        (len(normalized_value), field_name, db_value, normalized_value)
                    )
                continue

            candidates.append(
                (len(normalized_value), field_name, db_value, normalized_value)
            )

    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = []

    for _, field_name, db_value, normalized_value in candidates:
        pair = (field_name, normalized_value)

        if pair in existing_pairs:
            continue

        already_selected = any(
            item["field"] == field_name
            and _normalize_text(item["value"]) == normalized_value
            for item in selected
        )

        if already_selected:
            continue

        selected.append(
            {
                "field": field_name,
                "operator": "iexact",
                "value": db_value,
            }
        )

    for item in selected:
        field_name = item["field"]

        if any(isinstance(f, dict) and f.get("field") == field_name for f in existing_filters):
            continue

        existing_filters.append(item)

    query_plan["filters"] = existing_filters
    return query_plan

def _extract_single_date_from_question(question):
    question = str(question)

    match = re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", question)
    if match:
        try:
            dt = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    match = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b", question)
    if match:
        try:
            dt = datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    month_map = {
        "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
        "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
        "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10,
        "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
    }

    month_pattern = "|".join(month_map.keys())
    match = re.search(rf"\b(\d{{1,2}})\s+({month_pattern})\s+(20\d{{2}})\b", question, flags=re.IGNORECASE)

    if match:
        day = int(match.group(1))
        month = month_map[match.group(2).casefold()]
        year = int(match.group(3))

        try:
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None

def _parse_date_string(date_str, full_question=""):
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    month_map = {
        "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
        "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
        "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10,
        "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
    }
    
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    for month_name, month_num in month_map.items():
        pattern = rf"^(\d{{1,2}})\s+{month_name}\s+(20\d{{2}})$"
        match = re.match(pattern, date_str, flags=re.IGNORECASE)
        
        if match:
            day = int(match.group(1))
            year = int(match.group(2))
            try:
                dt = datetime(year, month_num, day)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        pattern = rf"^(\d{{1,2}})\s+{month_name}$"
        match = re.match(pattern, date_str, flags=re.IGNORECASE)
        
        if match:
            day = int(match.group(1))
            year_match = re.search(r"20\d{2}", full_question)
            year = int(year_match.group()) if year_match else datetime.now().year
            
            try:
                dt = datetime(year, month_num, day)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
    
    return None

def _extract_date_range_from_question(question):
    question = str(question)
    
    pattern1 = (
        r"(\d{1,2}\s+(?:january|jan|february|feb|march|mar|april|apr|may|"
        r"june|jun|july|jul|august|aug|september|sep|sept|october|oct|"
        r"november|nov|december|dec)(?:\s+20\d{2})?)"
        r"\s+(?:to|se|till|tak|through|-)\s+"
        r"(\d{1,2}\s+(?:january|jan|february|feb|march|mar|april|apr|may|"
        r"june|jun|july|jul|august|aug|september|sep|sept|october|oct|"
        r"november|nov|december|dec)(?:\s+20\d{2})?)"
    )
    
    match = re.search(pattern1, question, flags=re.IGNORECASE)
    
    if match:
        start_str = match.group(1)
        end_str = match.group(2)
        start_date = _parse_date_string(start_str, question)
        end_date = _parse_date_string(end_str, question)
        
        if start_date and end_date:
            return {"start": start_date, "end": end_date, "has_range": True}
    
    return {"start": None, "end": None, "has_range": False}

def _extract_json(text):
    if not text:
        raise ValueError("LLM returned an empty response.")
    
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    
    start = text.find("{")
    end = text.rfind("}")
    
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract valid JSON from LLM response:\n{text}")

def _normalize_query_plan(plan):
    if not isinstance(plan, dict):
        plan = {}

    normalized = {
        "intent": plan.get("intent", "search"),
        "filters": plan.get("filters", []),
        "operation": plan.get("operation", "retrieve"),
        "fields": plan.get("fields", []),
        "group_by": plan.get("group_by", []),
        "aggregation": plan.get("aggregation", None),
        "aggregation_field": plan.get("aggregation_field", None),
        "sort": plan.get("sort", []),
        "limit": plan.get("limit", 500),
        "offset": plan.get("offset", 0),
        "output_format": plan.get("output_format", "text"),
        "distinct": plan.get("distinct", False),
        "temporal_group": plan.get("temporal_group", None),
    }

    if not isinstance(normalized["filters"], list):
        normalized["filters"] = []
    if not isinstance(normalized["fields"], list):
        normalized["fields"] = []
    if not isinstance(normalized["group_by"], list):
        normalized["group_by"] = []
    if not isinstance(normalized["sort"], list):
        normalized["sort"] = []

    try:
        normalized["limit"] = int(normalized["limit"])
    except Exception:
        normalized["limit"] = 500

    try:
        normalized["offset"] = int(normalized["offset"])
    except Exception:
        normalized["offset"] = 0

    if normalized["limit"] <= 0:
        normalized["limit"] = 500
    if normalized["offset"] < 0:
        normalized["offset"] = 0

    normalized["limit"] = min(normalized["limit"], 5000)

    if normalized["intent"] not in {"search"}:
        normalized["intent"] = "search"

    if normalized["operation"] not in {"retrieve", "count", "aggregate"}:
        normalized["operation"] = "retrieve"

    allowed_aggs = {"count", "count_distinct", "sum", "avg", "min", "max"}
    if normalized["aggregation"] not in allowed_aggs:
        if normalized["aggregation"] is not None:
            normalized["aggregation"] = None

    if normalized["output_format"] not in {"text", "table", "excel", "csv"}:
        normalized["output_format"] = "text"

    allowed_temporal = {"year", "month", "week", "day", None}
    if normalized["temporal_group"] not in allowed_temporal:
        normalized["temporal_group"] = None

    return normalized

def _normalize_text_filter_case(query_plan, question):
    if re.search(r"\bcase sensitive\b", _normalize_text(question)):
        return query_plan

    for filter_item in query_plan.get("filters", []):
        if not isinstance(filter_item, dict):
            continue

        field_name = str(filter_item.get("field", "")).strip()
        operator = str(filter_item.get("operator", "")).strip().lower()
        if (
            operator == "exact"
            and field_name not in DATE_FIELDS
            and field_name not in NUMERIC_FIELDS
        ):
            filter_item["operator"] = "iexact"

    return query_plan

def _call_llm(user_question):
    if not HF_TOKEN:
        raise RuntimeError(
            "Hugging Face token not found. "
            "Set HUGGINGFACEHUB_API_TOKEN or HF_TOKEN "
            "in your .env file."
        )

    client = InferenceClient(base_url=HF_BASE_URL, api_key=HF_TOKEN)

    response = client.chat.completions.create(
        model=HF_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_question},
        ],
        max_tokens=1600,
        temperature=0.0,
        extra_body={"reasoning_effort": "low"},
    )

    content = response.choices[0].message.content
    return _extract_json(content)

def _clean_filters_for_groupby(query_plan, question):
    group_by = query_plan.get("group_by", [])
    operation = query_plan.get("operation")
    
    if group_by or operation == "aggregate":
        if "wise" in question.casefold():
            query_plan["filters"] = []
    
    return query_plan

def _apply_generic_count_recovery(query_plan, question):
    q = question.casefold()
    count_patterns = [
        r"\bhow many\b", r"\bnumber of\b", r"\btotal count\b",
        r"\bcount\b", r"\bkitne\b", r"\bkitna\b", r"\bkitni\b",
        r"\bkul\b", r"\btotal\b",
    ]
    is_count_question = any(re.search(pattern, q) for pattern in count_patterns)
    if is_count_question:
        if query_plan.get("operation") == "retrieve":
            query_plan["operation"] = "count"
        elif (
            query_plan.get("operation") == "aggregate"
            and query_plan.get("aggregation") == "count"
            and not query_plan.get("group_by")
            and not query_plan.get("temporal_group")
        ):
            query_plan["operation"] = "count"
            query_plan["aggregation"] = None
            query_plan["aggregation_field"] = None
    return query_plan

def _apply_generic_date_recovery(query_plan, question):
    filters = query_plan.get("filters", [])

    existing_date_filters = [
        item for item in filters
        if isinstance(item, dict) and item.get("field") in DATE_FIELDS
    ]

    if existing_date_filters:
        return query_plan

    question_lower = question.casefold()

    if (
        "upload date" in question_lower
        or "uploaded date" in question_lower
        or "upload" in question_lower
    ):
        date_field = "upload_date"
    else:
        date_field = "integration_date"

    date_range = _extract_date_range_from_question(question)

    if date_range["has_range"]:
        if date_range["start"]:
            filters.append({
                "field": date_field,
                "operator": "gte",
                "value": date_range["start"],
            })

        if date_range["end"]:
            filters.append({
                "field": date_field,
                "operator": "lte",
                "value": date_range["end"],
            })

        query_plan["filters"] = filters
        return query_plan

    date_value = _extract_single_date_from_question(question)

    if date_value:
        filters.append({
            "field": date_field,
            "operator": "exact",
            "value": date_value,
        })

        query_plan["filters"] = filters
        return query_plan

    return query_plan

def _apply_generic_aggregation_recovery(query_plan, question):
    q = _normalize_text(question)

    aggregation_words = [
        "sum", "total", "average", "avg",
        "minimum", "minimum value", "maximum", "maximum value",
    ]

    contains_aggregation_word = any(word in q for word in aggregation_words)

    if not contains_aggregation_word:
        return query_plan

    if query_plan.get("aggregation"):
        return query_plan

    for field_name in NUMERIC_FIELDS:
        aliases = FIELD_ALIASES.get(field_name, [])

        for alias in aliases:
            alias_normalized = _normalize_text(alias)

            if not alias_normalized:
                continue

            if re.search(
                r"(?<!\w)" + re.escape(alias_normalized) + r"(?!\w)", q
            ):

                if "average" in q or "avg" in q:
                    aggregation = "avg"
                elif "minimum" in q or "minimum value" in q:
                    aggregation = "min"
                elif "maximum" in q or "maximum value" in q:
                    aggregation = "max"
                else:
                    aggregation = "sum"

                query_plan["operation"] = "aggregate"
                query_plan["aggregation"] = aggregation
                query_plan["aggregation_field"] = field_name

                return query_plan

    return query_plan

def _apply_sorting_recovery(query_plan, question):
    q = question.casefold()
    
    if "highest" in q or "maximum" in q or "max" in q or "top" in q:
        for field_name in NUMERIC_FIELDS:
            aliases = FIELD_ALIASES.get(field_name, [])
            for alias in aliases:
                if _normalize_text(alias) in _normalize_text(question):
                    query_plan["sort"] = [{"field": field_name, "order": "desc"}]
                    query_plan["limit"] = 10
                    return query_plan
    
    if "lowest" in q or "minimum" in q or "min" in q or "bottom" in q:
        for field_name in NUMERIC_FIELDS:
            aliases = FIELD_ALIASES.get(field_name, [])
            for alias in aliases:
                if _normalize_text(alias) in _normalize_text(question):
                    query_plan["sort"] = [{"field": field_name, "order": "asc"}]
                    query_plan["limit"] = 10
                    return query_plan
    
    return query_plan

def _apply_distinct_recovery(query_plan, question):
    q = question.casefold()
    
    if "unique" in q or "distinct" in q or "alag alag" in q:
        query_plan["distinct"] = True
        if query_plan.get("operation") == "retrieve":
            query_plan["operation"] = "count"
    
    return query_plan

def _apply_null_recovery(query_plan, question):
    """✅ Handle NULL/empty/blank values"""
    
    q = question.casefold()
    
    if "without" in q or "empty" in q or "blank" in q or "no " in q:
        for field_name, aliases in FIELD_ALIASES.items():
            for alias in aliases:
                if _normalize_text(alias) in _normalize_text(question):
                    query_plan["filters"].append({
                        "field": field_name,
                        "operator": "isnull",
                        "value": "true",
                    })
                    return query_plan
    
    return query_plan

def _apply_pattern_recovery(query_plan, question):
    """✅ Handle pattern matching"""
    
    q = question.casefold()
    
    if "containing" in q or "has " in q or "like" in q or "likha" in q:
        for field_name in TEXT_FIELDS:
            aliases = FIELD_ALIASES.get(field_name, [])
            for alias in aliases:
                if _normalize_text(alias) in _normalize_text(question):
                    pattern_match = re.search(rf"(?:containing|has|like|likha)\s+['\"]?([^'\"]+)['\"]?", question, flags=re.IGNORECASE)
                    if pattern_match:
                        pattern_text = pattern_match.group(1).strip()
                        query_plan["filters"].append({
                            "field": field_name,
                            "operator": "icontains",
                            "value": pattern_text,
                        })
                        return query_plan
    
    return query_plan

def _apply_temporal_grouping(query_plan, question):
    """✅ Handle temporal grouping"""
    
    q = question.casefold()
    
    if "month-wise" in q or "monthly" in q or "by month" in q or "month wise" in q:
        query_plan["temporal_group"] = "month"
        if query_plan.get("operation") == "retrieve":
            query_plan["operation"] = "aggregate"
        if not query_plan.get("aggregation"):
            query_plan["aggregation"] = "count"
    
    elif "year-wise" in q or "yearly" in q or "by year" in q or "year wise" in q:
        query_plan["temporal_group"] = "year"
        if query_plan.get("operation") == "retrieve":
            query_plan["operation"] = "aggregate"
        if not query_plan.get("aggregation"):
            query_plan["aggregation"] = "count"
    
    elif "week-wise" in q or "weekly" in q or "by week" in q:
        query_plan["temporal_group"] = "week"
        if query_plan.get("operation") == "retrieve":
            query_plan["operation"] = "aggregate"
        if not query_plan.get("aggregation"):
            query_plan["aggregation"] = "count"
    
    return query_plan

def _apply_pagination_recovery(query_plan, question):
    """✅ Handle pagination"""
    
    q = question.casefold()
    
    page_match = re.search(r"page\s+(\d+)", q)
    if page_match:
        page = int(page_match.group(1))
        query_plan["offset"] = (page - 1) * query_plan.get("limit", 500)
    
    skip_match = re.search(r"skip\s+(\d+)", q)
    if skip_match:
        query_plan["offset"] = int(skip_match.group(1))
    
    return query_plan

def parse_user_query(user_question):
    if not user_question:
        raise ValueError("User question cannot be empty.")

    user_question = str(user_question).strip()

    if not user_question:
        raise ValueError("User question cannot be empty.")

    query_plan = _call_llm(user_question)
    query_plan = _normalize_query_plan(query_plan)
    query_plan = _normalize_text_filter_case(query_plan, user_question)

    query_plan = _clean_filters_for_groupby(query_plan, user_question)

    query_plan = _apply_generic_count_recovery(query_plan, user_question)
    query_plan = _apply_generic_date_recovery(query_plan, user_question)
    query_plan = _apply_generic_aggregation_recovery(query_plan, user_question)
    query_plan = _apply_sorting_recovery(query_plan, user_question)
    query_plan = _apply_distinct_recovery(query_plan, user_question)
    query_plan = _apply_null_recovery(query_plan, user_question)
    query_plan = _apply_pattern_recovery(query_plan, user_question)
    query_plan = _apply_temporal_grouping(query_plan, user_question)
    query_plan = _apply_pagination_recovery(query_plan, user_question)

    has_wise = "wise" in user_question.casefold()
    has_aggregation = query_plan.get("operation") == "aggregate"
    has_group_by = query_plan.get("group_by")
    
    if not (has_wise or has_aggregation or has_group_by):
        query_plan = _resolve_database_values(user_question, query_plan)

    if not (has_wise or has_group_by):
        query_plan = validate_against_question(query_plan, user_question)
    
    query_plan = _clean_filters_for_groupby(query_plan, user_question)
    
    query_plan = _normalize_query_plan(query_plan)

    return query_plan

def clear_value_catalog_cache():
    _get_value_catalog.cache_clear()

def execute_parsed_query(query_plan):
    """
    ✅ Execute parsed query using enhanced query_engine
    Matches query_engine.py signature exactly
    """
    from integration.query_engine import execute_query
    
    return execute_query(
        filters=query_plan.get('filters', []),
        operation=query_plan.get('operation', 'retrieve'),
        limit=query_plan.get('limit', 500),
        offset=query_plan.get('offset', 0),
        fields=query_plan.get('fields', []),
        group_by=query_plan.get('group_by', []),
        aggregation=query_plan.get('aggregation'),
        sort=query_plan.get('sort', []),
        aggregation_field=query_plan.get('aggregation_field'),
        distinct=query_plan.get('distinct', False),
        temporal_group=query_plan.get('temporal_group'),
    )