"""Mock legacy system. A table stands in for the real one (an API, SFTP drop or RPA on AWS).

Idempotent: the application ID is the key, so sending the same record twice updates it instead of
creating a duplicate. A real adapter would also add retries and a dead-letter queue.
"""
from psycopg.types.json import Jsonb

from .db import connect


def send_student(record: dict) -> str:
    """Create or update the student record. Returns "created" or "updated"."""
    key = record["application_id"]
    with connect() as conn:
        existed = conn.execute(
            "SELECT 1 FROM legacy_students WHERE application_id = %s", (key,)).fetchone()
        conn.execute(
            "INSERT INTO legacy_students (application_id, data) VALUES (%s, %s) "
            "ON CONFLICT (application_id) DO UPDATE SET data = EXCLUDED.data, updated_at = now()",
            (key, Jsonb(record)))
    return "updated" if existed else "created"


def list_students() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT application_id, data, created_at, updated_at FROM legacy_students "
            "ORDER BY application_id").fetchall()
    return [{"application_id": r[0], "data": r[1], "created_at": r[2], "updated_at": r[3]} for r in rows]
