import sqlite3
import json
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging import logger

def get_db_connection():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_name TEXT UNIQUE NOT NULL,
            document_type TEXT NOT NULL,
            processing_status TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {settings.DB_PATH}")

if __name__ == "__main__":
    init_db()
