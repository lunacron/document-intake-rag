"""Evaluation with a separate score for each part, so a failure says where to look.

    docker compose exec api python -m evals.run            # all three
    docker compose exec api python -m evals.run search     # free: no Claude call
    docker compose exec api python -m evals.run query      # search + Claude answers, a few cents
    docker compose exec api python -m evals.run extract    # Claude extraction, a few cents

SEARCH  - is the right chunk in the top 8? (embedding model, chunking, filters)
QUERY   - is the written answer right? A failure is labelled "retrieval" (the right chunk never
          reached Claude) or "generation" (it did, and the answer is still wrong).
EXTRACT - do the extracted fields match the expected record? (nothing is stored or sent anywhere)
"""
import json
import re
import sys
from pathlib import Path

from fastapi import HTTPException

from app.config import settings
from app.db import connect
from app.extract import _source_text, extract_from_text
from app.query import answer
from app.search import search

CASES = json.loads((Path(__file__).parent / "cases.json").read_text())
NOT_FOUND = ("could not find", "couldn't find", "cannot find", "can't find", "not found")


def _short(text: str, n: int = 220) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + "..."


# ---------- search ----------

def check_search(case: dict, found: dict) -> tuple[bool | None, str]:
    """(passed, detail); passed is None when the case has no retrieval expectation."""
    if "chunk_has" not in case and "forbid_file" not in case:
        return None, ""
    results = found.get("results", [])
    problems, detail = [], ""
    if "chunk_has" in case:
        rank = next((i for i, r in enumerate(results, 1)
                     if r["filename"] == case["file"] and case["chunk_has"].lower() in r["text"].lower()), None)
        if rank is None:
            problems.append(f"no retrieved chunk from {case['file']} contains {case['chunk_has']!r}")
        else:
            detail = f"rank {rank} of {len(results)}"
    if "forbid_file" in case and any(r["filename"] == case["forbid_file"] for r in results):
        problems.append(f"retrieved {case['forbid_file']}, which this question must not reach")
    return not problems, "; ".join(problems) or detail


# ---------- query ----------

def check_query(case: dict, ans: dict) -> list[str]:
    text = ans.get("answer") or ""
    low = text.lower()
    problems = []
    if case.get("not_found") and not any(p in low for p in NOT_FOUND):
        problems.append("did not say it could not find the answer")
    problems += [f"answer lacks {s!r}" for s in case.get("answer_has", []) if s.lower() not in low]
    problems += [f"answer contains {s!r}" for s in case.get("answer_lacks", []) if s.lower() in low]
    if case.get("file") and not case.get("not_found"):
        if case["file"] not in {s["filename"] for s in ans.get("sources", [])}:
            problems.append(f"does not cite {case['file']}")
    return problems


def run_questions(with_claude: bool) -> float:
    cases = CASES["questions"]
    search_rows, query_rows, cost = [], [], 0.0
    for c in cases:
        found = search(c["q"], c.get("role", "registrar"), settings.query_top_k)
        s_ok, s_detail = check_search(c, found)
        if s_ok is not None:
            search_rows.append((c["id"], s_ok, s_detail))
        if not with_claude:
            continue
        try:
            ans = answer(c["q"], c.get("role", "registrar"))
        except HTTPException as e:
            print(f"\nQUERY stopped at {c['id']}: HTTP {e.status_code} {e.detail}")
            break
        cost += ans.get("usage", {}).get("estimated_cost_usd", 0.0)
        problems = check_query(c, ans)
        stage = ""
        if problems:
            stage = "retrieval" if s_ok is False else "generation"
        query_rows.append((c["id"], not problems, stage, problems, ans.get("answer")))

    passed = sum(ok for _, ok, _ in search_rows)
    print(f"\nSEARCH   {passed}/{len(search_rows)} passed   (free: embeddings and database only)")
    for cid, ok, detail in search_rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {cid:<24} {detail}")

    if with_claude:
        passed = sum(ok for _, ok, *_ in query_rows)
        print(f"\nQUERY    {passed}/{len(query_rows)} passed   (cost ${cost:.4f})")
        for cid, ok, stage, problems, text in query_rows:
            if ok:
                print(f"  PASS  {cid}")
            else:
                print(f"  FAIL  {cid:<24} [{stage}] {'; '.join(problems)}")
                print(f"        answer: {_short(text)}")
        by_stage = {s: sum(1 for r in query_rows if r[2] == s) for s in ("retrieval", "generation")}
        if any(by_stage.values()):
            print(f"  failures by stage: {by_stage['retrieval']} retrieval, {by_stage['generation']} generation")
    return cost


# ---------- extract ----------

def canon(v):
    """Compare values loosely on punctuation and case, strictly on content."""
    if isinstance(v, str):
        return re.sub(r"[^a-z0-9]", "", v.lower())
    if isinstance(v, list):
        return sorted((canon(x) for x in v), key=repr)
    if isinstance(v, dict):
        return dict(sorted((k, canon(x)) for k, x in v.items() if x is not None))
    return v


def run_extractions() -> float:
    cost, form_rows = 0.0, []
    for c in CASES["extractions"]:
        with connect() as conn:
            doc = conn.execute("SELECT filename, sha256 FROM documents WHERE filename = %s "
                               "ORDER BY id DESC LIMIT 1", (c["file"],)).fetchone()
        if not doc:
            form_rows.append((c["id"], 0, 0, [f"{c['file']} is not ingested"], 0))
            continue
        result = extract_from_text(_source_text(*doc))
        cost += result["usage"]["estimated_cost_usd"]
        misses = []
        if result["status"] != c["expect_status"]:
            misses.append(f"status: expected {c['expect_status']}, got {result['status']}")
        for field, want in c["expected"].items():
            got = result["data"].get(field)
            if canon(want) != canon(got):
                misses.append(f"{field}: expected {want!r}, got {got!r}")
        form_rows.append((c["id"], len(c["expected"]) - sum(1 for m in misses if not m.startswith("status")),
                          len(c["expected"]), misses, len(result["flags"])))

    perfect = sum(1 for _, _, _, misses, _ in form_rows if not misses)
    got_f, all_f = sum(r[1] for r in form_rows), sum(r[2] for r in form_rows)
    print(f"\nEXTRACT  {perfect}/{len(form_rows)} forms fully correct, {got_f}/{all_f} fields   (cost ${cost:.4f})")
    for cid, ok_fields, n_fields, misses, n_flags in form_rows:
        label = "PASS" if not misses else "FAIL"
        fields = f"{ok_fields}/{n_fields} fields, " if n_fields else ""
        print(f"  {label}  {cid:<26} {fields}{n_flags} flag(s) raised")
        for m in misses:
            print(f"        {_short(m, 300)}")
    return cost


if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part not in ("all", "search", "query", "extract"):
        sys.exit(__doc__)
    total = 0.0
    if part in ("all", "search", "query"):
        total += run_questions(with_claude=part != "search")
    if part in ("all", "extract"):
        total += run_extractions()
    print(f"\ntotal cost this run: ${total:.4f}")
