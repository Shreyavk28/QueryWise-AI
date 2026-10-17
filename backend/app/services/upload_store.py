
import json
import threading
from pathlib import Path
from uuid import uuid4

from app.services.upload_service import load_uploaded_dataframe

# Persistent storage directory inside the backend folder.
STORAGE_DIR = Path(__file__).resolve().parents[2] / "data" / "uploaded_datasets"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

MAX_STORED_DATASETS = 20
_lock = threading.Lock()


def store_dataset(filename: str, dataframe, file_content: bytes) -> str:
    """Persist an uploaded file and its metadata until explicitly deleted."""
    suffix = Path(filename).suffix.lower()

    if suffix not in {".csv", ".xlsx"}:
        raise ValueError("Only CSV and XLSX files are supported.")

    dataset_id = uuid4().hex
    data_path = STORAGE_DIR / f"{dataset_id}{suffix}"
    metadata_path = STORAGE_DIR / f"{dataset_id}.json"

    with _lock:
        existing = list(STORAGE_DIR.glob("*.json"))
        if len(existing) >= MAX_STORED_DATASETS:
            raise RuntimeError(
                "The dataset storage limit has been reached. "
                "Delete an existing dataset before uploading another."
            )

        try:
            data_path.write_bytes(file_content)

            metadata_path.write_text(
                json.dumps(
                    {
                        "dataset_id": dataset_id,
                        "filename": Path(filename).name,
                        "stored_filename": data_path.name,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            data_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            raise

    return dataset_id


def get_dataset(dataset_id: str) -> dict:
    """Load a saved dataset from disk."""
    if not dataset_id or len(dataset_id) != 32:
        raise KeyError("Dataset not found.")

    metadata_path = STORAGE_DIR / f"{dataset_id}.json"

    with _lock:
        if not metadata_path.is_file():
            raise KeyError("Dataset not found.")

        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("dataset_id") != dataset_id:
                raise KeyError("Dataset not found.")

            stored_filename = metadata.get("stored_filename", "")
            expected_prefix = f"{dataset_id}."

            if (
                not stored_filename.startswith(expected_prefix)
                or Path(stored_filename).name != stored_filename
                or Path(stored_filename).suffix.lower() not in {".csv", ".xlsx"}
            ):
                raise KeyError("Dataset not found.")

            data_path = STORAGE_DIR / stored_filename
            if not data_path.is_file():
                raise KeyError("Dataset not found.")

            file_content = data_path.read_bytes()
            original_filename = metadata["filename"]

        except (OSError, ValueError, TypeError) as exc:
            raise KeyError("Saved dataset could not be loaded.") from exc

    try:
        dataframe = load_uploaded_dataframe(original_filename, file_content)
    except ValueError as exc:
        raise KeyError("Saved dataset could not be loaded.") from exc

    return {
        "filename": original_filename,
        "dataframe": dataframe,
    }


def delete_dataset(dataset_id: str) -> None:
    """Permanently delete a saved dataset and its metadata."""
    if not dataset_id or len(dataset_id) != 32:
        raise KeyError("Dataset not found.")

    metadata_path = STORAGE_DIR / f"{dataset_id}.json"

    with _lock:
        if not metadata_path.is_file():
            raise KeyError("Dataset not found.")

        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("dataset_id") != dataset_id:
                raise KeyError("Dataset not found.")

            stored_filename = metadata.get("stored_filename", "")
            if (
                not stored_filename.startswith(f"{dataset_id}.")
                or Path(stored_filename).name != stored_filename
                or Path(stored_filename).suffix.lower() not in {".csv", ".xlsx"}
            ):
                raise KeyError("Dataset not found.")

            data_path = STORAGE_DIR / stored_filename
            data_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)

        except (OSError, ValueError, TypeError) as exc:
            raise KeyError("Dataset could not be deleted.") from exc


def list_datasets() -> list[dict]:
    """Return saved datasets with metadata and a small preview."""
    datasets = []

    metadata_files = sorted(
        STORAGE_DIR.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for metadata_path in metadata_files:
        dataset_id = metadata_path.stem

        try:
            saved = get_dataset(dataset_id)
            dataframe = saved["dataframe"]

            preview_df = dataframe.head(10).astype(object).where(
                dataframe.head(10).notna(),
                None,
            )

            datasets.append(
                {
                    "dataset_id": dataset_id,
                    "filename": saved["filename"],
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
                    "rows": preview_df.to_dict(orient="records"),
                    "row_count": len(dataframe),
                    "column_count": len(dataframe.columns),
                }
            )
        except (KeyError, OSError, ValueError):
            # Skip datasets that cannot currently be loaded.
            continue

    return datasets
