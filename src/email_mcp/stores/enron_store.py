"""Step 4: open the Enron sample database file read-only.

Searching and reading reuse step 3's EmailStore and its SQL unchanged; only
the way the database is opened differs.
"""

import sqlite3
from pathlib import Path

from email_mcp.stores import ConfigurationError
from email_mcp.stores.sqlite_store import EmailStore


def open_file(path_text):
    path = Path(path_text).resolve()
    if not path.is_file():
        raise ConfigurationError(
            f"EMAIL_MCP_DATA=enron but no database file exists at {path}. "
            "Save the database there or set EMAIL_MCP_DB_PATH to its location."
        )
    # A file: URI with mode=ro opens the database read-only.
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, check_same_thread=False)
    try:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    except sqlite3.DatabaseError:  # the file exists but is not a SQLite database
        tables = set()
    if not {"emails", "emails_fts"} <= tables:
        connection.close()
        raise ConfigurationError(
            f"{path} (from EMAIL_MCP_DB_PATH) lacks the emails and emails_fts tables "
            "described in data/README.md."
        )
    # Clients see the description, so it names the file but not the folder it is in.
    return EmailStore(connection, f"the Enron sample database {path.name}")
