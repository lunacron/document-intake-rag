"""Working out which person a question is about, before any vector search runs."""
import unittest

from app.search import match_subjects

PEOPLE = [("s1", "Sarah Elizabeth Wilson"), ("s2", "Marcus Johnson"), ("s3", "Kim Wu")]


class MatchSubjectsTests(unittest.TestCase):
    def test_matches_a_person_by_first_name(self):
        self.assertEqual(match_subjects("What allergies does Sarah have?", PEOPLE), (["s1"], []))

    def test_matches_a_person_by_last_name_case_insensitive(self):
        self.assertEqual(match_subjects("johnson's start term?", PEOPLE), (["s2"], []))

    def test_question_about_nobody_matches_nobody(self):
        self.assertEqual(match_subjects("What is the refund policy?", PEOPLE), ([], []))

    def test_names_shorter_than_three_letters_are_ignored(self):
        # "Wu" is too short to match on its own; "Kim" still works.
        self.assertEqual(match_subjects("Is Wu enrolled?", PEOPLE), ([], []))
        self.assertEqual(match_subjects("Is Kim enrolled?", PEOPLE), (["s3"], []))

    def test_two_people_with_the_same_first_name_are_ambiguous(self):
        people = PEOPLE + [("s4", "Sarah Lopez")]
        matched, ambiguous = match_subjects("What is Sarah's phone number?", people)
        self.assertEqual(matched, [])
        self.assertEqual(len(ambiguous), 1)
        self.assertEqual(sorted(sid for sid, _ in ambiguous[0]), ["s1", "s4"])

    def test_a_fuller_name_beats_a_first_name_only_match(self):
        people = PEOPLE + [("s4", "Sarah Lopez")]
        self.assertEqual(match_subjects("Sarah Wilson's major?", people), (["s1"], []))

    def test_a_question_can_be_about_two_people(self):
        matched, ambiguous = match_subjects("Compare Marcus and Kim", PEOPLE)
        self.assertEqual(sorted(matched), ["s2", "s3"])
        self.assertEqual(ambiguous, [])


if __name__ == "__main__":
    unittest.main()
