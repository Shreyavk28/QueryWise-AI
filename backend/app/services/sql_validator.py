
import sqlglot
from sqlglot import exp


ALLOWED_TABLES = {"products", "sales"}

ALLOWED_COLUMNS = {
    "products": {"id", "product_name", "category", "unit_price"},
    "sales": {"id", "product_id", "quantity", "sale_date"},
}

MAX_ROWS = 100

BLOCKED_FUNCTIONS = {
    "SLEEP",
    "BENCHMARK",
    "LOAD_FILE",
}


class SQLValidationError(ValueError):
    """Raised when a SQL query is unsafe or invalid."""


def validate_sql(sql: str) -> str:
    if not sql or not sql.strip():
        raise SQLValidationError("SQL query cannot be empty.")

    try:
        statements = sqlglot.parse(sql, read="mysql")
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError("Invalid SQL syntax.") from exc

    if len(statements) != 1 or statements[0] is None:
        raise SQLValidationError("Only one SQL statement is allowed.")

    tree = statements[0]

    if not isinstance(tree, exp.Select):
        raise SQLValidationError("Only SELECT queries are allowed.")

    # Reject CTEs until their table and column scopes are handled explicitly.
    if tree.find(exp.With):
        raise SQLValidationError("CTEs are not currently supported.")

    # Validate all table references, including subqueries and UNION branches.
    for table in tree.find_all(exp.Table):
        if table.db or table.catalog:
            raise SQLValidationError(
                "Database-qualified table names are not allowed."
            )

        table_name = table.name.lower()

        if table_name not in ALLOWED_TABLES:
            raise SQLValidationError(
                f"Table '{table.name}' is not allowed."
            )

    # Reject potentially dangerous functions.
    for node in tree.walk():
        if isinstance(node, exp.Anonymous):
            function_name = node.name.upper()
            if function_name in BLOCKED_FUNCTIONS:
                raise SQLValidationError(
                    f"Function '{function_name}' is not allowed."
                )

        elif isinstance(node, exp.Func):
            function_name = node.sql_name().upper()
            if function_name in BLOCKED_FUNCTIONS:
                raise SQLValidationError(
                    f"Function '{function_name}' is not allowed."
                )

    def validate_select_scope(select: exp.Select) -> None:
        """Validate columns and aliases within one SELECT scope."""
        table_aliases = {}
        referenced_tables = set()

        def register_table(table: exp.Table) -> None:
            # Ignore tables that belong to a nested SELECT.
            if table.find_ancestor(exp.Select) is not select:
                return

            table_name = table.name.lower()
            alias = table.alias.lower() if table.alias else table_name

            table_aliases[alias] = table_name
            table_aliases[table_name] = table_name
            referenced_tables.add(table_name)

        # Register tables in FROM and JOIN clauses.
        from_clause = select.args.get("from_")
        if from_clause:
            for table in from_clause.find_all(exp.Table):
                register_table(table)

        for join in select.args.get("joins") or []:
            for table in join.find_all(exp.Table):
                register_table(table)

        # Collect aliases explicitly defined in the SELECT list.
        select_aliases = {
            projection.alias.lower()
            for projection in select.expressions
            if isinstance(projection, exp.Alias)
        }

        # Validate qualified and unqualified column references.
        for column in select.find_all(exp.Column):
            # Nested SELECT columns are validated in their own scope.
            if column.find_ancestor(exp.Select) is not select:
                continue

            column_name = column.name.lower()

            # SELECT aliases are allowed in ORDER BY, for example:
            # SUM(s.quantity * p.unit_price) AS total_revenue
            # ORDER BY total_revenue DESC
            if (
                not column.table
                and column_name in select_aliases
                and column.find_ancestor(exp.Order) is not None
            ):
                continue

            if column.table:
                alias_or_table = column.table.lower()
                table_name = table_aliases.get(alias_or_table)

                if table_name is None:
                    raise SQLValidationError(
                        f"Unknown table alias or name: "
                        f"'{alias_or_table}'."
                    )

                if column_name not in ALLOWED_COLUMNS[table_name]:
                    raise SQLValidationError(
                        f"Column '{column_name}' is not allowed "
                        f"for table '{table_name}'."
                    )

            else:
                # Allow an unqualified column only when it exists in
                # the current query's referenced tables.
                matching_tables = [
                    table_name
                    for table_name in referenced_tables
                    if column_name in ALLOWED_COLUMNS[table_name]
                ]

                if not matching_tables:
                    raise SQLValidationError(
                        f"Column '{column_name}' is not allowed."
                    )

                # In a multi-table query, reject ambiguous unqualified
                # columns instead of guessing which table they belong to.
                if (
                    len(referenced_tables) > 1
                    and len(matching_tables) != 1
                ):
                    raise SQLValidationError(
                        f"Unqualified column '{column_name}' is "
                        "ambiguous or not allowed across tables."
                    )

        # Validate nested SELECT queries independently.
        for nested_select in select.find_all(exp.Select):
            if nested_select is select:
                continue

            if nested_select.find_ancestor(exp.Select) is select:
                validate_select_scope(nested_select)

    # Validate each top-level SELECT, including UNION branches.
    for select in tree.find_all(exp.Select):
        if select.find_ancestor(exp.Select) is None:
            validate_select_scope(select)

    # Apply or validate the maximum row limit on the outer query.
    if tree.args.get("limit") is None:
        tree = tree.limit(MAX_ROWS)
    else:
        limit_expression = tree.args["limit"].expression

        if not isinstance(limit_expression, exp.Literal):
            raise SQLValidationError(
                "LIMIT must be a numeric literal."
            )

        if not limit_expression.is_int:
            raise SQLValidationError("LIMIT must be an integer.")

        requested_limit = int(limit_expression.this)

        if requested_limit < 1 or requested_limit > MAX_ROWS:
            raise SQLValidationError(
                f"LIMIT must be between 1 and {MAX_ROWS}."
            )

    return tree.sql(dialect="mysql")
