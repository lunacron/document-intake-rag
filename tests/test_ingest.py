"""Page text extraction marks headings so chunks can carry their section titles."""
import unittest
from pathlib import Path

from app.chunking import HEADING_MARK
from app.ingest import default_label, extract_pages

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


class ExtractPagesTests(unittest.TestCase):
    def test_sample_form_yields_text_with_headings_marked(self):
        pdf = SAMPLES / "enrollment_sarah_wilson.pdf"
        pages = extract_pages(pdf.name, pdf.read_bytes())
        text = "\n".join(pages)
        self.assertIn("Sarah Elizabeth Wilson", text)
        headings = [ln for ln in text.splitlines() if ln.startswith(HEADING_MARK)]
        self.assertTrue(any("Student Information" in ln for ln in headings))

    def test_plain_text_files_are_read_as_one_page(self):
        self.assertEqual(extract_pages("notes.txt", "hello\nworld".encode()), ["hello\nworld"])

    def test_default_label_comes_from_the_file_name(self):
        self.assertEqual(default_label("enrollment_sarah_wilson.pdf"), "Enrollment Sarah Wilson")


if __name__ == "__main__":
    unittest.main()
