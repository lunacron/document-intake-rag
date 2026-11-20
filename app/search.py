"""Retrieval: find the chunks closest to a question, restricted to the right people's documents.

Similarity search barely notices a name ("Marcus" vs "Sarah"), so the person is resolved first and
the search is then limited to their documents. Documents with no subject (e.g. the handbook) are
always searchable.
"""
import re

from .auth import allowed_levels
from .db import connect
from .embed import embed_query


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]+", text.lower()) if len(t) >= 3}


def match_subjects(question: str, subjects: list[tuple[str, str]]):
    """Work out which known people a question is about.

    `subjects` is a list of (subject_id, subject_name). A person matches when any part of their
    name appears in the question. Returns (matched_ids, ambiguous_groups) where each ambiguous group
    is a list of (id, name) the question cannot tell apart, such as two people called "Sarah".
    """
    q = _tokens(question)
    names = dict(subjects)
    hits = {sid: _tokens(name) & q for sid, name in names.items()}
    hits = {sid: toks for sid, toks in hits.items() if toks}
    # "Sarah Elizabeth" beats "Sarah" when another person only matches the first name
    hits = {sid: toks for sid, toks in hits.items()
            if not any(toks < other for o, other in hits.items() if o != sid)}
    groups: dict[frozenset, list[str]] = {}
    for sid, toks in hits.items():
        groups.setdefault(frozenset(toks), []).append(sid)
    matched = [ids[0] for ids in groups.values() if len(ids) == 1]
    ambiguous = [[(sid, names[sid]) for sid in ids] for ids in groups.values() if len(ids) > 1]
    return matched, ambiguous


def search(question: str, role: str, k: int = 8) -> dict:
    levels = allowed_levels(role)
    with connect() as conn:
        # Only people whose documents this role may read can be recognised in a question.
        subjects = conn.execute(
            "SELECT DISTINCT subject_id, subject_name FROM documents "
            "WHERE access_level = ANY(%s) AND subject_id IS NOT NULL", (levels,)).fetchall()
        matched, ambiguous = match_subjects(question, subjects)
        if ambiguous:
            return {"needs_clarification": [
                [{"subject_id": sid, "name": name} for sid, name in group] for group in ambiguous],
                "subjects_matched": [], "results": []}

        vector = embed_query(question)
        sql = ("SELECT d.filename, d.label, d.subject_id, c.page, c.idx, c.text, "
               "1 - (c.embedding <=> %s::vector) AS similarity "
               "FROM chunks c JOIN documents d ON d.id = c.doc_id "
               "WHERE d.access_level = ANY(%s)")
        params: list = [vector, levels]
        if matched:
            sql += " AND (d.subject_id IS NULL OR d.subject_id = ANY(%s))"
            params.append(matched)
        sql += " ORDER BY c.embedding <=> %s::vector LIMIT %s"
        params += [vector, k]
        rows = conn.execute(sql, params).fetchall()

    return {"subjects_matched": matched, "results": [
        {"filename": r[0], "label": r[1], "subject_id": r[2], "page": r[3], "chunk": r[4],
         "similarity": round(float(r[6]), 3), "text": r[5]} for r in rows]}
