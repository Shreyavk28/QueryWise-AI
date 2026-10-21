
import logging
import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.database import check_database
from app.services.llm_service import (
    generate_sql,
    generate_uploaded_sql,
)
from app.services.query_service import execute_readonly_query
from app.services.upload_service import load_uploaded_dataframe
from app.services.upload_query_service import execute_uploaded_query
from app.services.upload_store import (
    store_dataset,
    get_dataset,
    delete_dataset,
    list_datasets,
)


# Configure application logging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("querywise")


app = FastAPI(
    title="QueryWise AI",
    description=(
        "Ask questions about business data in natural language "
        "and upload CSV or Excel datasets."
    ),
    version="1.0.0",
)


# CORS configuration:
# Keep local development enabled and allow the deployed frontend
# through the FRONTEND_URL environment variable in Render.
frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

allowed_origins = ["http://localhost:5173"]

if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


SCHEMA = """
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


class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=500,
        description="A business question about the available data.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 3:
            raise ValueError(
                "Please enter a question with at least 3 characters."
            )

        if not any(character.isalpha() for character in value):
            raise ValueError("Please enter a meaningful question.")

        return value


class UploadedAskRequest(AskRequest):
    dataset_id: str = Field(
        min_length=32,
        max_length=32,
        pattern=r"^[a-fA-F0-9]{32}$",
        description="ID returned by the upload endpoint.",
    )


@app.get("/api/health")
def health_check():
    """Check whether the API is running."""
    return {
        "status": "success",
        "message": "QueryWise AI backend is running",
    }


@app.get("/api/db-health")
def database_health_check():
    """Check database connectivity without exposing internal errors."""
    try:
        result = check_database()

        return {
            "status": "success",
            "database": "connected",
            "test_result": result,
        }

    except Exception as exc:
        logger.error(
            "Database health check failed: %s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=503,
            detail="Database is currently unavailable.",
        ) from exc


@app.get("/api/datasets")
def get_saved_datasets():
    """List uploaded datasets saved on the server."""
    try:
        return {
            "status": "success",
            "datasets": list_datasets(),
        }
    except Exception as exc:
        logger.error(
            "Unable to list saved datasets: %s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to load saved datasets.",
        ) from exc


@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Save a validated CSV or XLSX dataset."""

    try:
        filename = file.filename or ""

        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Please select a file to upload.",
            )

        content = await file.read(MAX_UPLOAD_SIZE + 1)

        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size must not exceed 5 MB.",
            )

        dataframe = load_uploaded_dataframe(
            filename=filename,
            file_content=content,
        )

        dataset_id = store_dataset(
            filename,
            dataframe,
            content,
        )

        preview_dataframe = dataframe.head(10).astype(object).where(
            dataframe.head(10).notna(),
            None,
        )

        return {
            "status": "success",
            "dataset_id": dataset_id,
            "filename": filename,
            "columns": [
                {
                    "name": str(column),
                    "dtype": str(dtype),
                }
                for column, dtype in zip(
                    dataframe.columns,
                    dataframe.dtypes,
                )
            ],
            "rows": preview_dataframe.to_dict(orient="records"),
            "row_count": len(dataframe),
            "column_count": len(dataframe.columns),
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except OSError as exc:
        logger.error(
            "Dataset storage failed: %s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail="The uploaded dataset could not be saved.",
        ) from exc

    finally:
        await file.close()


@app.delete("/api/upload/{dataset_id}")
def delete_uploaded_dataset(dataset_id: str):
    """Permanently delete an uploaded dataset and its metadata."""

    try:
        delete_dataset(dataset_id)

        return {
            "status": "success",
            "message": "Dataset deleted successfully.",
        }

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found. It may already have been deleted.",
        ) from exc


@app.post("/api/ask")
def ask_question(request: AskRequest):
    """Generate and execute a read-only query against MySQL."""

    try:
        question = request.question

        logger.info("Processing a QueryWise question.")

        sql = generate_sql(question, SCHEMA)
        result = execute_readonly_query(sql)

        return {
            "status": "success",
            "question": question,
            "sql": result["sql"],
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
        }

    except ValueError as exc:
        logger.warning(
            "Query rejected: %s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        error_code = getattr(exc, "code", None)
        status_code = getattr(exc, "status_code", None)
        error_message = str(exc).lower()

        is_rate_limit = (
            error_code == 429
            or status_code == 429
            or "429 too many requests" in error_message
            or "429 resource_exhausted" in error_message
        )

        if is_rate_limit:
            daily_quota_markers = (
                "requests per day",
                "per-day quota",
                "daily quota",
                "quota exceeded",
            )

            daily_quota_exhausted = any(
                marker in error_message
                for marker in daily_quota_markers
            )

            if daily_quota_exhausted:
                detail = (
                    "Gemini daily quota may be exhausted. "
                    "Check your Google AI Studio usage and try again "
                    "after the quota resets."
                )
            else:
                detail = (
                    "Gemini is temporarily rate-limiting requests. "
                    "Please wait before trying again."
                )

            logger.warning("Gemini rate limit or quota reached.")

            raise HTTPException(
                status_code=429,
                detail=detail,
            ) from exc

        logger.error(
            "QueryWise request failed: %s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to answer the question right now. "
                "Please try again later."
            ),
        ) from exc


@app.post("/api/upload/ask")
def ask_uploaded_dataset(request: UploadedAskRequest):
    """Answer a question using a previously saved uploaded dataset."""

    try:
        dataset = get_dataset(request.dataset_id)
        dataframe = dataset["dataframe"]

        sql = generate_uploaded_sql(
            request.question,
            [str(column) for column in dataframe.columns],
        )

        result = execute_uploaded_query(dataframe, sql)

        return {
            "status": "success",
            "dataset_id": request.dataset_id,
            "filename": dataset["filename"],
            "question": request.question,
            **result,
        }

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Dataset not found. Please upload the file again "
                "if it was deleted or is unavailable."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        error_message = str(exc).lower()
        error_code = getattr(exc, "code", None)
        status_code = getattr(exc, "status_code", None)

        if (
            error_code == 429
            or status_code == 429
            or "429 too many requests" in error_message
            or "429 resource_exhausted" in error_message
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini is rate-limiting requests. "
                    "Please try again later."
                ),
            ) from exc

        logger.error(
            "Uploaded dataset query failed: %s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to answer this uploaded-dataset question "
                "right now."
            ),
        ) from exc
