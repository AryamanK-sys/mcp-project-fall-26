# Local email data

Git ignores everything in this directory except this README and
`mock_emails.db`, the three synthetic emails that
[step 3](../docs/week2/step3-sqlite.md) reads. Other data files stay on each
contributor's machine.

## Enron sample database

`data/enron_sample.db` is a SQLite database of 1,000 real emails from the
public Enron corpus: 100 from each of 10 mailboxes, dated July 1999 to
March 2002. A teammate prepared it for the AI @ UCI MCP project from
[`corbt/enron-emails`](https://huggingface.co/datasets/corbt/enron-emails) on
Hugging Face, which is derived from the
[CMU Enron email dataset](https://www.cs.cmu.edu/~enron/).

The MCP server reads this database read-only when started with
`EMAIL_MCP_DATA=enron`; see
[step 4](../docs/week2/step4-enron.md). This page describes the database
itself.

**Getting it.** The database is not committed to this repository.
[Step 4](../docs/week2/step4-enron.md#get-the-database) shows how to
download it from Google Drive with one command and save it as
`data/enron_sample.db`. Nothing in it is redacted: emails can contain
passwords, phone numbers, home addresses and other personal details, which
[step 5](../docs/week2/step5-redaction.md) hides from the model. The build notebook (`preprocess.ipynb`) is not in
this repository, so the file cannot be regenerated here.

## Tables

| Table | Purpose |
|-------|---------|
| `emails` | One row per email. The table to query. |
| `emails_fts` | Full-text search index over `subject` and `body`. |
| `emails_fts_config`, `emails_fts_data`, `emails_fts_docsize`, `emails_fts_idx` | Internal storage SQLite creates for `emails_fts`. Never query or edit these directly. |

### `emails`

```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY, message_id TEXT, mailbox TEXT, mailboxes TEXT, folder TEXT,
    date TEXT, sender TEXT, to_addrs TEXT, cc_addrs TEXT, bcc_addrs TEXT,
    subject TEXT, body TEXT, tags TEXT)
```

| Column | Type | Meaning | Notes |
|--------|------|---------|-------|
| `id` | INTEGER | Sample number, 1 to 1,000 | Primary key. Use this to look up one email. |
| `message_id` | TEXT | Original `Message-ID` header from the source dataset | Unique. Looks like `<number.number.JavaMail.evans@thyme>`. |
| `mailbox` | TEXT | Mailbox this copy was taken from, such as `lay-k` | Always one of the 10 mailboxes below. |
| `mailboxes` | TEXT | Comma-separated list of every chosen mailbox holding this email | 41 emails appear in two mailboxes. |
| `folder` | TEXT | Original folder, such as `inbox`, `sent_items` or `all_documents` | `sent`, `_sent`, `sent_items` and `_sent_mail` mean the mailbox owner sent it. |
| `date` | TEXT | Send time in UTC, formatted `YYYY-MM-DD HH:MM:SS` | Sorts correctly as text. |
| `sender` | TEXT | Sender email address | Some addresses are oddly formatted, such as a doubled dot (`first..last@enron.com`). |
| `to_addrs` | TEXT | JSON list of To addresses, such as `["a@enron.com"]` | 50 emails have `[]`. 290 have two or more. |
| `cc_addrs` | TEXT | JSON list of Cc addresses | Non-empty in 258 emails. |
| `bcc_addrs` | TEXT | JSON list of Bcc addresses | Always identical to `cc_addrs`; the source data holds no real hidden recipients. |
| `subject` | TEXT | Subject line | Empty string (not NULL) in 87 emails. |
| `body` | TEXT | Message text, often including quoted replies and forwards | Cut at 20,000 characters; 6 emails reach the cut. Median length is 728 characters. |
| `tags` | TEXT | Comma-separated email types, such as `reply,sent` or `forwarded` | For writing evaluation questions; empty in 113 emails. Do not show it to the agent. |

No column is NULL. Address lists are stored as JSON text because SQLite has no
list type; decode them with `json.loads` in Python or `json_each` in SQL.

The table has no thread, attachment or recipient-name columns. Threads appear
only as quoted text inside `body`.

Tag values, with how many emails carry each: `reply` (320), `sent` (276),
`has_cc` (258), `has_bcc` (258), `multi_to` (213, three or more To addresses),
`forwarded` (210), `long` (138, body over 3,000 characters), `short` (125, body
under 150 characters), `no_subject` (87), `cross_mailbox` (41, in two mailboxes).
There is no `received` tag. To tell sent from received mail, use `folder`:
289 emails sit in a sent folder, but only 276 of them carry the `sent` tag.

### `emails_fts`

```sql
CREATE VIRTUAL TABLE emails_fts USING fts5(subject, body, content='emails', content_rowid='id')
```

An [FTS5](https://www.sqlite.org/fts5.html) full-text index. It is an
*external content* table: it stores only the search index and reads the text
from `emails`, with `emails_fts.rowid` equal to `emails.id`. Search it with
`MATCH`, then join back to `emails` for the other columns. Column 0 is
`subject` and column 1 is `body`, which matters for functions such as
`snippet()`.

## Mailboxes

Each mailbox has exactly 100 emails. Roles are approximate, taken from the
dataset card.

| Mailbox | Likely role |
|---------|-------------|
| `lay-k` | Chairman and CEO |
| `skilling-j` | President/COO, later CEO |
| `lavorato-j` | CEO, Enron Americas |
| `kitchen-l` | President, EnronOnline |
| `haedicke-m` | General Counsel |
| `perlingiere-d` | Contracts and legal staff |
| `steffes-j` | VP, Government Affairs |
| `arnold-j` | VP, gas trading |
| `lokay-m` | Pipeline commercial and admin |
| `dorland-c` | Junior trader or analyst |

## Opening the database read-only

Open the file read-only so a query or bug cannot change it. Python's built-in
`sqlite3` module does this with a URI filename and `mode=ro`.

```python
import json
import sqlite3

# "file:...?mode=ro" with uri=True opens the database read-only.
conn = sqlite3.connect("file:data/enron_sample.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row  # read columns by name: row["subject"]

row = conn.execute("SELECT * FROM emails WHERE id = ?", (1,)).fetchone()
to = json.loads(row["to_addrs"])  # JSON text -> Python list of addresses
conn.close()
```

Run it with the project environment from the repository root:

- macOS/Linux: `.venv/bin/python your_script.py`
- Windows: `.venv\Scripts\python your_script.py`

The `sqlite3` command-line shell works too, if it is installed. Use
`sqlite3 -readonly data/enron_sample.db`.

## Example queries

```sql
-- Emails per mailbox (expect 100 each).
SELECT mailbox, count(*) FROM emails GROUP BY mailbox;

-- Every distinct tag and how often it appears.
WITH RECURSIVE split(tag, rest) AS (
    SELECT '', tags || ',' FROM emails
    UNION ALL
    SELECT substr(rest, 1, instr(rest, ',') - 1), substr(rest, instr(rest, ',') + 1)
    FROM split WHERE rest <> ''
)
SELECT tag, count(*) FROM split WHERE tag <> '' GROUP BY tag ORDER BY 2 DESC;

-- Full-text search, best matches first, with a highlighted body snippet.
SELECT e.id, e.date, e.sender, e.subject,
       snippet(emails_fts, 1, '[', ']', '...', 24) AS snippet
FROM emails_fts
JOIN emails e ON e.id = emails_fts.rowid
WHERE emails_fts MATCH 'california'
ORDER BY rank
LIMIT 5;

-- One row per To recipient, by expanding the JSON list.
SELECT e.id, r.value AS recipient
FROM emails e, json_each(e.to_addrs) AS r
WHERE e.id = 1;
```

FTS5 query syntax accepts plain words (`budget`), quoted phrases
(`"master agreement"`), `AND`, `OR` and `NOT`. Punctuation such as hyphens or
colons can cause a syntax error; quote each word to avoid it.

## How the sample was built

From the dataset card: the 46,255 emails in the 10 mailboxes were cleaned by
keeping dates from 1998 to 2002, dropping 853 company-wide announcements,
merging duplicates that matched on sender, date, subject and body (29,757
remained), cutting bodies at 20,000 characters, and turning `[""]` address
placeholders into empty lists. Then 100 emails per mailbox were chosen to
cover forwards, replies, Cc, multiple recipients, sent and received mail,
empty subjects and very short or long bodies, with random seed 42.

The Hugging Face page did not show a licence or usage terms when checked on
2026-10-11.

## References

- [SQLite: FTS5 full-text search](https://www.sqlite.org/fts5.html): `MATCH`
  syntax, `rank`, `snippet()` and external content tables.
- [SQLite: JSON functions](https://www.sqlite.org/json1.html): `json_each`.
- [SQLite: ROWIDs and the INTEGER PRIMARY KEY](https://www.sqlite.org/lang_createtable.html#rowid):
  why `id` is the row's key.
- [SQLite: Datatypes](https://www.sqlite.org/datatype3.html): storage of
  `TEXT` and `INTEGER` columns.
- [SQLite: URI filenames](https://www.sqlite.org/uri.html) and
  [Python `sqlite3`: How to work with SQLite URIs](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris):
  read-only `mode=ro` connections.
- [SQLite: Command line shell](https://www.sqlite.org/cli.html): the
  `-readonly` option.

Small synthetic test fixtures belong under `tests/`, where they can be committed.
