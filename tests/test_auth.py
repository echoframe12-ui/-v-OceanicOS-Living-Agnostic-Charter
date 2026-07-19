import os
import sqlite3
import tempfile
import unittest

from auth import AuthRegistry


class AuthRegistryTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        handle.close()
        self.db_path = handle.name
        self.auth = AuthRegistry(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_register_returns_token_once(self):
        result = self.auth.register("alice")
        self.assertEqual(result["username"], "alice")
        self.assertTrue(result["token"])
        self.assertIn("created_at", result)

    def test_raw_token_is_never_stored(self):
        result = self.auth.register("bob")
        token = result["token"]
        with sqlite3.connect(self.db_path) as conn:
            stored = conn.execute(
                "SELECT token_hash FROM users WHERE username = ?", ("bob",)
            ).fetchone()[0]
        self.assertNotEqual(stored, token)
        self.assertEqual(len(stored), 64)  # sha256 hex

    def test_authenticate_valid_and_invalid(self):
        token = self.auth.register("carol")["token"]
        user = self.auth.authenticate(token)
        self.assertEqual(user["username"], "carol")
        self.assertIsNone(self.auth.authenticate("not-a-real-token"))
        self.assertIsNone(self.auth.authenticate(None))

    def test_duplicate_username_raises(self):
        self.auth.register("dave")
        with self.assertRaises(ValueError):
            self.auth.register("dave")

    def test_empty_username_raises(self):
        with self.assertRaises(ValueError):
            self.auth.register("   ")

    def test_list_users_leaks_no_secrets(self):
        self.auth.register("erin")
        users = self.auth.list_users()
        self.assertEqual(users[0]["username"], "erin")
        self.assertNotIn("token", users[0])
        self.assertNotIn("token_hash", users[0])

    def test_new_users_default_to_attestor_tier(self):
        self.assertEqual(self.auth.register("frank")["tier"], "attestor")
        self.assertEqual(self.auth.authenticate(self.auth.register("gina")["token"])["tier"], "attestor")

    def test_set_tier_updates_and_validates(self):
        token = self.auth.register("hana")["token"]
        self.auth.set_tier("hana", "arbiter")
        self.assertEqual(self.auth.authenticate(token)["tier"], "arbiter")
        with self.assertRaises(ValueError):
            self.auth.set_tier("hana", "platinum")
        with self.assertRaises(KeyError):
            self.auth.set_tier("nobody", "arbiter")

    def test_admin_users_get_the_admin_role(self):
        auth = AuthRegistry(self.db_path, admin_users=["root"])
        root = auth.register("root")
        joe = auth.register("joe")
        self.assertEqual(root["role"], "admin")
        self.assertEqual(joe["role"], "member")
        # authenticate reflects the stored role
        self.assertEqual(auth.authenticate(root["token"])["role"], "admin")
        self.assertEqual(auth.authenticate(joe["token"])["role"], "member")

    def test_list_users_role_is_opt_in(self):
        auth = AuthRegistry(self.db_path, admin_users=["root"])
        auth.register("root")
        auth.register("joe")
        without_role = auth.list_users()
        self.assertNotIn("role", without_role[0])
        with_role = auth.list_users(include_role=True)
        roles = {u["username"]: u["role"] for u in with_role}
        self.assertEqual(roles["root"], "admin")
        self.assertEqual(roles["joe"], "member")


if __name__ == "__main__":
    unittest.main()
