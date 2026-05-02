# Getting Started

Three ways to run this demo — pick the one that fits your setup.

---

## Before you begin

You need the GitHub CLI for all three paths. Install it once:

```bash
# Windows
winget install --id GitHub.cli

# macOS
brew install gh

# Linux
sudo apt install gh
```

Verify:

```bash
gh --version
```

Then authenticate:

```bash
gh auth login
```

Follow the prompts — select **GitHub.com**, **HTTPS**, and authenticate via browser.

---

## Path A — Clone and run locally

**Best for:** running the demo on your own machine, modifying the code, experimenting offline.

**Time:** ~5 minutes

```bash
# 1. Clone the repo
gh repo clone rafdesouza/whos-in-charge-agentic-ai

# 2. Move into the project
cd whos-in-charge-agentic-ai

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

The app starts in **demo mode** — pre-computed decisions, no credentials needed.
To enable a live model, copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

See `.env.example` for the full list of options (Ollama or Azure OpenAI).

---

## Path B — GitHub Codespaces

**Best for:** zero local setup. Runs entirely in the cloud, accessible from any browser.
No Python, no pip, no ports to manage — the environment is pre-configured.

**Time:** ~2 minutes

```bash
# 1. Create the Codespace
gh codespace create --repo rafdesouza/whos-in-charge-agentic-ai

# 2. Open it in VS Code
gh codespace code
```

Inside the Codespace terminal:

```bash
# Dependencies were installed automatically on startup (postCreateCommand)
# Just run:
streamlit run app.py --server.headless true
```

Codespaces detects port 8501 and opens the app in your browser automatically.

> **No VS Code installed?**
> Open the Codespace in a browser instead:
> ```bash
> gh codespace code --web
> ```

> **Note on credentials:** to run in live AI mode inside a Codespace, add your
> Azure OpenAI or Ollama connection details as Codespace secrets via:
> ```bash
> gh secret set AZURE_OPENAI_API_KEY --app codespaces
> ```
> The app reads them as environment variables at startup.

---

## Path C — Fork, customise, run your own version

**Best for:** adapting the demo to your own domain — swap the building for a hospital,
data centre, warehouse, or any environment where humans and AI share decision-making.

**Time:** ~10 minutes to fork and run; as long as you like to customise.

```bash
# 1. Fork and clone in one command
gh repo fork rafdesouza/whos-in-charge-agentic-ai --clone

# 2. Move into the project
cd whos-in-charge-agentic-ai

# 3. Install dependencies
pip install -r requirements.txt
```

### Customise the domain

**Change the events** — `agent/events.py`

Replace or extend `SARAHS_DAY` with events from your domain:

```python
BuildingEvent(
    id="EVT-011",
    time="09:30",
    category=EventCategory.SECURITY,
    description="Unusual access pattern detected — server room, three attempts",
    location="Level 3 Server Room",
    severity=EventSeverity.HIGH,
    context={"attempts": 3, "user_id": "unknown", "time_gap": "4 minutes"},
)
```

**Change the agent's domain knowledge** — `agent/building_agent.py`

Replace the `SYSTEM_PROMPT` context to fit your environment:

```python
SYSTEM_PROMPT = """You are the AI operations agent for a regional hospital in Perth WA.
Your role: assess incoming clinical and facility events and route them based on
your confidence in the right course of action...
"""
```

The confidence scoring logic (`0–49 escalate`, `50–79 auto+log`, `80–100 automate`)
works unchanged across any domain.

```bash
# 4. Run your customised version
streamlit run app.py

# 5. Push to your fork when you're happy
git add .
git commit -m "adapt to my domain"
git push
```

Your fork is now at `github.com/<your-username>/whos-in-charge-agentic-ai`.

---

## Useful `gh` commands

```bash
# View the repo summary and README
gh repo view rafdesouza/whos-in-charge-agentic-ai

# Open the repo in your browser
gh repo view rafdesouza/whos-in-charge-agentic-ai --web

# List your Codespaces
gh codespace list

# Stop a running Codespace
gh codespace stop

# Delete a Codespace when done
gh codespace delete
```

---

## Troubleshooting

**`streamlit: command not found`**
Streamlit installed into a Python environment that isn't on your PATH.
Try: `python -m streamlit run app.py`

**Port 8501 already in use**
Another Streamlit instance is running. Either stop it or run on a different port:
`streamlit run app.py --server.port 8502`

**Codespace takes longer than expected to start**
The `postCreateCommand` is installing dependencies — this runs once on first start.
Subsequent starts are instant.

**Demo mode showing instead of live AI**
Check that your `.env` file exists and has the correct values.
The app prints the active mode ("Ollama", "Azure OpenAI", or "Demo") on the home page.
