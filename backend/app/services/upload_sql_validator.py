
import sqlglot
from sqlglot import exp


MAX_ROWS = 100

BLOCKED_FUNCTIONS = {
    "SLEEP",
    "BENCHMARK",
    "LOAD_FILE",
    "READ_CSV",
    "READ_PARQUET",
    "READ_JSON",
    "READ_TEXT",
    "READ_BLOB",
    "QUERY",
    "QUERY_TABLE",
    "SUMMARIZE",
    "GLOB",
}


def validate_uploaded_sql(sql: str, allowed_columns: list[str]) -> str:
    """Validate a single SELECT query against an uploaded dataset."""

    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except sqlglot.errors.ParseError as exc:
        raise ValueError("Invalid SQL syntax.") from exc

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is allowed.")

    tree = statements[0]

    if not isinstance(tree, exp.Select):
        raise ValueError("Only SELECT queries are allowed.")

    # Reject dangerous functions.
    for node in tree.walk():
        function_name = ""

        if isinstance(node, exp.Anonymous):
            function_name = node.name.upper()
        elif isinstance(node, exp.Func):
            function_name = node.sql_name().upper()

        if function_name in BLOCKED_FUNCTIONS:
            raise ValueError(
                f"The {function_name} function is not allowed."
            )

    # Allow only the uploaded_data table, including nested queries.
    tables = list(tree.find_all(exp.Table))

    if not tables:
        raise ValueError("Query must read from uploaded_data.")

    for table in tables:
        table_name = table.name.casefold()

        if table_name in {name.casefold() for name in BLOCKED_FUNCTIONS}:
            raise ValueError(
                f"The {table_name.upper()} function is not allowed."
            )

        if table_name != "uploaded_data":
            raise ValueError("Only the uploaded_data table is allowed.")

        if table.db or table.catalog:
            raise ValueError("Qualified table names are not allowed.")

    allowed = {column.casefold() for column in allowed_columns}

    # Validate column references, while permitting aliases in ORDER BY.
    for select in tree.find_all(exp.Select):
        aliases = {
            projection.alias.casefold()
            for projection in select.expressions
            if projection.alias
        }

        for column in select.find_all(exp.Column):
            # Nested SELECT columns are checked in their own scope.
            if column.find_ancestor(exp.Select) is not select:
                continue

            if column.is_star:
                continue

            if column.table:
                if column.table.casefold() != "uploaded_data":
                    raise ValueError("Unknown table alias.")

            column_name = column.name.casefold()

            # A SELECT alias may be referenced in ORDER BY.
            in_order_by = column.find_ancestor(exp.Order) is not None

            if in_order_by and not column.table and column_name in aliases:
                continue

            if column_name not in allowed:
                raise ValueError(f"Unknown column: {column.name}")

    # Enforce a maximum result size.
    limit = tree.args.get("limit")

    if limit is None:
        tree = tree.limit(MAX_ROWS)
    else:
        limit_value = limit.expression

        if (
            not isinstance(limit_value, exp.Literal)
            or limit_value.is_string
        ):
            raise ValueError("LIMIT must be a positive integer.")

        try:
            limit_number = int(limit_value.this)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "LIMIT must be a positive integer."
            ) from exc

        if not 1 <= limit_number <= MAX_ROWS:
            raise ValueError("LIMIT must be between 1 and 100.")

    return tree.sql(dialect="duckdb")
