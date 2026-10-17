
from app.services.llm_service import generate_sql
from app.services.query_service import execute_readonly_query

schema = """
Table products:
- id: integer
- product_name: string
- category: string
- unit_price: decimal

Table sales:
- id: integer
- product_id: integer
- quantity: integer
- sale_date: date

Relationship:
sales.product_id references products.id
"""

question = "Which products have the highest total sales revenue?"

try:
    generated_sql = generate_sql(question, schema)
    result = execute_readonly_query(generated_sql)

    print("\nGenerated SQL:")
    print(result["sql"])

    print("\nQuery results:")
    for row in result["rows"]:
        print(row)

    print("\nTotal rows:", result["row_count"])

except Exception as exc:
    print(f"\nTest failed: {type(exc).__name__}: {exc}")
