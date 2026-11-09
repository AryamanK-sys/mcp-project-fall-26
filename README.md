# Email MCP project

AI @ UCI's MCP project. Over about five weeks you build an MCP server that
lets an AI model search and read emails, then your own agent that uses it.
Each step adds one idea, and each step's guide walks you through the code and
connecting it to Claude on the web.

## Steps

| Step | Week | What you build | Guide |
|------|------|----------------|-------|
| 1 | 1 | A first MCP server with one tool | [Step 1: your first MCP server](docs/week1/step1-first-server.md) |
| 2 | 1 | An email server with two tools that work together | [Step 2: email tools](docs/week1/step2-email-tools.md) |

New steps are added to this repository as the weeks go on.
[Save your work and get new weeks](#save-your-work-and-get-new-weeks) shows
how to get them.

## Get the code

You work in your own copy of this repository, called a **fork**. Your fork
lives on your GitHub account, so your work is backed up there, and you can
still pull each new week from the club's repository. You need a free
[GitHub account](https://github.com/signup).

1. **Fork the repository.** Open
   [aiclubatuci/mcp-project-fall-26](https://github.com/aiclubatuci/mcp-project-fall-26),
   click **Fork**, then **Create fork**. GitHub creates
   `https://github.com/<your-username>/mcp-project-fall-26`, where
   `<your-username>` is your GitHub username.

2. **Download your fork.** Replace `<your-username>` with your GitHub
   username. The first command creates a folder named `mcp-project-fall-26`;
   the second moves into it:

   ```sh
   git clone https://github.com/<your-username>/mcp-project-fall-26.git
   cd mcp-project-fall-26
   ```

3. **Link the club's repository.** This gives the club's repository the
   name `upstream`, so you can pull new weeks from it:

   ```sh
   git remote add upstream https://github.com/aiclubatuci/mcp-project-fall-26.git
   ```

   Check with `git remote -v`. `origin` is your fork, where you save your
   work; `upstream` is the club's repository, where new weeks come from.

4. **Tell Git who you are**, once per computer, if you have never made a Git
   commit before. Use your name and your GitHub account's email:

   ```sh
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```

The folder you cloned, which contains this README, is the
**repository root**. Run every command in these guides from there unless a
guide says otherwise. These Git commands are the same on macOS, Windows
PowerShell and Linux.

## Development setup

You need Python 3.14 and Git. Install Python from
[python.org](https://www.python.org/downloads/) if you do not have it. To
connect your server to Claude you also need a **free** Claude account and a
free ngrok account; [ngrok setup](docs/week1/ngrok-setup.md) walks you through
ngrok. Then run these commands from the repository root. They create a
private Python environment in `.venv` and install the MCP SDK and this
project into it.

macOS/Linux:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -e .
```

Windows (PowerShell):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

The packages this project needs are listed in `pyproject.toml`, so there
is no `requirements.txt`. `pip install -e .` installs those packages and also
this project's own `email_mcp` package, which the servers and tests import.
`-e` (editable) means changes you make under `src/` take effect without
reinstalling.

## Run the tests

macOS/Linux:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Until you fill in the TODOs in steps 1 and 2, the tests for those steps fail
with a message naming the TODO to finish; the other tests pass. Once both
TODOs are done, all tests should pass. Error lines printed while they run come
from calls that are meant to fail.

## Save your work and get new weeks

**Save your work to GitHub** whenever you finish a piece of work:

```sh
git commit -am "Finish TODO 1"
git push
```

`git commit -am` saves every file you changed that Git already tracks, with
the message in quotes. Git ignores `.env`, `.venv` and `.local/`, so your
token and downloads are never saved. `git push` copies your commits to your
fork on GitHub.

The first time you push, Git asks you to sign in to GitHub; your GitHub
password does not work here. On Windows, Git for Windows opens a browser
window to sign in. On macOS, the easiest way is
[GitHub CLI](https://cli.github.com/): install it, run `gh auth login`,
choose **HTTPS**, and answer **Yes** when it asks to authenticate Git with
your GitHub credentials. GitHub's
[credential guide](https://docs.github.com/en/get-started/git-basics/caching-your-github-credentials-in-git)
has the details.

**Get a new week** when the club announces one. Save your work first, then
bring in the club's changes and save them to your fork:

```sh
git commit -am "Finish week 1"
git fetch upstream
git merge --no-edit upstream/main
git push
```

If the first command says `nothing to commit`, your work is already saved;
carry on with the next one. Run these commands in the terminal rather than
using the **Sync fork** button on GitHub: the button updates only your fork
on GitHub, not the folder on your computer.

New weeks add new files and do not change the code you wrote, so the merge
normally finishes on its own. If Git reports a `CONFLICT`, run
`git merge --abort` to put everything back as it was, and ask for help. Do
not delete your folder.

## What is in this repository

```text
src/email_mcp/
  hello_server.py   Step 1: an MCP server with one count_letter tool
  server.py         Step 2: the email server and its two tools
  stores/
    list_store.py   Step 2: three made-up emails in a Python list
tests/              Tests that start each server and call its tools
scripts/
  setup_ngrok.py    Sets up ngrok so Claude on the web can reach your server
docs/week1/         Week 1 guides: steps 1 and 2, ngrok setup, screenshots
pyproject.toml      The project's name and the packages it needs
```
