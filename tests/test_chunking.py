"""Chunking: one chunk per section, headings kept, long sections split with the heading repeated."""
import unittest

from app.chunking import HEADING_MARK, chunk_text, last_heading


def h(title: str) -> str:
    return f"{HEADING_MARK}{title}"


class ChunkTextTests(unittest.TestCase):
    def test_one_chunk_per_section_each_starting_with_its_heading(self):
        text = "\n".join([h("Contact"), "Phone: 555-0100", h("Health"), "Known allergies: Peanuts"])
        self.assertEqual(chunk_text(text), ["Contact\nPhone: 555-0100", "Health\nKnown allergies: Peanuts"])

    def test_heading_only_lines_join_the_next_section(self):
        text = "\n".join([h("Enrollment Form"), h("Student Information"), "Name: Sarah"])
        self.assertEqual(chunk_text(text), ["Enrollment Form\nStudent Information\nName: Sarah"])

    def test_long_section_is_split_and_heading_repeated_on_every_piece(self):
        lines = [f"Course {i}: Introduction to a long subject name" for i in range(60)]
        chunks = chunk_text("\n".join([h("Requested Courses")] + lines), max_chars=400)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertTrue(chunk.startswith("Requested Courses\n"))
            self.assertLessEqual(len(chunk), 400)
        body = "\n".join(c.split("\n", 1)[1] for c in chunks)
        for line in lines:  # nothing is lost
            self.assertIn(line, body)

    def test_a_single_line_longer_than_the_limit_is_sliced_with_overlap(self):
        line = "x" * 1000
        chunks = chunk_text(line, max_chars=400, overlap=100)
        self.assertGreater(len(chunks), 2)
        self.assertEqual(chunks[0][-100:], chunks[1][:100])

    def test_text_without_headings_uses_the_default_heading(self):
        chunks = chunk_text("continued text from the last page", default_heading="Health")
        self.assertEqual(chunks, ["Health\ncontinued text from the last page"])

    def test_empty_text_gives_no_chunks(self):
        self.assertEqual(chunk_text(""), [])


class LastHeadingTests(unittest.TestCase):
    def test_returns_the_last_heading_on_the_page(self):
        self.assertEqual(last_heading("\n".join([h("A"), "x", h("B"), "y"])), "B")

    def test_returns_empty_when_there_is_no_heading(self):
        self.assertEqual(last_heading("just text"), "")


if __name__ == "__main__":
    unittest.main()
