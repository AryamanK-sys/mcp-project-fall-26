"""Step 2: the email tools over a real stdio connection."""

import sys
import unittest
from tempfile import TemporaryDirectory

from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from email_mcp.server import get_email


def todo_2_done():
    """Whether get_email has been filled in.

    Called directly, not over MCP: the SDK hides an unexpected error's text
    from clients, so over MCP an unfinished TODO looks like any other crash.
    """
    try:
        get_email(1)
    except NotImplementedError:
        return False
    return True


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
    # Each search is (query, the ids it should find in any order).
    searches = [("friday", {1, 2}), ("nothing-here", set())]
    missing_id = 999

    def setUp(self):
        if not todo_2_done():
            self.fail("TODO 2 not done yet: fill in get_email in src/email_mcp/server.py")
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        # Launch the server the way a host does, from a folder outside the
        # repository, to prove the installed module works anywhere.
        self.server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "email_mcp.server"],
            cwd=self.directory.name,
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

