
import pytest

from app.services.upload_sql_validator import validate_uploaded_sql


COLUMNS = ["product", "category", "quantity", "unit_price"]


def test_valid_select():
    sql = validate_uploaded_sql(
        "SELECT product FROM uploaded_data",
        COLUMNS,
    )
    assert "uploaded_data" in sql.lower()
    assert "limit 100" in sql.lower()


def test_valid_aggregate():
    sql = validate_uploaded_sql(
        "SELECT category, SUM(quantity) AS total "
        "FROM uploaded_data GROUP BY category",
        COLUMNS,
    )
    assert "SUM(quantity)" in sql


def test_reject_unknown_table():
    with pytest.raises(ValueError, match="Only the uploaded_data"):
        validate_uploaded_sql(
            "SELECT * FROM customers",
            COLUMNS,
        )


def test_reject_unknown_column():
    with pytest.raises(ValueError, match="Unknown column"):
        validate_uploaded_sql(
            "SELECT salary FROM uploaded_data",
            COLUMNS,
        )


def test_reject_delete():
    with pytest.raises(ValueError, match="Only SELECT"):
        validate_uploaded_sql(
            "DELETE FROM uploaded_data",
            COLUMNS,
        )


def test_reject_multiple_statements():
    with pytest.raises(ValueError, match="Exactly one"):
        validate_uploaded_sql(
            "SELECT product FROM uploaded_data; SELECT 1",
            COLUMNS,
        )


def test_reject_sleep_function():
    with pytest.raises(ValueError, match="SLEEP"):
        validate_uploaded_sql(
            "SELECT SLEEP(10) FROM uploaded_data",
            COLUMNS,
        )


def test_reject_external_file_function():
    with pytest.raises(ValueError, match="READ_CSV"):
        validate_uploaded_sql(
            "SELECT * FROM read_csv('secret.csv')",
            COLUMNS,
        )


def test_reject_limit_over_100():
    with pytest.raises(ValueError, match="between 1 and 100"):
        validate_uploaded_sql(
            "SELECT product FROM uploaded_data LIMIT 101",
            COLUMNS,
        )


def test_reject_zero_limit():
    with pytest.raises(ValueError, match="between 1 and 100"):
        validate_uploaded_sql(
            "SELECT product FROM uploaded_data LIMIT 0",
            COLUMNS,
        )
