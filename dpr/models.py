from django.db import models


class DprRecord(models.Model):
    record_key = models.CharField(
        max_length=255,
        db_index=True
    )

    circle = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    old_site_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    old_toco = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    allocation_date = models.DateField(
        blank=True,
        null=True
    )

    issue_closer_date = models.DateField(
        blank=True,
        null=True
    )

    final_dismantle_survey_date = models.DateField(
        blank=True,
        null=True
    )

    sreq_creq_raised_date = models.DateField(
        blank=True,
        null=True
    )

    dismantle_date = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    material_pickup_date = models.DateField(
        blank=True,
        null=True
    )

    material_submission_date = models.DateField(
        blank=True,
        null=True
    )

    oci_done_date = models.DateField(
        blank=True,
        null=True
    )

    dismantling_status = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    ideploy_status = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    circle_remarks = models.TextField(
        blank=True,
        null=True
    )

    detailed_remarks = models.TextField(
        blank=True,
        null=True
    )

    circle_remarks_as_on_31_july = models.TextField(
        blank=True,
        null=True
    )

    short_remarks_as_on_31_july = models.TextField(
        blank=True,
        null=True
    )

    submission_pending_remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "dpr_records"

    def __str__(self):
        return self.record_key