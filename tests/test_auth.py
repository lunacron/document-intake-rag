"""Roles decide which access levels a caller can read and who may change data."""
import unittest

from fastapi import HTTPException

from app.auth import allowed_levels, current_role, require_registrar


class AuthTests(unittest.TestCase):
    def test_viewer_reads_public_only(self):
        self.assertEqual(allowed_levels("viewer"), ["public"])

    def test_registrar_reads_public_and_restricted(self):
        self.assertEqual(sorted(allowed_levels("registrar")), ["public", "restricted"])

    def test_unknown_role_is_refused(self):
        with self.assertRaises(HTTPException) as ctx:
            current_role("admin")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_only_a_registrar_may_change_data(self):
        self.assertEqual(require_registrar("registrar"), "registrar")
        with self.assertRaises(HTTPException) as ctx:
            require_registrar("viewer")
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
