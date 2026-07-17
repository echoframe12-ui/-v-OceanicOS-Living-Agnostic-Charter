import unittest

from review import ReviewEngine


class ReviewEngineTests(unittest.TestCase):
    def test_submit_and_approve(self):
        engine = ReviewEngine()
        review = engine.submit("Add a plugin", "maintainer")
        self.assertEqual(review["status"], "pending")
        approved = engine.approve("Add a plugin")
        self.assertEqual(approved["status"], "approved")


if __name__ == "__main__":
    unittest.main()
