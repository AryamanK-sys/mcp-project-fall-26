# Step 5: hide personal details

The Enron emails from step 4 are full of phone numbers and email addresses.
In this step you make the server hide them before they reach the model. You
write a function that finds them with **regular expressions** and replaces
them, and a store that passes every email through that function on its way
out.

Finish [step 4](step4-enron.md) first, including the download.

## What is new since step 4

- **Regular expressions.** A regular expression is a pattern that matches
  text, such as "three digits, a dash, three digits, a dash, four digits".
  Python's `re` module finds and replaces text that matches a pattern.
- **A wrapper store.** `RedactingStore` holds another store. It asks that
  store for results, redacts them, and returns them. The server and its
  tools do not change, and no tool can skip redaction.
- **A redaction setting.** `EMAIL_MCP_REDACT=on` wraps whichever store
  `EMAIL_MCP_DATA` chose; `off`, or not set, leaves it as it was.

## Why hide them

Everything your MCP server returns is sent to the model provider, such as
Anthropic, as part of your chat, so the safe habit is to send only what the
task needs. This is called **data minimization**, and it is a basic rule of
privacy-oriented design: each part of a system gets the data it needs to do
its job, and nothing extra. These emails are already public, but we apply
the rule anyway, as you would with private data.

In this project we treat the text of each email as private: every **phone
number** and email address in an email's subject or body counts as
**personally identifiable information (PII)**, and Claude should never
receive it. The server removes it before any result leaves your computer.

## What counts as personal

Redaction always trades privacy against usefulness. This step hides **email
addresses and phone numbers in the subject and body**. It keeps the
`sender`, `to` and `cc` fields, so the model can still say who wrote to
whom, and it keeps names in the text. Keep that choice in mind as you test:
you will see what it hides and what it lets through.

## Read the code

[`src/email_mcp/stores/redacting_store.py`](../../src/email_mcp/stores/redacting_store.py)
has three parts.

- `EMAIL_ADDRESS` and `PHONE_NUMBER` are compiled regular expressions. In a
  pattern, `\d` means a digit, `{3}` means "exactly three of the thing
  before", `[-. ]` means "one of these characters", `?` means "optional",
  `\(` matches a real parenthesis, and `\b` marks the edge of a word.
- `redact(text)` returns the text with every match replaced. It is not
  finished yet; that is TODO 4, part 1.
- `RedactingStore` wraps another store. `search()` is written for you: it
  copies each result with `dict(...)`, so the wrapped store's own data stays
  unchanged, and redacts the `subject` and `snippet`. `get()` is TODO 4,
  part 2.

[`open_store()`](../../src/email_mcp/stores/__init__.py) wraps the store in
a `RedactingStore` when `EMAIL_MCP_REDACT` is `on`, and stops the server if
it is anything other than `on` or `off`.

## Fill in TODO 4

TODO 4 has two parts in `src/email_mcp/stores/redacting_store.py`.

**Part 1: `redact(text)`.** Replace its `raise NotImplementedError(...)`
line. A compiled pattern's `.sub(replacement, text)` returns a copy of
`text` with every match replaced:

```python
EMAIL_ADDRESS.sub("[email]", "Write to a@example.com")  # "Write to [email]"
```

Replace email addresses with `[email]`, then phone numbers with `[phone]`,
and return the result.

**Part 2: `RedactingStore.get(email_id)`.** Replace its
`raise NotImplementedError(...)` line with code that does three things:

1. Ask the wrapped store for the email: `self._store.get(email_id)`.
2. If it returns `None`, return `None`, so the server still reports
   "No email found".
3. Otherwise, copy the email with `dict(...)`, pass its `subject` and `body`
   through `redact()`, and return the copy.

Use `search()`, just above it, as your model. Copying matters: the list
store from step 2 returns its own dictionaries, and changing them would
change the emails it holds.

## Check it works

Run the step 5 tests from the repository root.

macOS/Linux:

```sh
.venv/bin/python -m unittest discover -s tests -p "test_redacting_store.py" -v
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_redacting_store.py" -v
```

The tests call `redact()` and `RedactingStore` directly with text that has
addresses and phone numbers, check that text without them is unchanged, and
then start the server with `EMAIL_MCP_REDACT=on`. Until both parts are done,
they fail with:

```text
AssertionError: TODO 4 not done yet: fill in redact and RedactingStore.get in src/email_mcp/stores/redacting_store.py
```

Once both parts are right, all 13 tests pass. Then run every test, as in
the [README](../../README.md#run-the-tests); with TODOs 1 to 4 done, all of
them pass.

## Connect it to Claude

1. **Restart the server with redaction on.** Press **Ctrl+C** in the server
   terminal, then:

   macOS/Linux:

   ```sh
   export EMAIL_MCP_DATA=enron
   export EMAIL_MCP_REDACT=on
   .venv/bin/mcp run src/email_mcp/server.py:mcp --transport streamable-http
   ```

   Windows (PowerShell):

   ```powershell
   $env:EMAIL_MCP_DATA = "enron"
   $env:EMAIL_MCP_REDACT = "on"
   .\.venv\Scripts\mcp.exe run src/email_mcp/server.py:mcp --transport streamable-http
   ```

2. **Start a new chat** with Haiku and **AI Club MCP** enabled.

## Try it

Ask the same phone-number questions as in
[step 4](step4-enron.md#try-it), one at a time:

> Search the emails for fax and read the first result. What phone numbers does it contain?

> Search the emails for pager and list the phone numbers in the top three results.

The emails are the same, but Claude now sees `[phone]` wherever a number
was, and should say it cannot see them. Compare its answers with your
step 4 chat. Several pager results come from `no.address@enron.com`, the
address Enron used for company-wide announcements: that is the real
sender, not redaction, because this step keeps the `sender` field.

To check that the numbers never reached Claude, rather than taking its word
for it, ask:

> Quote, exactly as the tool returned it, every line of the first pager result that had a phone number.

The quoted lines show `[phone]` where the digits were. For proof that does
not depend on the model at all, click **Used AI Club MCP integration**
above Claude's answer and open a `get_email` call: the result is exactly
what your server sent, and it has no phone numbers in it.

Then look for what slips through:

> Read the first fax result again and list every other way it could identify a person.

Names, job titles and signatures are still there. Deciding how far to go is
part of designing a redaction step.

## Try changing it

1. **Catch more phone numbers.** `PHONE_NUMBER` misses numbers written with
   spaces only, such as `713 853 6161`, or with a slash, such as
   `713/853-6161`. Change the pattern to catch them, and add those examples
   to `test_hides_personal_details` in `tests/test_redacting_store.py`.
   Check that the dates and amounts in `test_keeps_other_text` still pass.
2. **Redact the address fields too.** Make `get()` also redact `sender`,
   `to` and `cc`, then ask Claude who sent an email. What can it still tell
   you?
3. **Search still sees the original text.** With redaction on, ask Claude
   to search for `713`. Results come back even though every number shows as
   `[phone]`: search runs on the database's original text, and only the
   results are redacted. What could someone learn from that?

The tests check the original behaviour, so changes 1 and 2 can make tests
fail. Update the tests to match what you decided.

## If it does not work

- `test_keeps_other_text` fails: your patterns match something they should
  not, such as a date. Check that you used `EMAIL_ADDRESS` and
  `PHONE_NUMBER` as given.
- The result still contains an address or a number: `redact()` returned
  before the second `.sub()`, or ran the second `.sub()` on the original
  `text` instead of the result of the first, which brings the addresses
  back.
- `test_get_leaves_the_wrapped_store_unchanged` fails: `get()` changed the
  wrapped store's dictionary. Copy it with `dict(...)` first.
- `TypeError: 'NoneType' object is not iterable` or
  `'NoneType' object is not subscriptable`: `get()` did not return `None`
  early for a missing id.
- `ConfigurationError: Unknown EMAIL_MCP_REDACT value`: use `on` or `off`.
- Claude still shows phone numbers: the server was not restarted with
  `EMAIL_MCP_REDACT=on`, or the chat started before the restart.

## References

- [UK Information Commissioner's Office: data minimisation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/):
  the principle, as data protection law states it.
- [Python: re](https://docs.python.org/3/library/re.html): pattern syntax
  and [`Pattern.sub`](https://docs.python.org/3/library/re.html#re.Pattern.sub).
- [Python: Regular expression HOWTO](https://docs.python.org/3/howto/regex.html):
  a gentler introduction.
- [regex101](https://regex101.com/): try a pattern against sample text and
  see what each part matches. Choose the Python flavour.
