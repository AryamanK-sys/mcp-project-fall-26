# Set up ngrok

Your MCP server runs on your computer, but Claude on the web runs on
Anthropic's servers, which cannot reach a program on your computer. ngrok
solves this: it gives your server a public HTTPS address and forwards every
request sent there to your computer.

```text
Claude on the web -> ngrok HTTPS address -> MCP server on your computer -> its tools
```

You set ngrok up once, in steps 1 to 4 below. After that, each step's guide
tells you which server to start, and you start the tunnel and build your
connector URL as in steps 6 and 7.

Run every command from the repository root. The commands are given for
macOS (which also work on Linux) and for Windows PowerShell. You need internet
access and the Python environment from the
[README development setup](../../README.md#development-setup). Macs with Intel
or Apple chips and Windows PCs (x64, or ARM with Windows 11) are supported.

## 1. Install the project dependencies

If you have not created `.venv` yet, do the
[README development setup](../../README.md#development-setup) first; it installs
everything ngrok needs, and you can go straight to step 2. If you already
have `.venv`, rerun the editable install to make sure the helper's
`python-dotenv` dependency is installed.

macOS/Linux:

```sh
.venv/bin/python -m pip install -e .
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

## 2. Create a free ngrok account

If you have never used ngrok, start here. If you already have an account,
sign in and go to step 3.

1. Open the [ngrok sign-up page](https://dashboard.ngrok.com/signup) and
   create an account. The free plan is enough for this project and needs no
   payment details.
2. Confirm your email address if ngrok asks you to.
3. Sign in. You land on the ngrok dashboard, the website where you manage
   your account. If it asks what you plan to use ngrok for, any answer works.

You do not need to download ngrok from the website: the helper in step 4
downloads it into this project for you.

Every ngrok account comes with a public address, such as
`https://jolly-otter-sunny.ngrok-free.app`. Your tunnel uses it
automatically.

## 3. Save your ngrok authtoken in .env

The authtoken is a password that tells ngrok the tunnel belongs to your
account. Treat it like a password: do not share it, post it or commit it.

1. Create your `.env` file by copying the template `.env.example`. Run this
   from the repository root.

   macOS/Linux:

   ```sh
   cp .env.example .env
   ```

   Windows (PowerShell):

   ```powershell
   Copy-Item .env.example .env
   ```

   Run it only once. If you already have a `.env` with your token in it,
   skip this command: it would replace your file with the empty template.

2. In the [ngrok dashboard](https://dashboard.ngrok.com/), open
   **Your Authtoken** and copy the token.

3. Open `.env` in your editor and paste your token after the `=`, then save:

   ```dotenv
   NGROK_AUTHTOKEN=your_token_here
   ```

Git ignores `.env`, so your token stays on your computer. `.env.example` is
the shared template and must stay empty.

## 4. Run the setup helper

macOS/Linux:

```sh
.venv/bin/python scripts/setup_ngrok.py
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe scripts/setup_ngrok.py
```

The helper reads `.env`, downloads the official ngrok program into
`.local/bin` and creates these files, which Git ignores:

| File | Purpose |
|---|---|
| `.local/ngrok.yml` | ngrok settings for this project, including your token |
| `.local/ngrok-policy.json` | A rule that lets the MCP server accept requests forwarded by ngrok |

When it works, it prints:

```text
ngrok is installed and the project-local configuration is valid.
```

This checks the settings file. It does not start a tunnel or check the token
with ngrok's service; step 6 does that. If you change the token in `.env`
later, run the helper again.

## 5. Start your MCP server over HTTP

In one terminal, start your server with the `mcp run` command from your
step's guide. For step 1 that is:

macOS/Linux:

```sh
.venv/bin/mcp run src/email_mcp/hello_server.py:mcp --transport streamable-http
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\mcp.exe run src/email_mcp/hello_server.py:mcp --transport streamable-http
```

When it is ready, the last line it prints is:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

The server is now at `http://127.0.0.1:8000/mcp`, an address only your own
computer can reach. Keep this terminal open. Only one server can use port 8000
at a time.

## 6. Start the ngrok tunnel

Open a second terminal at the repository root.

macOS/Linux:

```sh
.local/bin/ngrok http 8000 --config .local/ngrok.yml --traffic-policy-file .local/ngrok-policy.json
```

Windows (PowerShell):

```powershell
.\.local\bin\ngrok.exe http 8000 --config .local/ngrok.yml --traffic-policy-file .local/ngrok-policy.json
```

- `http 8000` forwards requests to your server's port.
- `--config` uses this project's settings, including your token.
- `--traffic-policy-file` applies the rule from step 4. Without it, the
  server refuses forwarded requests.

ngrok fills the terminal with status lines. Find the one that starts with
**Forwarding**. It looks like this, with your own address in it:

```text
Forwarding    https://jolly-otter-sunny.ngrok-free.app -> http://localhost:8000
```

Copy the HTTPS address on the left of the arrow, here
`https://jolly-otter-sunny.ngrok-free.app`. Yours is different. It may be a
few words like this one, or groups of letters and numbers such as
`https://1a2b-3c4d-5e6f.ngrok-free.app`, and it may end in `.ngrok-free.dev`
instead. All of these work.

## 7. Build your connector URL

ngrok's address does not end in `/mcp`, and you will not find `/mcp`
anywhere in ngrok's output. You add it yourself: type `/mcp` at the end of
the address you copied. The result is your **connector URL**:

```text
https://jolly-otter-sunny.ngrok-free.app/mcp
```

`/mcp` is the path where your MCP server listens. Without it, Claude reaches
your computer but not the server.

Add the connector URL to Claude as your step's guide describes. Keep both
terminals open while you chat.

## 8. Stop the tunnel when you are not using it

**Your ngrok address is public.** While the tunnel runs, anyone on the
internet who knows or guesses the address can call your server's tools.
Week 1 uses made-up emails, so nothing private can leak, but build the habit
now:

- Press **Ctrl+C** in the ngrok terminal as soon as you finish testing, and
  whenever you step away from your computer.
- Press **Ctrl+C** in the server terminal when you are done with the server.
- Never put real emails or other private data behind a tunnel.

## 9. Starting again later

Each time you come back, start the server (step 5) and the tunnel (step 6)
again, then compare the address ngrok shows with the URL in your Claude
connector. ngrok usually reuses your dev domain, but if the address is
different, the old connector no longer reaches your server. Claude does not
let you edit a connector's URL, so:

1. In Claude, remove the old connector, as in
   [Remove a connector](step1-first-server.md#remove-a-connector).
2. Add it again with the new connector URL (step 7), as in your step's guide.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `No module named dotenv` | Rerun step 1 using the `.venv` Python. |
| `Add NGROK_AUTHTOKEN to .env` | Save your token in the `.env` file at the repository root, then rerun the helper. |
| `Python could not verify the download's security certificate` | On macOS with Python from python.org: open the Python 3.14 folder in Applications, run `Install Certificates.command`, then rerun the helper. |
| `Could not download ... ngrok` | Check your internet connection and rerun the helper. |
| ngrok shows an error instead of a **Forwarding** line | Read the error ngrok prints; it usually includes a link that explains it. A wrong token (next row) is the most common cause. |
| ngrok rejects the token when the tunnel starts | Copy the authtoken from the dashboard into `.env` again, rerun the helper, then restart the tunnel. |
| `address already in use` when starting the server | Another server is using port 8000. Stop it with Ctrl+C in its terminal. |
| `421 Invalid Host header` | Start ngrok with the `--traffic-policy-file` argument shown in step 6. |
| Claude cannot reach the server | Check that both terminals are still running, and that the connector URL is ngrok's current address plus `/mcp` (steps 7 and 9). |

## Official references

- [ngrok CLI documentation](https://ngrok.com/docs/gateway/agent/cli): the
  `ngrok http` command.
- [ngrok domains](https://ngrok.com/docs/universal-gateway/domains/): the
  dev domain every account gets.
- [ngrok configuration file](https://ngrok.com/docs/gateway/agent/config/v3):
  the `ngrok.yml` format.
- [ngrok Host header replacement](https://ngrok.com/docs/gateway/traffic-policy/actions/add-headers#special-cases):
  the rule in `ngrok-policy.json`.
- [MCP Python SDK: running a server](https://py.sdk.modelcontextprotocol.io/run/):
  the `mcp run` command.

The `.env` helper and the `.local/` folder are this project's own choices,
not part of ngrok.
