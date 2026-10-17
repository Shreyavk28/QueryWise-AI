
import pandas as pd
import pytest

from app.services.upload_query_service import execute_uploaded_query


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        "product": ["Laptop", "Mobile", "Headphones"],
        "category": ["Electronics", "Electronics", "Accessories"],
        "quantity": [5, 10, 8],
        "unit_price": [50000, 20000, 2500],
    })


def test_simple_select(sample_dataframe):
    result = execute_uploaded_query(
        sample_dataframe,
        "SELECT product FROM uploaded_data",
    )

    assert result["row_count"] == 3
    assert result["columns"] == ["product"]
    assert result["rows"][0]["product"] == "Laptop"


def test_aggregate_query(sample_dataframe):
    result = execute_uploaded_query(
        sample_dataframe,
        "SELECT category, SUM(quantity) AS total_quantity "
        "FROM uploaded_data GROUP BY category",
    )

    assert result["row_count"] == 2
    totals = {
        row["category"]: row["total_quantity"]
        for row in result["rows"]
    }
    assert totals["Electronics"] == 15
    assert totals["Accessories"] == 8


def test_reject_empty_query(sample_dataframe):
    with pytest.raises(ValueError, match="cannot be empty"):
        execute_uploaded_query(sample_dataframe, "")


def test_reject_non_select_query(sample_dataframe):
    with pytest.raises(ValueError, match="Only SELECT"):
        execute_uploaded_query(
            sample_dataframe,
            "DELETE FROM uploaded_data",
        )


def test_reject_multiple_statements(sample_dataframe):
    with pytest.raises(ValueError, match="Multiple SQL statements"):
        execute_uploaded_query(
            sample_dataframe,
            "SELECT * FROM uploaded_data; SELECT 1",
        )


def test_invalid_column_returns_safe_error(sample_dataframe):
    with pytest.raises(ValueError, match="could not be executed"):
        execute_uploaded_query(
            sample_dataframe,
            "SELECT unknown_column FROM uploaded_data",
        )


def test_results_are_limited_to_100_rows():
    dataframe = pd.DataFrame({"number": list(range(150))})

    result = execute_uploaded_query(
        dataframe,
        "SELECT number FROM uploaded_data",
    )

    assert result["row_count"] == 100
    assert len(result["rows"]) == 100
    assert "LIMIT 100" in result["sql"]
