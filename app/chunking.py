import re

HEADING_MARK = "## "  # extract_pages() prefixes detected heading lines with this


def _sections(text: str) -> list[tuple[str, str]]:
    """Split page text into (heading, body) pairs at heading-marked lines."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in text.splitlines():
        if line.startswith(HEADING_MARK):
            sections.append((line[len(HEADING_MARK):].strip(), []))
        elif line.strip():
            sections[-1][1].append(line.strip())
    return [(h, "\n".join(body)) for h, body in sections if h or body]


def _split_body(body: str, limit: int, overlap: int) -> list[str]:
    """Pack lines into pieces up to `limit` chars; slice any single line longer than that."""
    pieces: list[str] = []
    current = ""
    for line in body.splitlines():
        if len(line) > limit:
            if current:
                pieces.append(current)
                current = ""
            step = limit - overlap
            pieces.extend(line[i:i + limit] for i in range(0, len(line), step))
        elif current and len(current) + len(line) + 1 > limit:
            pieces.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        pieces.append(current)
    return pieces


def last_heading(text: str) -> str:
    """The last heading on a page, so a section that continues on the next page keeps its title."""
    found = [ln[len(HEADING_MARK):].strip() for ln in text.splitlines() if ln.startswith(HEADING_MARK)]
    return found[-1] if found else ""


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 150, default_heading: str = "") -> list[str]:
    """One chunk per section, each starting with its heading.

    Sections longer than max_chars are split, and the heading is repeated on every piece so
    each chunk stays self-explanatory. Text with no detected headings is split by length only.
    """
    merged: list[tuple[str, str]] = []
    carry = ""  # consecutive heading-only lines (e.g. document title, subtitle) join the next section
    for heading, body in _sections(text):
        if not heading:  # text before the first heading: a section continued from the previous page
            heading = default_heading
        title = "\n".join(p for p in (carry, heading) if p)
        if not body:
            carry = title
            continue
        merged.append((title, body))
        carry = ""
    if carry:  # heading with nothing after it
        merged.append((carry, ""))

    chunks: list[str] = []
    for heading, body in merged:
        room = max_chars - len(heading) - 1
        for piece in _split_body(body, max(room, 200), overlap):
            chunks.append(f"{heading}\n{piece}" if heading else piece)
    return chunks
