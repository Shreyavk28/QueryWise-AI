
import duckdb

from app.services.upload_sql_validator import validate_uploaded_sql


MAX_RESULT_ROWS = 100


def execute_uploaded_query(dataframe, sql: str) -> dict:
    """Validate and execute a SELECT query against uploaded data."""

    try:
        validated_sql = validate_uploaded_sql(
            sql,
            allowed_columns=[
                str(column) for column in dataframe.columns
            ],
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Exactly one SQL statement is allowed.":
            raise ValueError(
                "Multiple SQL statements are not allowed."
            ) from exc

        if message.startswith("Unknown column:"):
            raise ValueError(
                "The SQL query could not be executed against "
                "the uploaded dataset."
            ) from exc

        raise

    connection = duckdb.connect(":memory:")

    try:
        # Prevent SQL from reading external files or network resources.
        connection.execute("SET enable_external_access = false")
        connection.register("uploaded_data", dataframe)

        result = connection.execute(validated_sql)
        columns = [
            description[0] for description in result.description
        ]
        rows = result.fetchmany(MAX_RESULT_ROWS)

        return {
            "sql": validated_sql,
            "columns": columns,
            "rows": [
                {
                    key: value.isoformat()
                    if hasattr(value, "isoformat")
                    else value
                    for key, value in zip(columns, row)
                }
                for row in rows
            ],
            "row_count": len(rows),
        }

    except duckdb.Error as exc:
        raise ValueError(
            "The SQL query could not be executed against "
            "the uploaded dataset."
        ) from exc

    finally:
        connection.close()
