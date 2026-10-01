import pandas as pd

from django.core.management.base import BaseCommand
from dpr.models import DprRecord


class Command(BaseCommand):
    help = "Import DPR Excel data into PostgreSQL"

    EXCEL_FILE = (
        r"C:\Users\304758\Downloads\DPR_Final_Cleaned.xlsx"
    )

    def clean_value(self, value):
        """
        Convert NaN/NaT to None.
        Convert other values to string where required.
        """
        if pd.isna(value):
            return None

        return value

    def clean_date(self, value):
        """
        Convert Excel date value into Python date.
        """
        if pd.isna(value):
            return None

        date_value = pd.to_datetime(
            value,
            errors="coerce"
        )

        if pd.isna(date_value):
            return None

        return date_value.date()

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.SUCCESS(
                "Reading Excel file..."
            )
        )

        df = pd.read_excel(
            self.EXCEL_FILE
        )

        self.stdout.write(
            f"Excel rows: {len(df)}"
        )

        # ------------------------------------------------
        # Clean key columns
        # ------------------------------------------------

        df["Circle"] = (
            df["Circle"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        df["Old site Id"] = (
            df["Old site Id"]
            .astype("string")
            .str.strip()
        )

        # ------------------------------------------------
        # Create record_key
        # ------------------------------------------------

        df["record_key"] = (
            df["Circle"]
            + "_"
            + df["Old site Id"]
        )

        # ------------------------------------------------
        # Remove invalid keys
        # ------------------------------------------------

        df = df[
            df["Circle"].notna()
            & df["Old site Id"].notna()
        ].copy()

        self.stdout.write(
            f"Valid rows: {len(df)}"
        )

        # ------------------------------------------------
        # Prepare objects
        # ------------------------------------------------

        records = []

        for _, row in df.iterrows():

            record = DprRecord(
                record_key=str(
                    row["record_key"]
                ),

                circle=self.clean_value(
                    row["Circle"]
                ),

                old_site_id=self.clean_value(
                    row["Old site Id"]
                ),

                old_toco=self.clean_value(
                    row["Old Toco"]
                ),

                allocation_date=self.clean_date(
                    row["Allocation Date"]
                ),

                issue_closer_date=self.clean_date(
                    row["Issue Closer Date"]
                ),

                final_dismantle_survey_date=self.clean_date(
                    row["Final Dismantle Survey Date"]
                ),

                sreq_creq_raised_date=self.clean_date(
                    row["SREQ/CREQ Raised Date"]
                ),

                dismantle_date=(
                    str(row["Dismantle Date"])
                    if self.clean_value(
                        row["Dismantle Date"]
                    ) is not None
                    else None
                ),

                material_pickup_date=self.clean_date(
                    row["Material Pickup Date"]
                ),

                material_submission_date=self.clean_date(
                    row["Material Submission Date"]
                ),

                oci_done_date=self.clean_date(
                    row["OCI Done Date"]
                ),

                dismantling_status=self.clean_value(
                    row["Dismantling Status"]
                ),

                ideploy_status=self.clean_value(
                    row["ideploy status"]
                ),

                circle_remarks=self.clean_value(
                    row["Circle Remarks"]
                ),

                detailed_remarks=self.clean_value(
                    row["Detailed Remarks"]
                ),

                circle_remarks_as_on_31_july=self.clean_value(
                    row["Circle Remarks as on 31-July"]
                ),

                short_remarks_as_on_31_july=self.clean_value(
                    row["Short Remarks as on 31-July"]
                ),

                submission_pending_remarks=self.clean_value(
                    row["Submission Pending Remarks"]
                ),
            )

            records.append(record)

        # ------------------------------------------------
        # Bulk insert
        # ------------------------------------------------

        self.stdout.write(
            "Inserting records into PostgreSQL..."
        )

        DprRecord.objects.bulk_create(
            records,
            batch_size=500
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(records)} records."
            )
        )