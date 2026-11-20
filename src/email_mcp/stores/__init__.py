"""Open the email store that the EMAIL_MCP_* environment variables name."""

import os


class ConfigurationError(Exception):
    """Raised at startup when the data environment variables are unusable."""


def open_store():
    """Return a store with search(), get() and description.

    EMAIL_MCP_DATA chooses the emails. EMAIL_MCP_REDACT=on hides personal
    details in whatever that store returns.
    """
    store = open_data_store(os.environ.get("EMAIL_MCP_DATA", "list"))

    # Step 5: wrap the store so every result passes through redaction.
    redact = os.environ.get("EMAIL_MCP_REDACT", "off")
    if redact == "on":
        from email_mcp.stores.redacting_store import RedactingStore

        return RedactingStore(store)
    if redact != "off":
        raise ConfigurationError(
            f"Unknown EMAIL_MCP_REDACT value {redact!r}. Use on or off."
        )
    return store


def open_data_store(mode):
    """Return the store for one EMAIL_MCP_DATA value."""
    # Each store is imported only when chosen, so a release that contains
    # only some steps needs only those steps' files.

    # Step 2: mock emails in a plain Python list.
    if mode == "list":
        from email_mcp.stores.list_store import ListStore

        return ListStore()

    # Step 3: the same mock emails in a SQLite database file.
    if mode == "sqlite-mock":
        from email_mcp.stores.sqlite_store import open_mock_file

        return open_mock_file()

    # Step 4: the Enron sample database file, opened read-only.
    if mode == "enron":
        from email_mcp.stores.enron_store import open_file

        return open_file(os.environ.get("EMAIL_MCP_DB_PATH", "data/enron_sample.db"))

    raise ConfigurationError(
        f"Unknown EMAIL_MCP_DATA value {mode!r}. Use list, sqlite-mock or enron."
    )
