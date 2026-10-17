
from io import BytesIO, StringIO

import pandas as pd


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_ROWS = 10_000
MAX_COLUMNS = 100


def load_uploaded_dataframe(
    filename: str,
    file_content: bytes,
) -> pd.DataFrame:
    """Validate and load an uploaded CSV or XLSX file."""

    if not filename:
        raise ValueError("A filename is required.")

    extension = filename.rsplit(".", 1)[-1].lower()

    if extension not in {"csv", "xlsx"}:
        raise ValueError("Only CSV and XLSX files are supported.")

    if not file_content:
        raise ValueError("The uploaded file is empty.")

    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError("File size must not exceed 5 MB.")

    try:
        if extension == "csv":
            dataframe = pd.read_csv(
                StringIO(file_content.decode("utf-8-sig")),
                nrows=MAX_ROWS + 1,
            )
        else:
            dataframe = pd.read_excel(
                BytesIO(file_content),
                nrows=MAX_ROWS + 1,
                engine="openpyxl",
            )
    except Exception as exc:
        raise ValueError(
            "Unable to read this file. Please upload a valid CSV or XLSX file."
        ) from exc

    if dataframe.empty:
        raise ValueError("The uploaded file has no data rows.")

    if len(dataframe) > MAX_ROWS:
        raise ValueError("The file must contain no more than 10,000 rows.")

    if len(dataframe.columns) == 0:
        raise ValueError("The file must contain column headers.")

    if len(dataframe.columns) > MAX_COLUMNS:
        raise ValueError("The file must contain no more than 100 columns.")

    columns = [str(column).strip() for column in dataframe.columns]

    if any(not column for column in columns):
        raise ValueError("Column names cannot be empty.")

    normalized = [column.casefold() for column in columns]

    if len(normalized) != len(set(normalized)):
        raise ValueError("Column names must be unique, ignoring case.")

    dataframe.columns = columns

    # Keep the actual DataFrame for querying; do not truncate it to 10 rows.
    return dataframe


def load_uploaded_dataset(
    filename: str,
    file_content: bytes,
) -> dict:
    """Load an uploaded file and return a JSON-safe preview."""

    dataframe = load_uploaded_dataframe(filename, file_content)

    preview = dataframe.head(10).astype(object).where(
        pd.notna(dataframe.head(10)), None
    )

    return {
        "columns": [
            {"name": str(column), "dtype": str(dtype)}
            for column, dtype in zip(
                dataframe.columns,
                dataframe.dtypes,
            )
        ],
        "rows": preview.to_dict(orient="records"),
        "row_count": len(dataframe),
        "column_count": len(dataframe.columns),
    }
