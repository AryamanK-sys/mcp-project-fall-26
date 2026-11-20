"""Step 3: search and read emails with SQL in a SQLite database file.

data/mock_emails.db holds step 2's three mock emails as rows in a table. Its
emails table has the Enron sample's columns that the tools use (see
data/README.md), so the same queries also work on the real database file in
step 4, which has more columns.
"""

import json
import re
import sqlite3
import threading
from pathlib import Path

# data/mock_emails.db was made with these two statements. The emails table
# holds one row per email. emails_fts is an FTS5 full-text index that reads
# its text from emails, so search can find words quickly.
SCHEMA = """
CREATE TABLE emails (
    id INTEGER PRIMARY KEY, date TEXT, sender TEXT, to_addrs TEXT, cc_addrs TEXT,
    subject TEXT, body TEXT);
CREATE VIRTUAL TABLE emails_fts USING fts5(
    subject, body, content='emails', content_rowid='id');
"""


class EmailStore:
    """Read-only queries over one SQLite connection shared by all tool calls."""

    def __init__(self, connection, description):
        connection.row_factory = sqlite3.Row  # read columns by name: row["subject"]
        self._connection = connection
        # The SDK runs each tool call in a worker thread; the lock lets only
        # one thread use the shared connection at a time.
        self._lock = threading.Lock()
        self.description = description

    def _query(self, sql, parameters=()):
        """Run one SQL query and return its rows as a list."""
        with self._lock:
            return self._connection.execute(sql, parameters).fetchall()

    def search(self, query, limit):
        # Each ? is filled in by SQLite with the matching value from the
        # tuple passed to _query, in order. snippet() marks matching words in
        # body (column 1) with [brackets].
        sql = """
            SELECT e.id, e.date, e.sender, e.subject,
                   snippet(emails_fts, 1, '[', ']', '...', 24) AS snippet
            FROM emails_fts JOIN emails e ON e.id = emails_fts.rowid
            WHERE emails_fts MATCH ?
            ORDER BY rank LIMIT ?
        """
        try:
            rows = self._query(sql, (query, limit))
        except sqlite3.OperationalError:
            # FTS5 rejects punctuation such as hyphens or colons. Retry with
            # every word quoted, which FTS5 treats as plain text.
            quoted = " ".join(f'"{word}"' for word in re.findall(r"\w+", query))
            if not quoted:
                return []
            rows = self._query(sql, (quoted, limit))
        return [
            {
                "id": row["id"],
                "date": row["date"],
                "sender": row["sender"],
                "subject": row["subject"] or "(no subject)",
                "snippet": (row["snippet"] or "")[:400],
            }
            for row in rows
        ]

    def get(self, email_id):
        """Return the email with this id, or None when no email has it."""
        # TODO 3: look the email up with SQL and return it as a dictionary.
        # search() above is your model: it writes a query with ? for each
        # value, runs it with self._query, and turns each row into a
        # dictionary.
        # Hint 1: select the id, date, sender, to_addrs, cc_addrs, subject
        #         and body columns from the emails table where id = ?, and
        #         run it with self._query(sql, (email_id,)). Always use ?,
        #         never an f-string: SQLite then treats the id as a value,
        #         never as part of the query.
        # Hint 2: if no rows come back, return None.
        # Hint 3: otherwise build the dictionary from rows[0] with the keys
        #         id, date, sender, to, cc, subject and body. to_addrs and
        #         cc_addrs hold JSON text; json.loads turns them back into
        #         lists. An empty subject becomes "(no subject)", as in
        #         search().
        raise NotImplementedError("TODO 3: fill in EmailStore.get in sqlite_store.py")


# The file is found from this file's place in the repository
# (src/email_mcp/stores/), so the server finds it whichever folder it
# starts in.
MOCK_DATABASE = Path(__file__).resolve().parents[3] / "data" / "mock_emails.db"


# Step 3: open data/mock_emails.db.
def open_mock_file():
    # A file: URI with mode=ro opens the database read-only, so no query,
    # and no bug, can change the file.
    connection = sqlite3.connect(
        f"{MOCK_DATABASE.as_uri()}?mode=ro", uri=True, check_same_thread=False
    )
    return EmailStore(connection, "3 synthetic emails in data/mock_emails.db")
