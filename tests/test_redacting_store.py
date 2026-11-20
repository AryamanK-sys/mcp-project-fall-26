"""Step 5: TODO 4 in src/email_mcp/stores/redacting_store.py."""

import unittest

from email_mcp.stores.redacting_store import RedactingStore, redact

# Imported as modules so unittest does not run their test classes here too.
import test_enron
import test_server
from test_server import require_todos


class RedactTests(unittest.TestCase):
    """TODO 4, part 1: redact replaces addresses and phone numbers."""

    def setUp(self):
        require_todos(self, (4,))

    def test_hides_personal_details(self):
        for text, expected in [
            ("Write to jeff.skilling@enron.com today.", "Write to [email] today."),
            ("Call 713-853-6161.", "Call [phone]."),
            ("Call 713.853.6161 or (713) 853-6161.", "Call [phone] or [phone]."),
            ("From a.b@x.com, cell 281-555-0199", "From [email], cell [phone]"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(redact(text), expected)

    def test_keeps_other_text(self):
        for text in [
            "Let's meet on Friday at 10:30.",
            "The deal closed on 2001-05-14 for $1,250,000.",
            "",
        ]:
            with self.subTest(text=text):
                self.assertEqual(redact(text), text)


class FakeStore:
    """A stand-in store with one email that has personal details."""

    description = "a fake store"

    def __init__(self):
        self.email = {
            "id": 7,
            "date": "2001-05-14 09:00:00",
            "sender": "jeff.skilling@enron.com",
            "to": ["kenneth.lay@enron.com"],
            "cc": [],
            "subject": "Call 713-853-6161",
            "body": "Reach me at jeff.skilling@enron.com or 713-853-6161.",
        }

    def search(self, query, limit):
        return [
            {
                "id": 7,
                "date": self.email["date"],
                "sender": self.email["sender"],
                "subject": self.email["subject"],
                "snippet": self.email["body"],
            }
        ]

    def get(self, email_id):
        return self.email if email_id == 7 else None


class RedactingStoreTests(unittest.TestCase):
    """TODO 4, part 2: RedactingStore.get redacts what the wrapped store returns."""

    def setUp(self):
        require_todos(self, (4,))
        self.inner = FakeStore()
        self.store = RedactingStore(self.inner)

    def test_get_redacts_subject_and_body(self):
        self.assertEqual(
            self.store.get(7),
            {
                "id": 7,
                "date": "2001-05-14 09:00:00",
                # The people stay named; only the text is redacted.
                "sender": "jeff.skilling@enron.com",
                "to": ["kenneth.lay@enron.com"],
                "cc": [],
                "subject": "Call [phone]",
                "body": "Reach me at [email] or [phone].",
            },
        )

    def test_get_missing_id_returns_none(self):
        self.assertIsNone(self.store.get(999))

    def test_get_leaves_the_wrapped_store_unchanged(self):
        self.store.get(7)
        self.assertEqual(self.inner.email["body"], FakeStore().email["body"])

    def test_search_redacts_subject_and_snippet(self):
        (summary,) = self.store.search("anything", 5)
        self.assertEqual(summary["subject"], "Call [phone]")
        self.assertEqual(summary["snippet"], "Reach me at [email] or [phone].")
        self.assertEqual(summary["sender"], "jeff.skilling@enron.com")

    def test_description_says_redacted(self):
        self.assertEqual(self.store.description, "a fake store, with personal details redacted")


class RedactedListTests(test_server.ListModeTests):
    """Step 5: EMAIL_MCP_REDACT=on still serves every email.

    The mock emails have no addresses or phone numbers in their text, so the
    results are unchanged. RedactedEnronFixtureTests below checks emails that do.
    """

    environment = {"EMAIL_MCP_REDACT": "on"}
    todos = (2, 4)


# The same emails as step 5 returns them: personal details in the subject and
# body are replaced, and the sender and recipients stay as they are.
REDACTED_FIXTURE_EMAILS = test_enron.FIXTURE_EMAILS[:2] + [
    test_enron.FIXTURE_EMAILS[2]
    | {"subject": "Call [phone]", "body": "Reach me at [email] or [phone]."}
]


class RedactedEnronFixtureTests(test_enron.EnronFixtureStdioTests):
    """Step 5: EMAIL_MCP_REDACT=on hides personal details in the fixture."""

    emails = REDACTED_FIXTURE_EMAILS
    environment = {"EMAIL_MCP_DATA": "enron", "EMAIL_MCP_REDACT": "on"}
    todos = (2, 3, 4)


if __name__ == "__main__":
    unittest.main()
