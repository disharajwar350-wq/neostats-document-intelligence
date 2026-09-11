import json
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "documents.sqlite3"


def initialize() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_name TEXT PRIMARY KEY,
                document_type TEXT NOT NULL,
                status TEXT NOT NULL,
                processed_at TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
        """)


def save(result: dict) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """INSERT OR REPLACE INTO documents
               (document_name, document_type, status, processed_at, result_json)
               VALUES (?, ?, ?, ?, ?)""",
            (result["document_name"], result["document_type"], result["processing_status"],
             result["processing_metadata"]["processed_at"], json.dumps(result)),
        )


def get(document_name: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT result_json FROM documents WHERE document_name = ?", (document_name,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def list_documents() -> list[dict]:
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT result_json FROM documents ORDER BY processed_at DESC"
        ).fetchall()
    return [json.loads(row[0]) for row in rows]

