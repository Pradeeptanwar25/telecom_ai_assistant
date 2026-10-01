from pathlib import Path

import pandas as pd
from pypdf import PdfReader


def extract_text_from_pdf(file_path):

    reader = PdfReader(file_path)

    all_text = []

    for page_number, page in enumerate(reader.pages):

        page_text = page.extract_text()

        if page_text:
            all_text.append(
                f"\n--- Page {page_number + 1} ---\n"
            )

            all_text.append(page_text)

    return "\n".join(all_text)


def extract_text_from_excel(file_path):

    excel_file = pd.ExcelFile(file_path)

    all_text = []

    for sheet_name in excel_file.sheet_names:

        dataframe = pd.read_excel(
            file_path,
            sheet_name=sheet_name
        )

        all_text.append(
            f"\n--- Sheet: {sheet_name} ---\n"
        )

        all_text.append(
            dataframe.to_string(index=False)
        )

    return "\n".join(all_text)


def extract_text_from_csv(file_path):

    dataframe = pd.read_csv(file_path)

    return dataframe.to_string(index=False)


def extract_text_from_file(file_path):

    file_path = Path(file_path)

    extension = file_path.suffix.lower()

    if extension == ".pdf":

        return extract_text_from_pdf(file_path)

    elif extension in [".xlsx", ".xls"]:

        return extract_text_from_excel(file_path)

    elif extension == ".csv":

        return extract_text_from_csv(file_path)

    else:

        raise ValueError(
            "Only PDF, Excel and CSV files are supported."
        )