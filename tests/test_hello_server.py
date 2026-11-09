"""Step 1 tests: the first server's count_letter tool over a real stdio connection."""

import sys
import unittest
from tempfile import TemporaryDirectory

from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from email_mcp.hello_server import count_letter


def todo_1_done():
    """Whether count_letter has been filled in.

    Called directly, not over MCP: the SDK hides an unexpected error's text
    from clients, so over MCP an unfinished TODO looks like any other crash.
    """
    try:
        count_letter("strawberry", "r")
    except NotImplementedError:
        return False
    return True


class HelloStdioTests(unittest.IsolatedAsyncioTestCase):
    """Step 1: python -m email_mcp.hello_server, launched the way a host launches it."""

    def setUp(self):
        if not todo_1_done():
            self.fail("TODO 1 not done yet: fill in count_letter in src/email_mcp/hello_server.py")
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        # An unrelated directory proves the installed module works outside the repo.
        self.server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "email_mcp.hello_server"],
            cwd=self.directory.name,
        )

    async def test_tool_discovery(self):
        async with Client(self.server, read_timeout_seconds=10) as client:
            result = await client.list_tools()
            self.assertEqual([tool.name for tool in result.tools], ["count_letter"])
            tool = result.tools[0]
            self.assertIn("Count how many times", tool.description)
            self.assertEqual(sorted(tool.input_schema["required"]), ["letter", "text"])
            self.assertEqual(tool.input_schema["properties"]["text"]["type"], "string")

    async def test_count_then_error_then_count(self):
        async with Client(self.server, read_timeout_seconds=10) as client:
            for text, letter, expected in [
                ("strawberry", "r", 3),
                ("Hello", "h", 1),
                ("MCP", "z", 0),
            ]:
                with self.subTest(text=text, letter=letter):
                    result = await client.call_tool(
                        "count_letter", {"text": text, "letter": letter}
                    )
                    self.assertFalse(result.is_error)
                    # The SDK wraps a plain int result as {"result": ...}.
                    self.assertEqual(result.structured_content, {"result": expected})

            too_long = await client.call_tool(
                "count_letter", {"text": "strawberry", "letter": "rr"}
            )
            self.assertTrue(too_long.is_error)
            self.assertIn(
                "letter must be exactly one character.",
                " ".join(
                    block.text for block in too_long.content if isinstance(block, TextContent)
                ),
            )

            # A missing argument is rejected by the SDK before count_letter runs.
            missing = await client.call_tool("count_letter", {"text": "strawberry"})
            self.assertTrue(missing.is_error)

            # An error does not break the connection; the next call still works.
            again = await client.call_tool("count_letter", {"text": "banana", "letter": "a"})
            self.assertEqual(again.structured_content, {"result": 3})
