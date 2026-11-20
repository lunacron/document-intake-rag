from typing import Literal

from pydantic import BaseModel, Field
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile

from .auth import allowed_levels, current_role, require_registrar
from .db import connect
from .extract import approve, extract_document, get_extraction, list_extractions, reject
from .ingest import ingest_document
from .legacy import list_students
from .query import answer
from .search import search

app = FastAPI(title="Document Intake RAG")


@app.get("/health")
def health():
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"ok": True}


@app.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    access_level: Literal["public", "restricted"] = Form("restricted"),
    label: str = Form(""),
    subject_id: str = Form(""),
    subject_name: str = Form(""),
    role: str = Depends(current_role),
):
    if role != "registrar":
        raise HTTPException(status_code=403, detail="only registrar can ingest")
    if bool(subject_id) != bool(subject_name):
        raise HTTPException(status_code=400, detail="give both subject_id and subject_name, or neither")
    return ingest_document(file.filename, await file.read(), access_level, label, subject_id, subject_name)


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.post("/query")
def query(body: QueryRequest, role: str = Depends(current_role)):
    """Answer a question from the documents this role may read, with citations."""
    return answer(body.question, role)


@app.post("/extract/{doc_id}")
def extract(doc_id: int, _: str = Depends(require_registrar)):
    """Have Claude pull the enrollment-form fields out of one stored document into the review queue."""
    return extract_document(doc_id)


@app.get("/extractions")
def extractions(status: str | None = None, _: str = Depends(require_registrar)):
    """The review queue. Filter with ?status=pending_review (or sent, rejected, failed)."""
    return list_extractions(status)


@app.get("/extractions/{extraction_id}")
def extraction(extraction_id: int, _: str = Depends(require_registrar)):
    return get_extraction(extraction_id)


class Approval(BaseModel):
    corrections: dict = Field(default_factory=dict, description="Fields to overwrite before approving")


@app.post("/extractions/{extraction_id}/approve")
def approve_extraction(extraction_id: int, body: Approval = Approval(), role: str = Depends(require_registrar)):
    """Approve (optionally with corrections), then write the record to the legacy system."""
    return approve(extraction_id, body.corrections, role)


@app.post("/extractions/{extraction_id}/reject")
def reject_extraction(extraction_id: int, role: str = Depends(require_registrar)):
    return reject(extraction_id, role)


@app.get("/legacy/students")
def legacy_students(_: str = Depends(require_registrar)):
    """What the mock legacy system holds."""
    return list_students()


@app.get("/search")
def search_chunks(q: str, k: int = Query(8, ge=1, le=20), role: str = Depends(current_role)):
    """Closest chunks to a question, limited to what the role may read and to the person named."""
    return search(q, role, k)


@app.get("/documents")
def documents(role: str = Depends(current_role)):
    with connect() as conn:
        rows = conn.execute(
            "SELECT d.id, d.filename, d.status, d.access_level, d.pii_found, count(c.id), d.label "
            "FROM documents d LEFT JOIN chunks c ON c.doc_id = d.id "
            "WHERE d.access_level = ANY(%s) "
            "GROUP BY d.id ORDER BY d.id",
            (allowed_levels(role),),
        ).fetchall()
    return [
        {"id": r[0], "filename": r[1], "label": r[6], "status": r[2], "access_level": r[3],
         "pii_found": r[4], "chunks": r[5]}
        for r in rows
    ]
