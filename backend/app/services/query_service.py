
import logging
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
from app.services.sql_validator import validate_sql


logger = logging.getLogger("querywise.query_service")

QUERY_TIMEOUT_MS = 5000


def execute_readonly_query(sql: str) -> dict:
    """
    Validate and execute a read-only query.

    Security relies on both SQL validation and a database user
    that has SELECT-only permissions.
    """
    # Validate before opening a database connection.
    safe_sql = validate_sql(sql)

    try:
        with engine.connect() as connection:
            # Set a per-session execution limit for SELECT queries.
            connection.exec_driver_sql(
                f"SET SESSION max_execution_time = {QUERY_TIMEOUT_MS}"
            )

            result = connection.execute(text(safe_sql))

            columns = list(result.keys())
            rows = [
                dict(row._mapping)
                for row in result.fetchall()
            ]

        # Convert values such as Decimal and dates into JSON-friendly values.
        for row in rows:
            for key, value in row.items():
                if isinstance(value, Decimal):
                    row[key] = str(value)
                elif isinstance(value, (datetime, date)):
                    row[key] = value.isoformat()
                elif value is not None and not isinstance(
                    value, (str, int, float, bool)
                ):
                    row[key] = str(value)

        return {
            "sql": safe_sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }

    except SQLAlchemyError as exc:
        # Log the exception type, not SQL or credentials.
        logger.error(
            "Read-only query execution failed: %s",
            type(exc).__name__,
        )
        raise RuntimeError(
            "The database query could not be completed."
        ) from exc
