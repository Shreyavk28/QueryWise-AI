
import pytest

from app.services.sql_validator import (
    SQLValidationError,
    validate_sql,
)


def test_simple_select_is_allowed():
    sql = validate_sql("SELECT product_name FROM products")

    assert "SELECT" in sql.upper()
    assert "LIMIT 100" in sql.upper()


def test_join_with_aliases_is_allowed():
    sql = validate_sql(
        """
        SELECT p.product_name, SUM(s.quantity * p.unit_price) AS revenue
        FROM products p
        JOIN sales s ON p.id = s.product_id
        GROUP BY p.product_name
        """
    )

    assert "JOIN" in sql.upper()
    assert "LIMIT 100" in sql.upper()


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM products",
        "UPDATE products SET quantity = 0",
        "DROP TABLE products",
        "INSERT INTO products (product_name) VALUES ('Test')",
        "SELECT * FROM customers",
        "SELECT * FROM other_database.products",
        "SELECT product_name FROM products; DELETE FROM products",
        "SELECT product_name FROM products LIMIT 101",
        "SELECT product_name FROM products LIMIT 0",
        "SELECT SLEEP(10) FROM products",
    ],
)
def test_unsafe_queries_are_rejected(sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_empty_query_is_rejected():
    with pytest.raises(SQLValidationError):
        validate_sql("   ")


def test_unknown_qualified_column_is_rejected():
    with pytest.raises(SQLValidationError):
        validate_sql("SELECT p.secret FROM products AS p")


def test_blocks_union_select_from_unknown_table():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT product_name FROM products "
            "UNION SELECT password FROM users"
        )


def test_blocks_sleep_function():
    with pytest.raises(ValueError):
        validate_sql("SELECT SLEEP(10) FROM products")


def test_blocks_select_from_unknown_table():
    with pytest.raises(ValueError):
        validate_sql("SELECT * FROM users")


def test_blocks_multiple_statements():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT * FROM products; SELECT * FROM sales"
        )
        

def test_blocks_unknown_table_inside_subquery():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT product_name FROM products "
            "WHERE id IN (SELECT id FROM users)"
        )


def test_blocks_unknown_table_inside_union():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT product_name FROM products "
            "UNION SELECT product_name FROM customers"
        )


def test_blocks_unknown_qualified_column_in_subquery():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT product_name FROM products "
            "WHERE id IN (SELECT p.password FROM products p)"
        )


def test_rejects_unknown_table_alias():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT x.product_name FROM products p"
        )


def test_blocks_unknown_column_in_select():
    with pytest.raises(ValueError):
        validate_sql("SELECT password FROM products")


def test_blocks_unknown_column_in_where():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT product_name FROM products "
            "WHERE secret_value = 1"
        )


def test_blocks_unknown_column_in_order_by():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT product_name FROM products "
            "ORDER BY secret_value"
        )


def test_blocks_unknown_column_in_group_by():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT category, COUNT(*) FROM products "
            "GROUP BY secret_value"
        )
