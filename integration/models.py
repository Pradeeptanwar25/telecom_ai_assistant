from django.db import models


class IntegrationRecord(models.Model):
    unique_key = models.TextField(
        blank=True,
        null=True,
        db_index=True,
    )

    oem = models.CharField(max_length=100, blank=True, null=True)
    integration_date = models.DateField(blank=True, null=True)
    circle = models.CharField(max_length=100, blank=True, null=True)
    activity_name = models.TextField(blank=True, null=True)
    site_id = models.CharField(max_length=255, blank=True, null=True)
    mo_name = models.TextField(blank=True, null=True)
    lnbts_id = models.CharField(max_length=255, blank=True, null=True)
    new_nrbts_id = models.CharField(max_length=255, blank=True, null=True)
    technology_siwa = models.CharField(max_length=255, blank=True, null=True)
    configuration_5g = models.TextField(blank=True, null=True)
    oss_details = models.TextField(blank=True, null=True)
    cell_id = models.CharField(max_length=255, blank=True, null=True)
    cell_count = models.CharField(max_length=100, blank=True, null=True)
    bsc_name = models.CharField(max_length=255, blank=True, null=True)
    bcf = models.CharField(max_length=255, blank=True, null=True)
    trx_count = models.CharField(max_length=100, blank=True, null=True)
    pre_alarm = models.TextField(blank=True, null=True)
    gps_ip_clk = models.TextField(blank=True, null=True)
    ret = models.TextField(blank=True, null=True)
    post_vswr = models.TextField(blank=True, null=True)
    post_alarms = models.TextField(blank=True, null=True)

    activity_mode_sa_nsa = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    activity_type_siwa = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    band_siwa = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    cell_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    ctr_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    integration_remark = models.TextField(
        blank=True,
        null=True,
    )

    t2t4r = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    bbu_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    bb_card = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    rru_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    media_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    mplane_ip = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    scf_prepared_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    site_integrate_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    site_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    external_alarm_confirmation = models.TextField(
        blank=True,
        null=True,
    )

    soft_at_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    licence_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    esn_no = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    responsibility_for_alarm_clearance = models.TextField(
        blank=True,
        null=True,
    )

    tac = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    pci_tdd_20 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    pci_tdd_10_20 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    pci_fdd_2100 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    pci_fdd_1800 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    pci_l900 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    pci_5g = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    rsi_tdd_20 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    rsi_tdd_10_20 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    rsi_fdd_2100 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    rsi_fdd_1800 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    rsi_l900 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    rsi_5g = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    gpl = models.TextField(
        blank=True,
        null=True,
    )

    pre_post_check = models.TextField(
        blank=True,
        null=True,
    )

    crq = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    customer_approval = models.TextField(
        blank=True,
        null=True,
    )

    old_site_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    old_site_lnbts = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    old_nrbts_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    old_site_oss = models.TextField(
        blank=True,
        null=True,
    )

    old_site_mplane_ip = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    old_site_tech = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    allocated_tech = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    deployed_tech = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    no_of_bbu = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    mids_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    uploaded_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    upload_date = models.DateField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "integration_records"

    def __str__(self):
        return self.unique_key or f"IntegrationRecord {self.id}"