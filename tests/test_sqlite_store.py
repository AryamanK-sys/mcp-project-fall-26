"""Step 3: data/mock_emails.db, and TODO 3 in src/email_mcp/stores/sqlite_store.py."""

import json
import sqlite3
import unittest

from email_mcp.stores.sqlite_store import MOCK_DATABASE, EmailStore

# Imported as a module so unittest does not run its test classes here too.
import test_server
from test_server import empty_database, require_todos

# The rows in data/mock_emails.db for emails 1 to 3, in the table's column
# order, with to and cc stored as JSON text.
EXPECTED_ROWS = [
    (1, "2026-10-01 16:00:00", "alice@example.com", '["bob@example.com"]', "[]",
     "AI Club project meeting", "Let's meet on Friday to work on the MCP project."),
    (2, "2026-10-01 18:30:00", "bob@example.com", '["alice@example.com"]',
     '["carol@example.com"]', "Re: AI Club project meeting",
     "Friday works. I'll bring a sample email for the demo."),
    (3, "2026-10-02 09:15:00", "carol@example.com",
     '["alice@example.com", "bob@example.com"]', "[]", "",
     "The dataset link is ready. Ask me before sharing it outside the club."),
]


class MockDatabaseTests(unittest.TestCase):
    """data/mock_emails.db holds the three mock emails. No TODO needed.

    If these fail after you changed the file, restore it with
    git checkout data/mock_emails.db
    """

    def setUp(self):
        self.connection = sqlite3.connect(f"{MOCK_DATABASE.as_uri()}?mode=ro", uri=True)
        self.addCleanup(self.connection.close)

    def test_rows_hold_every_field(self):
        rows = self.connection.execute("SELECT * FROM emails ORDER BY id").fetchall()
        self.assertEqual(rows, EXPECTED_ROWS)

    def test_full_text_index_finds_words(self):
        rows = self.connection.execute(
            "SELECT rowid FROM emails_fts WHERE emails_fts MATCH 'friday' ORDER BY rowid"
        ).fetchall()
        self.assertEqual(rows, [(1,), (2,)])


class GetTests(unittest.TestCase):
    """TODO 3: EmailStore.get reads one email with SQL.

    The rows are inserted into a new database here, so the test does not
    depend on data/mock_emails.db.
    """

    def setUp(self):
        require_todos(self, (3,))
        connection = empty_database()
        connection.executemany(
            "INSERT INTO emails VALUES (?, ?, ?, ?, ?, ?, ?)", EXPECTED_ROWS
        )
        self.store = EmailStore(connection, "test emails")

    def test_returns_each_email(self):
        for row in EXPECTED_ROWS:
            with self.subTest(id=row[0]):
                self.assertEqual(
                    self.store.get(row[0]),
                    {
                        "id": row[0],
                        "date": row[1],
                        "sender": row[2],
                        "to": json.loads(row[3]),
                        "cc": json.loads(row[4]),
                        "subject": row[5] or "(no subject)",
                        "body": row[6],
                    },
                )

    def test_missing_id_returns_none(self):
        self.assertIsNone(self.store.get(999))


class SqliteMockTests(test_server.ListModeTests):
    """Step 3: EMAIL_MCP_DATA=sqlite-mock, the same emails in data/mock_emails.db."""

    environment = {"EMAIL_MCP_DATA": "sqlite-mock"}
    todos = (2, 3)


if __name__ == "__main__":
    unittest.main()
