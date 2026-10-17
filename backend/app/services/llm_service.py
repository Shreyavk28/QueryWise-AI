
import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to backend/.env."
    )

client = genai.Client(api_key=api_key)

RETRY_DELAY_SECONDS = 5

QUOTA_EXHAUSTED_MARKERS = (
    "daily quota",
    "requests per day",
    "per-day quota",
    "quota exceeded",
    "billing",
)


def is_temporary_rate_limit(exc: Exception) -> bool:
    """Identify rate-limit errors that may be temporary."""
    code = getattr(exc, "code", None)
    status = getattr(exc, "status_code", None)
    message = str(exc).lower()

    is_rate_limit = (
        code == 429
        or status == 429
        or "429 too many requests" in message
        or "429 resource_exhausted" in message
    )

    if not is_rate_limit:
        return False

    if any(marker in message for marker in QUOTA_EXHAUSTED_MARKERS):
        return False

    return True


def generate_sql(question: str, schema: str) -> str:
    """Generate SQL, retrying once for a temporary rate limit."""

    prompt = f"""
You are QueryWise AI, a MySQL query-generation assistant.

Generate exactly one MySQL SELECT query answering the user's question.

Rules:
- Use only tables and columns listed in the schema below.
- Only generate SELECT queries.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
  TRUNCATE, or other data-changing statements.
- Do not use multiple statements.
- Do not include Markdown fences or explanations.
- Limit results to at most 100 rows.
- If the question cannot be answered from the schema, say
  CANNOT_ANSWER.

Database schema:
{schema}

User question:
{question}

SQL query:
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
    except Exception as exc:
        if not is_temporary_rate_limit(exc):
            raise

        # Make at most one retry for a potentially temporary limit.
        time.sleep(RETRY_DELAY_SECONDS)

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

    sql = (response.text or "").strip()

    # Remove Markdown fences if the model includes them.
    if sql.startswith("```"):
        lines = sql.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        sql = "\n".join(lines).strip()

    if sql == "CANNOT_ANSWER":
        raise ValueError(
            "This question cannot be answered using the available database schema."
        )

    return sql



def generate_uploaded_sql(question: str, columns: list[str]) -> str:
    """Generate DuckDB SQL for a user-uploaded dataset."""

    if not question or not question.strip():
        raise ValueError("Please enter a question.")

    if not columns:
        raise ValueError("The uploaded dataset has no columns.")

    schema = "\n".join(f"- {column}" for column in columns)

    prompt = f"""
You are QueryWise AI, a data analysis assistant for uploaded datasets.

Generate exactly one DuckDB SELECT query answering the user's question.

Rules:
- The only available table is uploaded_data.
- Use only the column names listed in the schema.
- Quote column identifiers with double quotes when necessary.
- Only generate SELECT queries.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
  TRUNCATE, COPY, ATTACH, DETACH, or other data-changing statements.
- Never read external files or access external resources.
- Do not use multiple statements.
- Do not include Markdown fences or explanations.
- Limit results to at most 100 rows.
- If the question cannot be answered from the schema, return exactly:
  CANNOT_ANSWER

Available columns:
{schema}

User question:
{question}

SQL query:
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
    except Exception as exc:
        if not is_temporary_rate_limit(exc):
            raise

        time.sleep(RETRY_DELAY_SECONDS)

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

    sql = (response.text or "").strip()

    if sql.startswith("```"):
        lines = sql.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        sql = "\n".join(lines).strip()

    if sql == "CANNOT_ANSWER":
        raise ValueError(
            "This question cannot be answered using the uploaded dataset."
        )

    return sql
