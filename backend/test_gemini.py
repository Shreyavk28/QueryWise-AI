
from app.services.llm_service import generate_sql

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
    sql = generate_sql(question, schema)
    print("\nQuestion:", question)
    print("\nGenerated SQL:\n", sql)
except Exception as exc:
    print(f"\nGemini request failed: {type(exc).__name__}: {exc}")
