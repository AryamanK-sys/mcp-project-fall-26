# Step 3: emails in a SQLite database

In this step the same three emails from step 2 come in a database file,
`data/mock_emails.db`. The server and its two tools stay the same; only the
store changes. The new store reads the emails with SQLite, a database built
into Python, and finds them with SQL, the language most databases use. You
look inside the file first, then write the code that reads one email back.

Finish [step 2](../week1/step2-email-tools.md) first, including TODO 2.

## Get week 2

Save your work and bring in the club's week 2 changes, as in the README's
[Save your work and get new weeks](../../README.md#save-your-work-and-get-new-weeks):

```sh
git commit -am "Finish week 1"
git fetch upstream
git merge --no-edit upstream/main
git push
```

Week 2 adds new files and changes a few lines near the top of `server.py`,
above your `get_email`. Your TODO 1 and TODO 2 code stays as you wrote it. Nothing new
needs installing: `sqlite3` is part of Python.

## What is new since step 2

- **A database file.** SQLite keeps data in **tables**. A table has named
  **columns**, and each email is one **row**. The three emails now live in
  `data/mock_emails.db`, a file in this repository, instead of in the
  `MOCK_EMAILS` Python list. The two are separate copies of the same emails:
  changing one does not change the other.
- **SQL.** You ask the database for rows with a query such as
  `SELECT subject FROM emails WHERE id = 3`.
- **Query parameters.** A `?` in a query is a placeholder; SQLite fills it
  with a value you pass separately. This keeps values from being read as
  part of the query.
- **Full-text search.** An index called `emails_fts` lets SQLite find emails
  by their words, and rank the best matches first.
- **Read-only access.** The server opens the file so that no query, and no
  bug, can change it.
- **Choosing the data.** The `EMAIL_MCP_DATA` setting tells the server which
  store to use, so the list store from step 2 still works.

## Look inside the database

Python comes with a small SQLite shell. Open the file with it, from the
repository root:

macOS/Linux:

```sh
.venv/bin/python -m sqlite3 "file:data/mock_emails.db?mode=ro"
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m sqlite3 "file:data/mock_emails.db?mode=ro"
```

`?mode=ro` opens the file **read-only**, the same way the server does, so
nothing you type can change it. At the `sqlite>` prompt, type a query and
press Enter:

```sql
SELECT id, sender, subject FROM emails;
```

The shell prints one line per row:

```text
(1, 'alice@example.com', 'AI Club project meeting')
(2, 'bob@example.com', 'Re: AI Club project meeting')
(3, 'carol@example.com', '')
```

Now look at the recipients of email 3:

```sql
SELECT to_addrs, cc_addrs FROM emails WHERE id = 3;
```

```text
('["alice@example.com", "bob@example.com"]', '[]')
```

Compare these rows with `MOCK_EMAILS` in
[`list_store.py`](../../src/email_mcp/stores/list_store.py):

- In the list, each email is a dictionary, and the step 2 store loops over
  all of them to find one. In the database, each email is a row in the
  `emails` table, and you ask SQLite for the rows you want.
- In the list, `to` is a Python list. SQLite has no list type, so the
  database stores it as **JSON text** in a column named `to_addrs`. The
  quotes around `'["alice@example.com", "bob@example.com"]'` show that it
  is text.
- Email 3 has an empty subject in both. The store turns it into
  "(no subject)" when it returns the email.

Try `SELECT * FROM emails;` to see every column, then type `.quit` to leave
the shell.

## Read the code

### `src/email_mcp/stores/__init__.py`

[`open_store()`](../../src/email_mcp/stores/__init__.py) reads the
`EMAIL_MCP_DATA` environment variable and opens the matching store:

| Value | Step | Data |
|-------|------|------|
| `list` (or not set) | 2 | The three emails in a Python list |
| `sqlite-mock` | 3 | The same three emails in `data/mock_emails.db` |
| `enron` | 4 | 1,000 real emails from a database file; see [step 4](step4-enron.md) |

`server.py` now calls `open_store()` instead of creating a `ListStore`. An
unknown value stops the server at startup with an error naming
`EMAIL_MCP_DATA`, rather than quietly using other data.

### `src/email_mcp/stores/sqlite_store.py`

[`sqlite_store.py`](../../src/email_mcp/stores/sqlite_store.py) has the new
store.

- `SCHEMA` shows the statements that created the two tables in
  `data/mock_emails.db`. `emails` has one column per field. `to` and `cc`
  become `to_addrs` and `cc_addrs`, stored as JSON text. `emails_fts` is the
  full-text index over `subject` and `body`.
- `open_mock_file()` opens the file read-only, with `mode=ro` as in the
  shell above, and returns an `EmailStore`. `MOCK_DATABASE` finds the file
  from where `sqlite_store.py` sits in the repository, so the server finds
  it whichever folder it starts in.
- `EmailStore.search()` is written for you. Its query joins the full-text
  index to the `emails` table, finds rows whose words match, puts the best
  matches first and returns at most `limit` of them. `snippet()` returns a
  short piece of the body with the matching words in `[brackets]`.
- `EmailStore._query()` runs one query and returns its rows. Each row works
  like a dictionary: `row["subject"]`.
- `EmailStore.get()` is not finished yet; it is TODO 3.

## Fill in TODO 3

In `src/email_mcp/stores/sqlite_store.py`, find `EmailStore.get()`. Replace
its `raise NotImplementedError(...)` line with code that does three things:

1. Run a query that selects the `id`, `date`, `sender`, `to_addrs`,
   `cc_addrs`, `subject` and `body` columns from `emails` where `id = ?`.
   Run it with `self._query(sql, (email_id,))`. The comma makes
   `(email_id,)` a tuple with one value.
2. If no rows come back, return `None`. `server.py` turns that into the
   "No email found" error you wrote in TODO 2.
3. Otherwise, return a dictionary built from `rows[0]` with the keys `id`,
   `date`, `sender`, `to`, `cc`, `subject` and `body`. Use `json.loads` to
   turn `to_addrs` and `cc_addrs` back into lists, and return
   `"(no subject)"` when the subject is empty, as `search()` does.

Use `search()`, just above it, as your model. Always put the id in the query
with `?`, never with an f-string such as `f"... WHERE id = {email_id}"`.
With `?`, SQLite treats the value only as data. Pasting values into the
query text is how **SQL injection** happens: a value that contains SQL
changes what the query does.

## Check it works

Run the step 3 tests from the repository root.

macOS/Linux:

```sh
.venv/bin/python -m unittest discover -s tests -p "test_sqlite_store.py" -v
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_sqlite_store.py" -v
```

The tests first check that `data/mock_emails.db` holds the three emails,
then check TODO 3 on its own, then start the server with
`EMAIL_MCP_DATA=sqlite-mock` and run the same checks as step 2. Until TODO 3
is done, they fail with:

```text
AssertionError: TODO 3 not done yet: fill in EmailStore.get in src/email_mcp/stores/sqlite_store.py
```

Once it is right, all 7 tests pass.

## Connect it to Claude

The tools are the same as in step 2, so your **AI Club MCP** connector
does not change. Only the server's setting does.

1. **Restart the server with the SQLite store.** Press **Ctrl+C** in the
   server terminal, then run:

   macOS/Linux:

   ```sh
   export EMAIL_MCP_DATA=sqlite-mock
   .venv/bin/mcp run src/email_mcp/server.py:mcp --transport streamable-http
   ```

   Windows (PowerShell):

   ```powershell
   $env:EMAIL_MCP_DATA = "sqlite-mock"
   .\.venv\Scripts\mcp.exe run src/email_mcp/server.py:mcp --transport streamable-http
   ```

   The setting lasts until you close that terminal. The tests ignore it, so
   you can run them from the same terminal.

2. **Start the tunnel if it is not running**, as in
   [step 2](../week1/step2-email-tools.md#connect-it-to-claude), and check
   that its address still matches your connector's URL.

3. **Start a new chat with Haiku** and check that **AI Club MCP** is
   enabled.

## Try it

Ask the same questions as in step 2:

> Use the email tools to find the email about the AI Club project meeting and summarize it.

> Which email has no subject, and who sent it?

> Read email 999.

The answers should match step 2's: the emails are the same, only where the
server reads them from has changed. Open a `search_emails` call and look at
the `snippet`: matching words now appear in `[brackets]`, which shows the
full-text index found them.

## Try changing it

1. **Search syntax.** Full-text search understands a small query language.
   Ask Claude to search for `friday OR dataset`, then for
   `"project meeting"` with the quotes. The first finds emails with either
   word; the second finds the two words next to each other. The
   [FTS5 documentation](https://www.sqlite.org/fts5.html#full_text_query_syntax)
   lists the rest.
2. **Two copies.** Change the subject of email 1 in `MOCK_EMAILS`, restart
   the server in `sqlite-mock` mode and ask Claude for email 1. The subject
   has not changed: the server reads the database file, not the list. Undo
   your change afterwards; the step 2 tests expect the original subject.

## If it does not work

- `test_rows_hold_every_field` fails: `data/mock_emails.db` was changed.
  Restore it with `git checkout data/mock_emails.db`.
- `sqlite3.OperationalError: unable to open database file`: the file is
  missing. Restore it with `git checkout data/mock_emails.db`; if Git does
  not know the file, get week 2 again as described above.
- A test shows two dictionaries that differ in `to` or `cc`, such as
  `'["bob@example.com"]'` instead of `['bob@example.com']`: the list was
  not turned back with `json.loads`.
- `sqlite3.OperationalError: no such module: fts5`: your Python's SQLite
  has no full-text search. Install Python 3.14 from
  [python.org](https://www.python.org/downloads/), recreate `.venv`, and
  ask for help if it persists.
- `ConfigurationError: Unknown EMAIL_MCP_DATA value`: check the spelling;
  the values are `list`, `sqlite-mock` and `enron`.
- Claude reports "Error executing tool get_email": run the step 3 tests to
  see the details, then restart the server.

## References

- [Python: sqlite3](https://docs.python.org/3/library/sqlite3.html):
  connections, `execute`, and
  [placeholders](https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders),
  which explains why `?` prevents SQL injection.
- [Python: the sqlite3 command-line interface](https://docs.python.org/3/library/sqlite3.html#command-line-interface):
  the shell used in "Look inside the database".
- [SQLite: URI filenames](https://www.sqlite.org/uri.html): what
  `file:...?mode=ro` means.
- [SQLite: SELECT](https://www.sqlite.org/lang_select.html).
- [SQLite: FTS5 full-text search](https://www.sqlite.org/fts5.html):
  `MATCH`, `rank` and `snippet()`.
- [Python: json](https://docs.python.org/3/library/json.html): `json.loads`
  turns JSON text back into a list.
