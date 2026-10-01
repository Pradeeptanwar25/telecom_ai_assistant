import os
import pandas as pd


def generate_excel_report(records, output_folder="reports"):
    """
    Convert database records into an Excel report.
    """

    # Create reports folder
    os.makedirs(output_folder, exist_ok=True)

    # Convert records to DataFrame
    df = pd.DataFrame(records)

    # Remove internal database fields
    columns_to_remove = [
        "id",
        "created_at",
        "updated_at",
    ]

    df = df.drop(
        columns=[
            column
            for column in columns_to_remove
            if column in df.columns
        ],
        errors="ignore",
    )

    # Employee-friendly column names
    column_names = {
        "record_key": "Record Key",
        "circle": "Circle",
        "old_site_id": "Old Site ID",
        "old_toco": "Old Toco",
        "allocation_date": "Allocation Date",
        "issue_closer_date": "Issue Closer Date",
        "final_dismantle_survey_date": "Final Dismantle Survey Date",
        "sreq_creq_raised_date": "SREQ/CREQ Raised Date",
        "dismantle_date": "Dismantle Date",
        "material_pickup_date": "Material Pickup Date",
        "material_submission_date": "Material Submission Date",
        "oci_done_date": "OCI Done Date",
        "dismantling_status": "Dismantling Status",
        "ideploy_status": "iDeploy Status",
        "circle_remarks": "Circle Remarks",
        "detailed_remarks": "Detailed Remarks",
        "circle_remarks_as_on_31_july": "Circle Remarks as on 31-July",
        "short_remarks_as_on_31_july": "Short Remarks as on 31-July",
        "submission_pending_remarks": "Submission Pending Remarks",
    }

    df = df.rename(columns=column_names)

    # Excel file path
    file_path = os.path.join(
        output_folder,
        "DPR_Report.xlsx"
    )

    # Generate Excel
    df.to_excel(
        file_path,
        index=False,
        engine="openpyxl"
    )

    return file_path