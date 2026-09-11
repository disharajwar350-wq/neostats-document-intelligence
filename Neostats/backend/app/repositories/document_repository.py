import json
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db_connection
from backend.app.core.logging import logger

class DocumentRepository:
    """
    Persistence layer using SQLite to save and query document extraction records.
    Supports GET by document name and GET all for dashboard view (Section 5.1 & 6).
    """

    @staticmethod
    def save_document(document_name: str, document_type: str, processing_status: str, result_dict: Dict[str, Any]) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        json_str = json.dumps(result_dict)

        try:
            cursor.execute("""
                INSERT INTO processed_documents (document_name, document_type, processing_status, result_json, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(document_name) DO UPDATE SET
                    document_type = excluded.document_type,
                    processing_status = excluded.processing_status,
                    result_json = excluded.result_json,
                    updated_at = CURRENT_TIMESTAMP
            """, (document_name, document_type, processing_status, json_str))
            conn.commit()
            logger.info(f"Successfully stored/updated record for '{document_name}' in SQLite")
            return True
        except Exception as e:
            logger.error(f"Error saving document '{document_name}' to DB: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_by_name(document_name: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT result_json FROM processed_documents WHERE document_name = ?", (document_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row["result_json"])
        return None

    @staticmethod
    def list_all() -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, document_name, document_type, processing_status, created_at, updated_at, result_json FROM processed_documents ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            res_dict = json.loads(row["result_json"]) if row["result_json"] else {}
            results.append({
                "id": row["id"],
                "document_name": row["document_name"],
                "document_type": row["document_type"],
                "processing_status": row["processing_status"],
                "overall_confidence": res_dict.get("overall_confidence"),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        return results
