import os

import pandas as pd

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from integration.models import IntegrationRecord


def _strip_string_values(dataframe):
    for column in dataframe.select_dtypes(include=["object"]).columns:
        dataframe[column] = dataframe[column].str.strip()

    return dataframe


class Command(BaseCommand):
    help = "Import Integration Tracker CSV into integration PostgreSQL database"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to Integration Tracker CSV file",
        )

    def handle(self, *args, **options):

        csv_file = options["csv_file"]

        # --------------------------------------------------
        # CHECK FILE
        # --------------------------------------------------

        if not os.path.exists(csv_file):
            raise CommandError(
                f"CSV file not found:\n{csv_file}"
            )

        self.stdout.write(
            self.style.NOTICE(
                f"\nReading CSV:\n{csv_file}\n"
            )
        )

        # --------------------------------------------------
        # READ CSV
        # --------------------------------------------------

        try:
            df = pd.read_csv(
                csv_file,
                dtype=str,
                keep_default_na=False,
            )
        except Exception as e:
            raise CommandError(
                f"Failed to read CSV:\n{e}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "CSV loaded successfully."
            )
        )

        self.stdout.write(
            f"Rows   : {len(df)}"
        )

        self.stdout.write(
            f"Columns: {len(df.columns)}"
        )

        # --------------------------------------------------
        # CLEAN COLUMN NAMES
        # --------------------------------------------------

        df.columns = (
            df.columns
            .str.strip()
        )

        # --------------------------------------------------
        # COLUMN MAPPING
        # --------------------------------------------------

        column_mapping = {

            "Unique Key": "unique_key",
            "OEM": "oem",
            "Integration Date": "integration_date",
            "CIRCLE": "circle",
            "Activity Name": "activity_name",
            "Site ID": "site_id",
            "MO NAME": "mo_name",
            "LNBTS ID": "lnbts_id",
            "New NRBTS ID": "new_nrbts_id",
            "Technology (SIWA)": "technology_siwa",
            "5G Configuration": "configuration_5g",
            "OSS Details": "oss_details",
            "Cell ID": "cell_id",
            "CELL COUNT": "cell_count",
            "BSC NAME": "bsc_name",
            "BCF": "bcf",
            "TRX Count": "trx_count",
            "PRE ALARM": "pre_alarm",
            "GPS IP CLK": "gps_ip_clk",
            "RET": "ret",
            "POST VSWR": "post_vswr",
            "POST Alarms": "post_alarms",
            "Activity Mode (SA/NSA)": "activity_mode_sa_nsa",
            "Activity Type (SIWA)": "activity_type_siwa",
            "Band (SIWA)": "band_siwa",
            "CELL STATUS": "cell_status",
            "CTR STATUS": "ctr_status",
            "Integration Remark": "integration_remark",
            "T2T4R": "t2t4r",
            "BBU TYPE": "bbu_type",
            "BB CARD": "bb_card",
            "RRU Type": "rru_type",
            "Media Status": "media_status",
            "Mplane IP": "mplane_ip",
            "SCF PREPARED_BY": "scf_prepared_by",
            "SITE INTEGRATE_BY": "site_integrate_by",
            "Site Status": "site_status",
            "External Alarm Confirmation": "external_alarm_confirmation",
            "SOFT AT STATUS": "soft_at_status",
            "LICENCE Status": "licence_status",
            "ESN NO": "esn_no",
            "Responsibility_for_alarm_clearance":
                "responsibility_for_alarm_clearance",
            "TAC": "tac",
            "PCI TDD 20": "pci_tdd_20",
            "PCI TDD 10/20": "pci_tdd_10_20",
            "PCI FDD 2100": "pci_fdd_2100",
            "PCI FDD 1800": "pci_fdd_1800",
            "PCI L900": "pci_l900",
            "5G PCI": "pci_5g",
            "RSI TDD 20": "rsi_tdd_20",
            "RSI TDD 10/20": "rsi_tdd_10_20",
            "RSI FDD 2100": "rsi_fdd_2100",
            "RSI FDD 1800": "rsi_fdd_1800",
            "RSI L900": "rsi_l900",
            "5G RSI": "rsi_5g",
            "GPL": "gpl",
            "Pre/Post Check": "pre_post_check",
            "CRQ": "crq",
            "Customer Approval": "customer_approval",
            "Old Site ID": "old_site_id",
            "Old Site LNBTS": "old_site_lnbts",
            "Old NRBTS ID": "old_nrbts_id",
            "Old Site OSS": "old_site_oss",
            "Old Site MPlane IP": "old_site_mplane_ip",
            "Old Site Tech": "old_site_tech",
            "Allocated Tech.": "allocated_tech",
            "Deployed Tech.": "deployed_tech",
            "NO OF BBU": "no_of_bbu",
            "MIDS ID": "mids_id",
            "Uploaded By": "uploaded_by",
            "Upload Date": "upload_date",
        }

        # --------------------------------------------------
        # CHECK COLUMNS
        # --------------------------------------------------

        missing_columns = [
            column
            for column in column_mapping
            if column not in df.columns
        ]

        if missing_columns:
            raise CommandError(
                "Missing columns in CSV:\n"
                + "\n".join(missing_columns)
            )

        # --------------------------------------------------
        # RENAME COLUMNS
        # --------------------------------------------------

        df = df.rename(
            columns=column_mapping
        )

        df = _strip_string_values(df)

        # --------------------------------------------------
        # CLEAN EMPTY VALUES
        # --------------------------------------------------

        df = df.replace(
            {
                "": None,
                "nan": None,
                "NaN": None,
                "None": None,
                "NaT": None,
            }
        )

        # --------------------------------------------------
        # DATE CONVERSION
        # --------------------------------------------------

        df["integration_date"] = pd.to_datetime(
            df["integration_date"],
            errors="coerce",
        ).dt.date

        df["upload_date"] = pd.to_datetime(
            df["upload_date"],
            errors="coerce",
        ).dt.date

        # --------------------------------------------------
        # UNIQUE KEY INFORMATION
        #
        # IMPORTANT:
        # Duplicate Unique Keys ARE ALLOWED.
        # Blank Unique Keys ARE ALSO ALLOWED.
        # --------------------------------------------------

        blank_keys = df["unique_key"].isna().sum()

        non_blank_keys = df.loc[
            df["unique_key"].notna(),
            "unique_key"
        ]

        unique_key_count = non_blank_keys.nunique()

        repeated_key_rows = (
            len(non_blank_keys)
            - unique_key_count
        )

        duplicate_keys = (
            non_blank_keys[
                non_blank_keys.duplicated(keep=False)
            ]
            .drop_duplicates()
            .tolist()
        )

        self.stdout.write(
            f"\nEmpty Unique Keys found: {blank_keys}"
        )

        self.stdout.write(
            f"Repeated Unique Key rows: {repeated_key_rows}"
        )

        self.stdout.write(
            f"Repeated Unique Key values: {len(duplicate_keys)}"
        )

        if duplicate_keys:
            self.stdout.write(
                "\nFirst 20 repeated Unique Keys:"
            )

            for key in duplicate_keys[:20]:
                self.stdout.write(
                    f"  {key}"
                )

        self.stdout.write(
            "\nDuplicate Unique Keys will NOT be deleted."
        )

        # --------------------------------------------------
        # PREPARE DATABASE RECORDS
        # --------------------------------------------------

        records = []

        model_fields = [
            field.name
            for field in IntegrationRecord._meta.fields
            if field.name not in [
                "id",
                "created_at",
                "updated_at",
            ]
        ]

        for row in df.to_dict("records"):

            record_data = {
                field: row.get(field)
                for field in model_fields
            }

            records.append(
                IntegrationRecord(**record_data)
            )

        # --------------------------------------------------
        # DATABASE IMPORT
        # --------------------------------------------------

        self.stdout.write(
            "\nStarting database import..."
        )

        batch_size = 1000

        try:

            with transaction.atomic(
                using="integration"
            ):

                IntegrationRecord.objects.using(
                    "integration"
                ).bulk_create(
                    records,
                    batch_size=batch_size,
                )

        except Exception as e:

            raise CommandError(
                f"\nDatabase import failed:\n{e}"
            )

        # --------------------------------------------------
        # VERIFY DATABASE COUNT
        # --------------------------------------------------

        db_count = (
            IntegrationRecord.objects
            .using("integration")
            .count()
        )

        # --------------------------------------------------
        # FINAL RESULT
        # --------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                "\n========================================"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "IMPORT SUCCESSFUL"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            f"CSV rows       : {len(df)}"
        )

        self.stdout.write(
            f"DB rows        : {db_count}"
        )

        self.stdout.write(
            f"Blank keys     : {blank_keys}"
        )

        self.stdout.write(
            f"Repeated keys  : {repeated_key_rows}"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "\nIntegration Tracker import completed."
            )
        )