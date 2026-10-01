from io import BytesIO

import pandas as pd


# ============================================================
# EXCEL
# ============================================================

def generate_integration_excel(
    records
):

    df = pd.DataFrame(
        records
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Integration Tracker"
        )

    output.seek(
        0
    )

    return output.getvalue()


# ============================================================
# CSV
# ============================================================

def generate_integration_csv(
    records
):

    df = pd.DataFrame(
        records
    )

    return (
        df
        .to_csv(
            index=False
        )
        .encode(
            "utf-8"
        )
    )