"""Serve the email search and lookup tools."""

from typing import Annotated, TypedDict

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from email_mcp.stores.list_store import ListStore

MAX_SEARCH_LIMIT = 10


# These describe the tools' results; the SDK turns them into output schemas.
class EmailSummary(TypedDict):
    """One search result."""

    id: int
    date: str
    sender: str
    subject: str
    snippet: str


class Email(TypedDict):
    """One email in full."""

    id: int
    date: str
    sender: str
    to: list[str]
    cc: list[str]
    subject: str
    body: str


# The store holds the emails; the tools below ask it for them.
store = ListStore()

mcp = MCPServer("email", instructions=f"Serves {store.description}.")


# Register these functions as MCP tools clients can discover and call. The SDK
# builds each tool's input schema from the type hints; Annotated[..., Field(...)]
# adds a description or bounds that the SDK checks before the function runs.
@mcp.tool()
def search_emails(
    query: Annotated[
        str,
        Field(description="Words to look for; emails containing every word match."),
    ],
    limit: Annotated[int, Field(ge=1, le=MAX_SEARCH_LIMIT)] = 5,
) -> list[EmailSummary]:
    """Search email subjects and bodies.

    Returns each match's id, date, sender, subject and a short snippet.
    Pass an id to get_email to read the full email.
    """
    if not query.strip():
        raise ToolError("Search query must contain at least one word.")
    return store.search(query, limit)


@mcp.tool()
def get_email(id: int) -> Email:
    """Get one email in full by the id that search_emails returned."""
    # TODO 2: look up the email with this id and return it.
    # search_emails above is your model: it checks its input, raises a
    # ToolError when it cannot answer, and returns what the store gives it.
    # Hint 1: store.get(id) returns the email, or None when no email has
    #         that id.
    # Hint 2: if there is no email, raise
    #         ToolError(f"No email found for ID {id}.")
    #         Use that exact message; the tests check it.
    # Hint 3: otherwise, return the email.
    raise NotImplementedError("TODO 2: fill in get_email in server.py")


if __name__ == "__main__":
    # stdout (standard output) carries MCP messages. Send diagnostic logs to
    # stderr (standard error) so log text does not interfere with those messages.
    mcp.run(transport="stdio")
