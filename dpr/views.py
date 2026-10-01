from django.db.models import Q
from django.http import JsonResponse

from .models import DprRecord


def search_dpr(request):
    """
    Search DPR records using PostgreSQL.
    """

    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({
            "error": "Please provide a search query."
        }, status=400)

    # --------------------------------------------------
    # Search across important DPR fields
    # --------------------------------------------------

    records = DprRecord.objects.filter(
        Q(record_key__icontains=query)
        | Q(circle__icontains=query)
        | Q(old_site_id__icontains=query)
        | Q(old_toco__icontains=query)
        | Q(dismantling_status__icontains=query)
        | Q(ideploy_status__icontains=query)
        | Q(circle_remarks__icontains=query)
        | Q(detailed_remarks__icontains=query)
        | Q(circle_remarks_as_on_31_july__icontains=query)
        | Q(short_remarks_as_on_31_july__icontains=query)
        | Q(submission_pending_remarks__icontains=query)
    )

    results = []

    for record in records[:100]:

        results.append({
            "id": record.id,
            "record_key": record.record_key,
            "circle": record.circle,
            "old_site_id": record.old_site_id,
            "old_toco": record.old_toco,
            "allocation_date": record.allocation_date,
            "issue_closer_date": record.issue_closer_date,
            "final_dismantle_survey_date":
                record.final_dismantle_survey_date,
            "sreq_creq_raised_date":
                record.sreq_creq_raised_date,
            "dismantle_date": record.dismantle_date,
            "material_pickup_date":
                record.material_pickup_date,
            "material_submission_date":
                record.material_submission_date,
            "oci_done_date": record.oci_done_date,
            "dismantling_status":
                record.dismantling_status,
            "ideploy_status":
                record.ideploy_status,
            "circle_remarks":
                record.circle_remarks,
            "detailed_remarks":
                record.detailed_remarks,
            "circle_remarks_as_on_31_july":
                record.circle_remarks_as_on_31_july,
            "short_remarks_as_on_31_july":
                record.short_remarks_as_on_31_july,
            "submission_pending_remarks":
                record.submission_pending_remarks,
        })

    return JsonResponse({
        "query": query,
        "count": records.count(),
        "results": results,
    })