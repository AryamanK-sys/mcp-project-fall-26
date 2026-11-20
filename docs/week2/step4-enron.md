# Step 4: real emails from Enron

In this step your server reads 1,000 real emails instead of three made-up
ones. The emails are in a SQLite database file with the same `emails` and
`emails_fts` tables as step 3's `data/mock_emails.db`, so step 3's
`EmailStore`, and your TODO 3, read it unchanged. There is no TODO in this
step: you download the database, point the server at it, and see how the
same two tools cope with real data.

Finish [step 3](step3-sqlite.md) first, including TODO 3.

## Where these emails come from

Enron was an energy company in Texas, and one of the largest companies in
the US. In December 2001 it went bankrupt after it came out that it had
hidden debts and inflated its profits through accounting fraud. A US agency
investigating the company, the Federal Energy Regulatory Commission,
released the employees' emails online, which is why they are public now.
Researchers at Carnegie Mellon University then gathered about half a million
of them, from about 150 employees, into the dataset that is still used
today. Our MCP project needs only a sample, not that whole messy
collection, so the project coordinators cleaned it and kept 1,000 emails:
100 from each of ten mailboxes.

## What is new since step 3

- **A downloaded database file.** The emails live in
  `data/enron_sample.db`, which you will download using a terminal command.
- **Startup checks.** The server checks that the file exists and has the
  right tables before it accepts any request.
- **Real data.** Real emails have long bodies, quoted replies, odd
  addresses, and personal details such as phone numbers. Step 5 deals with
  those.

## Get the database

The database is not stored in this repository. Keeping data files out of a
Git repository is common practice: the repository stays small and quick to
clone, and the data lives with a storage provider and is downloaded with one
command. (A tiny sample such as step 3's `data/mock_emails.db` is the
exception.) The club keeps the database on
[Google Drive](https://drive.google.com/file/d/1ayZGS1kMYTdYyGBgfFqTmVZYGiq4mg4l/view?usp=sharing).
Git already ignores everything in `data/` except `data/README.md` and
`data/mock_emails.db`, so `git commit -am` and `git add .` leave the
database out.

1. **Download it** from the repository root. The quotes matter.

   macOS/Linux:

   ```sh
   curl -L -o data/enron_sample.db "https://drive.google.com/uc?export=download&id=1ayZGS1kMYTdYyGBgfFqTmVZYGiq4mg4l"
   ```

   Windows (PowerShell):

   ```powershell
   curl.exe -L -o data\enron_sample.db "https://drive.google.com/uc?export=download&id=1ayZGS1kMYTdYyGBgfFqTmVZYGiq4mg4l"
   ```

   `-L` follows Google's redirect to the file and `-o` names where to save
   it. On Windows, type `curl.exe`: plain `curl` in PowerShell runs a
   different command.

2. **Check the size.** The file should be about 3.5 MB (3,551,232 bytes).
   If it is only a few kilobytes, `curl` saved a Google web page instead,
   usually because many people downloaded the file recently and Google is
   limiting downloads. Wait a while and download again.

[data/README.md](../../data/README.md) describes the database: its columns,
its ten mailboxes, and example queries.

## Read the code

[`src/email_mcp/stores/enron_store.py`](../../src/email_mcp/stores/enron_store.py)
opens the file and hands it to step 3's `EmailStore`.

- `Path(path_text).resolve()` turns the path into a full one, so error
  messages show exactly where the server looked.
- If there is no file there, it raises `ConfigurationError` and the server
  stops, naming `EMAIL_MCP_DB_PATH`.
- `sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, ...)` opens the
  file read-only, as step 3's `open_mock_file()` does.
- It checks that the `emails` and `emails_fts` tables exist, so a wrong
  file fails at startup instead of on the first tool call.

`EMAIL_MCP_DB_PATH` names the file. Its default, `data/enron_sample.db`,
is relative to the folder the server starts in, so start the server from
the repository root.

To look inside, open it with the SQLite shell from
[step 3](step3-sqlite.md#look-inside-the-database), using
`"file:data/enron_sample.db?mode=ro"`. [data/README.md](../../data/README.md)
lists its columns and has example queries.

## Check it works

Run the step 4 tests from the repository root.

macOS/Linux:

```sh
.venv/bin/python -m unittest discover -s tests -p "test_enron.py" -v
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_enron.py" -v
```

Most of these tests use a tiny made-up database with the same tables, so
they work before you download anything. One test reads your real
`data/enron_sample.db`; it is skipped until the file is there. With
TODO 3 done and the file downloaded, all 5 tests pass. If they fail with
"TODO 3 not done yet", go back to [step 3](step3-sqlite.md).

## Connect it to Claude

As in step 3, the tools and your **AI Club MCP** connector stay the same.

1. **Restart the server with the Enron data.** Press **Ctrl+C** in the
   server terminal, then, from the repository root:

   macOS/Linux:

   ```sh
   export EMAIL_MCP_DATA=enron
   .venv/bin/mcp run src/email_mcp/server.py:mcp --transport streamable-http
   ```

   Windows (PowerShell):

   ```powershell
   $env:EMAIL_MCP_DATA = "enron"
   .\.venv\Scripts\mcp.exe run src/email_mcp/server.py:mcp --transport streamable-http
   ```

2. **Start the tunnel if it is not running**, and check that its address
   matches your connector's URL.

3. **Start a new chat with Haiku** with **AI Club MCP** enabled.

**Stop ngrok when you are not using it.** While the tunnel runs, anyone who
has your address can read these real emails. Press **Ctrl+C** in the ngrok
terminal whenever you finish testing or step away.

## Try it

> Search the emails for California and summarize what the top three results are about.

Claude should call `search_emails`, then `get_email` for some of the
results. Open the tool calls: the snippets show `[California]` in brackets,
and the full emails are much longer and messier than the mock ones.

> Read email 1001.

The ids run from 1 to 1,000, so this should return the "No email found for
ID 1001." error, the same error your TODO 2 code gives for the mock data.

Now see what personal details reach Claude. Ask, one at a time:

> Search the emails for fax and read the first result. What phone numbers does it contain?

> Search the emails for pager and list the phone numbers in the top three results.

Claude reads the emails and repeats real people's phone numbers back to
you. Every one of them went from your computer to Anthropic. Step 5 stops
that; keep this chat open to compare.

## Try changing it

Real data shows where the tools fall short. Try a few questions of your
own, such as who wrote the most about a topic, or what happened in a given
month, and notice when Claude cannot answer well: search returns at most 10
results, and nothing lets it filter by date or sender. A later step works on
making search more useful to the model.

## If it does not work

- `ConfigurationError: EMAIL_MCP_DATA=enron but no database file exists at
  ...`: the file is not where the message says. Download it into `data/`,
  or start the server from the repository root.
- `ConfigurationError: ... lacks the emails and emails_fts tables`: the
  download saved a web page, not the database. Check that the file is about
  3.5 MB; if not, wait a while and download again.
- The test that reads the real database is skipped: `data/enron_sample.db`
  is missing or misnamed.
- Claude still answers about Alice, Bob and Carol: the server was not
  restarted with `EMAIL_MCP_DATA=enron`, or the chat started before the
  restart. Restart the server and start a new chat.
- Claude reports "Error executing tool get_email": run the step 4 tests to
  see the details.

## References

- [SQLite: URI filenames](https://www.sqlite.org/uri.html) and
  [Python: how to work with SQLite URIs](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris):
  read-only `mode=ro` connections.
- [Python: pathlib](https://docs.python.org/3/library/pathlib.html):
  `Path.resolve()` and `Path.as_uri()`.
- [CMU Enron email dataset](https://www.cs.cmu.edu/~enron/): where the
  emails come from.
- [curl manual](https://curl.se/docs/manpage.html): `-L` and `-o`.
