"""Step 2: the email tools over a real stdio connection.

The helpers here are shared with the later steps' tests.
"""

import os
import sqlite3
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

from mcp import Client, StdioServerParameters
from mcp.types import TextContent

# Importing email_mcp.server opens a store, which reads EMAIL_MCP_* settings.
# Remove any left in this terminal from running the server, so the tests
# always import the default list store. Each test server gets its own
# settings below.
for key in [key for key in os.environ if key.startswith("EMAIL_MCP_")]:
    del os.environ[key]

# These imports come after the cleanup on purpose.
from email_mcp.server import get_email
from email_mcp.stores.list_store import ListStore
from email_mcp.stores.redacting_store import RedactingStore, redact
from email_mcp.stores.sqlite_store import SCHEMA, EmailStore


# Each TODO is checked by calling it directly, not over MCP: the SDK hides an
# unexpected error's text from clients, so over MCP an unfinished TODO looks
# like any other crash.
def finished(function, *arguments):
    """Whether calling function runs past its NotImplementedError placeholder."""
    try:
        function(*arguments)
    except NotImplementedError:
        return False
    return True


def empty_database():
    """An in-memory database with the step 3 tables and no emails."""
    connection = sqlite3.connect(":memory:")
    connection.executescript(SCHEMA)
    return connection


# TODO number -> (where to finish it, whether it is finished).
TODOS = {
    2: ("fill in get_email in src/email_mcp/server.py",
        lambda: finished(get_email, 1)),
    3: ("fill in EmailStore.get in src/email_mcp/stores/sqlite_store.py",
        lambda: finished(EmailStore(empty_database(), "").get, 1)),
    4: ("fill in redact and RedactingStore.get in src/email_mcp/stores/redacting_store.py",
        lambda: finished(redact, "") and finished(RedactingStore(ListStore()).get, 1)),
}


def require_todos(test, numbers):
    """Fail test with one line naming the first unfinished TODO in numbers."""
    for number in numbers:
        where, is_finished = TODOS[number]
        if not is_finished():
            test.fail(f"TODO {number} not done yet: {where}")


def error_text(result):
    """The text of a tool error, which is what the model reads."""
    return " ".join(block.text for block in result.content if isinstance(block, TextContent))


class ListModeTests(unittest.IsolatedAsyncioTestCase):
    """Step 2: the default list store."""

    # The emails the server should return, exactly as get_email returns them.
    # Later tests reuse these checks with other data by changing these values.
    emails = [
        {
            "id": 1,
            "date": "2026-10-01 16:00:00",
            "sender": "alice@example.com",
            "to": ["bob@example.com"],
            "cc": [],
            "subject": "AI Club project meeting",
            "body": "Let's meet on Friday to work on the MCP project.",
        },
        {
            "id": 2,
            "date": "2026-10-01 18:30:00",
            "sender": "bob@example.com",
            "to": ["alice@example.com"],
            "cc": ["carol@example.com"],
            "subject": "Re: AI Club project meeting",
            "body": "Friday works. I'll bring a sample email for the demo.",
        },
        {
            "id": 3,
            "date": "2026-10-02 09:15:00",
            "sender": "carol@example.com",
            "to": ["alice@example.com", "bob@example.com"],
            "cc": [],
            "subject": "(no subject)",
            "body": "The dataset link is ready. Ask me before sharing it outside the club.",
        },
    ]
    # Each search is (query, the ids it should find in any order). The last
    # query has punctuation, which SQLite's full-text search rejects unless the
    # store retries with each word quoted.
    searches = [("friday", {1, 2}), ("nothing-here", set()), ("dataset-link:", {3})]
    missing_id = 999
    # EMAIL_MCP_* settings for the server; none means the default list store.
    environment = {}
    # The TODOs this data needs; each test fails until they are done.
    todos = (2,)

    def setUp(self):
        require_todos(self, self.todos)
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        # Launch the server the way a host does, from a folder outside the
        # repository, to prove the installed module works anywhere. The SDK
        # adds env to a minimal environment, so settings in your terminal
        # do not reach the server.
        self.server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "email_mcp.server"],
            cwd=self.directory.name,
            env=self.environment,
        )

    async def test_tool_discovery(self):
        async with Client(self.server, read_timeout_seconds=10) as client:
            result = await client.list_tools()
            tools = {tool.name: tool for tool in result.tools}
            self.assertEqual(sorted(tools), ["get_email", "search_emails"])

            search = tools["search_emails"].input_schema
            self.assertEqual(search["required"], ["query"])
            self.assertEqual(search["properties"]["limit"]["maximum"], 10)

            get = tools["get_email"].input_schema
            self.assertEqual(get["required"], ["id"])
            self.assertEqual(get["properties"]["id"]["type"], "integer")

    async def test_search_then_get(self):
        async with Client(self.server, read_timeout_seconds=10) as client:
            for query, expected_ids in self.searches:
                with self.subTest(query=query):
                    result = await client.call_tool("search_emails", {"query": query})
                    self.assertFalse(result.is_error)
                    # The SDK wraps a list result as {"result": [...]}.
                    hits = result.structured_content["result"]
                    self.assertEqual({hit["id"] for hit in hits}, expected_ids)

            for expected in self.emails:
                with self.subTest(id=expected["id"]):
                    result = await client.call_tool("get_email", {"id": expected["id"]})
                    self.assertFalse(result.is_error)
                    self.assertEqual(result.structured_content, expected)

    async def test_errors_then_recovery(self):
        async with Client(self.server, read_timeout_seconds=10) as client:
            missing = await client.call_tool("get_email", {"id": self.missing_id})
            self.assertTrue(missing.is_error)
            self.assertIn(f"No email found for ID {self.missing_id}.", error_text(missing))

            for tool, arguments in [
                ("get_email", {"id": "not-a-number"}),
                ("search_emails", {"query": "x", "limit": 11}),
                ("search_emails", {"query": "   "}),
            ]:
                with self.subTest(tool=tool, arguments=arguments):
                    invalid = await client.call_tool(tool, arguments)
                    self.assertTrue(invalid.is_error)

            # An error does not break the connection; the next call still works.
            first = self.emails[0]
            valid = await client.call_tool("get_email", {"id": first["id"]})
            self.assertEqual(valid.structured_content, first)



def server_environment(settings):
    """This process's environment without EMAIL_MCP_* settings, plus settings."""
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("EMAIL_MCP_")
    }
    return environment | settings


def run_server(settings, directory):
    """Start the stdio server with settings and return once it exits."""
    return subprocess.run(
        [sys.executable, "-m", "email_mcp.server"],
        cwd=directory,
        env=server_environment(settings),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )


class StartupFailureTests(unittest.TestCase):
    """Steps 3 and 5: a bad setting must stop the server, not fall back."""

    def test_unknown_values_stop_startup(self):
        with TemporaryDirectory() as directory:
            for name, value in [
                ("EMAIL_MCP_DATA", "enorn"),
                ("EMAIL_MCP_DATA", "mock"),
                ("EMAIL_MCP_REDACT", "yes"),
            ]:
                with self.subTest(name=name, value=value):
                    process = run_server({name: value}, directory)
                    self.assertNotEqual(process.returncode, 0)
                    self.assertIn("ConfigurationError", process.stderr)
                    self.assertIn(name, process.stderr)
