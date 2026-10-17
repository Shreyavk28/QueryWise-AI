
import io

import pandas as pd
import pytest

from app.services.upload_service import load_uploaded_dataset


def test_valid_csv_upload():
    content = b"product,quantity\nLaptop,5\nMobile,10\n"

    result = load_uploaded_dataset("products.csv", content)

    assert result["row_count"] == 2
    assert result["column_count"] == 2
    assert result["rows"][0]["product"] == "Laptop"


def test_valid_xlsx_upload():
    buffer = io.BytesIO()

    dataframe = pd.DataFrame({
        "product": ["Laptop", "Mobile"],
        "quantity": [5, 10],
    })

    dataframe.to_excel(buffer, index=False, engine="openpyxl")

    result = load_uploaded_dataset("products.xlsx", buffer.getvalue())

    assert result["row_count"] == 2
    assert result["rows"][1]["product"] == "Mobile"


def test_reject_unsupported_file():
    with pytest.raises(ValueError, match="Only CSV and XLSX"):
        load_uploaded_dataset("products.json", b'{"product": "Laptop"}')


def test_reject_empty_file():
    with pytest.raises(ValueError, match="empty"):
        load_uploaded_dataset("products.csv", b"")


def test_reject_file_over_size_limit():
    content = b"a" * (5 * 1024 * 1024 + 1)

    with pytest.raises(ValueError, match="5 MB"):
        load_uploaded_dataset("products.csv", content)


def test_reject_duplicate_column_names():
    content = b"Product,product\nLaptop,Computer\n"

    with pytest.raises(ValueError, match="unique"):
        load_uploaded_dataset("products.csv", content)


def test_preview_contains_only_first_ten_rows():
    dataframe = pd.DataFrame({
        "number": list(range(15)),
    })

    content = dataframe.to_csv(index=False).encode("utf-8")

    result = load_uploaded_dataset("numbers.csv", content)

    assert result["row_count"] == 15
    assert len(result["rows"]) == 10
