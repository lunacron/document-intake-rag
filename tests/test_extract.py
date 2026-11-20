"""Extraction checks: every value must appear in the form, and the schema must hold."""
import unittest

from pydantic import ValidationError

from app.extract import grounding_flags
from app.extract_schema import Enrollment

FORM = """Application ID: MROU-2026-00417
Student legal name: Sarah Elizabeth Wilson
Date of birth: March 9, 2008
Known allergies: Peanuts
Emergency contact: Megan Wilson (Mother) 555-0142
Requested courses: ENG 101, MATH 151
Enrollment status: Full-time"""


class GroundingFlagsTests(unittest.TestCase):
    def test_values_copied_from_the_form_raise_no_flags(self):
        data = {"application_id": "MROU-2026-00417", "legal_name": "Sarah Elizabeth Wilson",
                "date_of_birth": "2008-03-09", "known_allergies": "Peanuts"}
        self.assertEqual(grounding_flags(data, FORM), [])

    def test_an_invented_value_is_flagged(self):
        flags = grounding_flags({"known_allergies": "Shellfish"}, FORM)
        self.assertEqual(len(flags), 1)
        self.assertIn("known_allergies", flags[0])
        self.assertIn("not found", flags[0])

    def test_a_date_is_checked_in_the_way_the_form_writes_it(self):
        self.assertEqual(grounding_flags({"date_of_birth": "2008-03-09"}, FORM), [])
        self.assertTrue(grounding_flags({"date_of_birth": "2008-03-10"}, FORM))

    def test_an_invalid_date_is_flagged(self):
        flags = grounding_flags({"date_of_birth": "not-a-date"}, FORM)
        self.assertIn("not a valid date", flags[0])

    def test_matching_ignores_case_spacing_and_punctuation(self):
        self.assertEqual(grounding_flags({"legal_name": "sarah  elizabeth-wilson"}, FORM), [])

    def test_values_inside_lists_and_nested_records_are_checked(self):
        data = {"requested_courses": ["ENG 101", "HIST 200"],
                "emergency_contacts": [{"name": "Megan Wilson", "phone": "555-9999"}]}
        flags = grounding_flags(data, FORM)
        self.assertEqual(len(flags), 2)
        self.assertTrue(any("requested_courses[1]" in f for f in flags))
        self.assertTrue(any("emergency_contacts[0].phone" in f for f in flags))

    def test_mapped_choices_booleans_and_nulls_are_not_text_checked(self):
        data = {"enrollment_status": "full_time", "financial_aid_applied": True, "physician": None}
        self.assertEqual(grounding_flags(data, FORM), [])

    def test_fields_the_model_marked_uncertain_are_flagged(self):
        flags = grounding_flags({"uncertain_fields": ["physician"]}, FORM)
        self.assertEqual(flags, ["physician: the model marked this uncertain"])


class EnrollmentSchemaTests(unittest.TestCase):
    MINIMAL = {"is_enrollment_form": True, "application_id": "MROU-2026-00417",
               "legal_name": "Sarah Elizabeth Wilson", "date_of_birth": "2008-03-09"}

    def test_a_minimal_record_is_valid_and_optional_fields_default_to_empty(self):
        record = Enrollment.model_validate(self.MINIMAL)
        self.assertIsNone(record.physician)
        self.assertEqual(record.requested_courses, [])

    def test_a_missing_required_field_is_rejected(self):
        data = dict(self.MINIMAL)
        del data["legal_name"]
        with self.assertRaises(ValidationError):
            Enrollment.model_validate(data)

    def test_enrollment_status_must_be_one_of_the_allowed_values(self):
        with self.assertRaises(ValidationError):
            Enrollment.model_validate({**self.MINIMAL, "enrollment_status": "sometimes"})

    def test_a_bad_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            Enrollment.model_validate({**self.MINIMAL, "date_of_birth": "March 9"})


if __name__ == "__main__":
    unittest.main()
