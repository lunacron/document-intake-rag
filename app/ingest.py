import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from .chunking import HEADING_MARK, chunk_text, last_heading
from .db import connect
from .embed import embed
from .pii import redact
from .storage import storage


def _pdf_page_text(page) -> str:
    """Extract page text, marking lines set in a noticeably larger font as headings."""
    fragments: list[tuple[str, float]] = []

    def visit(text, cm, tm, font_dict, font_size):
        if text.strip():
            fragments.append((text.strip(), font_size))

    page.extract_text(visitor_text=visit)
    if not fragments:
        return ""
    weight: Counter = Counter()  # body size = the font size carrying the most characters
    for text, size in fragments:
        weight[round(size, 1)] += len(text)
    body_size = weight.most_common(1)[0][0]
    headings = {t for t, s in fragments if s >= body_size + 1.5}

    lines = (page.extract_text() or "").splitlines()
    return "\n".join(f"{HEADING_MARK}{ln}" if ln.strip() in headings else ln for ln in lines)


def extract_pages(filename: str, data: bytes) -> list[str]:
    if filename.lower().endswith(".pdf"):
        return [_pdf_page_text(p) for p in PdfReader(io.BytesIO(data)).pages]
    return [data.decode("utf-8", errors="replace")]


def default_label(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").replace("-", " ").title()


def ingest_document(filename: str, data: bytes, access_level: str = "restricted", label: str = "",
                    subject_id: str = "", subject_name: str = "") -> dict:
    """`label` says what the document is and whose it is (e.g. "Enrollment form - Sarah Wilson").

    It is written at the top of every chunk, because a chunk like "Known allergies: Peanuts" does not
    say which student it is about, and the search could not tell two students' forms apart.
    """
    label = label.strip() or default_label(filename)
    sha = hashlib.sha256(data).hexdigest()

    with connect() as conn:
        existing = conn.execute("SELECT id FROM documents WHERE sha256 = %s", (sha,)).fetchone()
        if existing:
            return {"doc_id": existing[0], "duplicate": True}

        storage.save_file(f"{sha[:12]}_{filename}", data)

        pii_counts: Counter = Counter()
        rows: list[tuple[int, int, str]] = []  # (page, idx, text)
        idx = 0
        carried_heading = ""
        for page_no, page_text in enumerate(extract_pages(filename, data), start=1):
            clean, counts = redact(page_text)
            pii_counts.update(counts)
            for chunk in chunk_text(clean, max_chars=1500 - len(label) - 3, default_heading=carried_heading):
                rows.append((page_no, idx, f"[{label}]\n{chunk}"))
                idx += 1
            carried_heading = last_heading(clean) or carried_heading

        if not rows:
            return {"doc_id": None, "error": "no extractable text (scanned PDF? OCR not added yet)"}

        vectors = embed([r[2] for r in rows])

        doc_id = conn.execute(
            "INSERT INTO documents (filename, sha256, pii_found, access_level, label, subject_id, subject_name) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (filename, sha, json.dumps(dict(pii_counts)), access_level, label,
             subject_id or None, subject_name or None),
        ).fetchone()[0]
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (doc_id, page, idx, text, embedding) VALUES (%s, %s, %s, %s, %s)",
                [(doc_id, p, i, t, v) for (p, i, t), v in zip(rows, vectors)],
            )
        return {"doc_id": doc_id, "chunks": len(rows), "pii_redacted": dict(pii_counts)}
