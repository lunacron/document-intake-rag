"""Redaction of high-risk identifiers before anything is embedded or sent to Claude."""
import unittest

from app.pii import redact


class RedactTests(unittest.TestCase):
    def test_a_social_security_number_is_replaced(self):
        clean, counts = redact("Applicant SSN: 536-22-4817")
        self.assertNotIn("536-22-4817", clean)
        self.assertIn("<US_SSN>", clean)
        self.assertEqual(counts.get("US_SSN"), 1)

    def test_a_credit_card_number_is_replaced(self):
        clean, counts = redact("Card on file: 4111 1111 1111 1111")
        self.assertNotIn("4111 1111 1111 1111", clean)
        self.assertEqual(counts.get("CREDIT_CARD"), 1)

    def test_names_and_emails_are_kept_for_staff_questions(self):
        text = "Student: Kim Wu, email kim.wu2007@example.com"
        clean, counts = redact(text)
        self.assertEqual(clean, text)
        self.assertEqual(counts, {})

    def test_text_without_identifiers_is_unchanged(self):
        text = "Known allergies: Peanuts"
        self.assertEqual(redact(text), (text, {}))


if __name__ == "__main__":
    unittest.main()
