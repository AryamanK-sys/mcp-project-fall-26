"""Step 4: Enron mode over a synthetic Enron-schema database.

The fixture copies the Enron sample's schema from data/README.md but holds
synthetic emails, so Enron mode can be tested without the private database.
The real sample is checked too when data/enron_sample.db exists.
"""

import json
import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp import Client, StdioServerParameters

# Imported as a module so unittest does not run its test classes here too.
import test_server

ENRON_SAMPLE = Path(__file__).resolve().parent.parent / "data" / "enron_sample.db"

# Written independently of the server code so a schema mismatch fails.
_ENRON_SCHEMA = """
CREATE TABLE emails (
    id INTEGER PRIMARY KEY, message_id TEXT, mailbox TEXT, mailboxes TEXT, folder TEXT,
    date TEXT, sender TEXT, to_addrs TEXT, cc_addrs TEXT, bcc_addrs TEXT,
    subject TEXT, body TEXT, tags TEXT);
CREATE VIRTUAL TABLE emails_fts USING fts5(subject, body, content='emails', content_rowid='id');
"""

_FIXTURE_ROWS = [
    (101, "<101.fixture@example>", "sample-a", "sample-a", "inbox", "2001-05-01 10:00:00",
     "trader@example.com", ["sample-a@example.com"], ["legal@example.com"],
     ["legal@example.com"], "Pipeline capacity", "Capacity on the west pipeline is full.",
     "has_cc,has_bcc"),
    (102, "<102.fixture@example>", "sample-b", "sample-b,sample-a", "sent_items",
     "2001-05-02 11:30:00", "sample-b@example.com",
     ["trader@example.com", "sample-a@example.com"], [], [], "",
     "Pipeline maintenance moves to Monday.", "sent,no_subject"),
    (103, "<103.fixture@example>", "sample-a", "sample-a", "inbox", "2001-05-03 08:45:00",
     "sample-b@example.com", ["sample-a@example.com"], [], [], "Call 713-555-0142",
     "Reach me at sample-b@example.com or 713-555-0142.", ""),
]


def write_enron_fixture(path):
    """Create a small Enron-schema SQLite database at path."""
    connection = sqlite3.connect(path)
    connection.executescript(_ENRON_SCHEMA)
    for row in _FIXTURE_ROWS:
        values = list(row)
        values[7:10] = [json.dumps(addresses) for addresses in values[7:10]]
        connection.execute(
            "INSERT INTO emails VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values
        )
    connection.execute("INSERT INTO emails_fts(emails_fts) VALUES ('rebuild')")
    connection.commit()
    connection.close()


# What the server should return for the fixture rows above.
FIXTURE_EMAILS = [
    {
        "id": 101,
        "date": "2001-05-01 10:00:00",
        "sender": "trader@example.com",
        "to": ["sample-a@example.com"],
        "cc": ["legal@example.com"],
        "subject": "Pipeline capacity",
        "body": "Capacity on the west pipeline is full.",
    },
    {
        "id": 102,
        "date": "2001-05-02 11:30:00",
        "sender": "sample-b@example.com",
        "to": ["trader@example.com", "sample-a@example.com"],
        "cc": [],
        "subject": "(no subject)",
        "body": "Pipeline maintenance moves to Monday.",
    },
    {
        "id": 103,
        "date": "2001-05-03 08:45:00",
        "sender": "sample-b@example.com",
        "to": ["sample-a@example.com"],
        "cc": [],
        "subject": "Call 713-555-0142",
        "body": "Reach me at sample-b@example.com or 713-555-0142.",
    },
]

FIXTURE_SEARCHES = [("pipeline", {101, 102}), ("friday", set()), ("west-pipeline:", {101})]


class EnronFixtureStdioTests(test_server.ListModeTests):
    """EMAIL_MCP_DATA=enron reading data/enron_sample.db from the working directory."""

    emails = FIXTURE_EMAILS
    searches = FIXTURE_SEARCHES
    missing_id = 1
    # Only EMAIL_MCP_DATA is set, so the default relative path is used.
    environment = {"EMAIL_MCP_DATA": "enron"}
    # Step 4 reuses step 3's EmailStore, so it needs TODO 3 too.
    todos = (2, 3)

    def setUp(self):
        super().setUp()
        data = Path(self.directory.name) / "data"
        data.mkdir()
        write_enron_fixture(data / "enron_sample.db")


@unittest.skipUnless(ENRON_SAMPLE.is_file(), "data/enron_sample.db is not present")
class EnronSampleStdioTests(unittest.IsolatedAsyncioTestCase):
    """The real Enron sample, when a contributor has it. Checks shape only."""

    def setUp(self):
        test_server.require_todos(self, (2, 3))

    async def test_search_then_get(self):
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "email_mcp.server"],
            env={"EMAIL_MCP_DATA": "enron", "EMAIL_MCP_DB_PATH": str(ENRON_SAMPLE)},
        )
        async with Client(server, read_timeout_seconds=10) as client:
            result = await client.call_tool("search_emails", {"query": "california", "limit": 10})
            hits = result.structured_content["result"]
            self.assertEqual(len(hits), 10)

            for email_id in (hits[0]["id"], 1, 1000):
                email = await client.call_tool("get_email", {"id": email_id})
                self.assertFalse(email.is_error)
                self.assertEqual(email.structured_content["id"], email_id)
                self.assertIsInstance(email.structured_content["to"], list)
                self.assertNotIn("bcc", email.structured_content)

            missing = await client.call_tool("get_email", {"id": 1001})
            self.assertTrue(missing.is_error)


class DatabaseSettingFailureTests(unittest.TestCase):
    """A missing or wrong database file must stop the server at startup."""

    def test_bad_database_stops_startup(self):
        with TemporaryDirectory() as directory:
            not_a_database = Path(directory) / "notes.db"
            not_a_database.write_text("not a database")
            for settings in (
                {"EMAIL_MCP_DATA": "enron"},  # no data/enron_sample.db here
                {"EMAIL_MCP_DATA": "enron", "EMAIL_MCP_DB_PATH": str(not_a_database)},
            ):
                with self.subTest(settings=settings):
                    process = test_server.run_server(settings, directory)
                    self.assertNotEqual(process.returncode, 0)
                    self.assertIn("ConfigurationError", process.stderr)
                    self.assertIn("EMAIL_MCP_DB_PATH", process.stderr)
