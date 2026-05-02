# Who's Really in Charge?
### The People Puzzle Behind Agentic AI

> *"The danger isn't sentience. It's losing control through design laziness."*

A working demonstration of **AI-in-the-Loop** design — a building management agent
that uses LLM-generated confidence scores to route decisions: automate what it knows,
escalate what it doesn't, and preserve human expertise for what genuinely needs it.

Companion repository for the talk by **Rafael Souza** at the
Microsoft Azure Data Analytics Meetup — Perth, Western Australia.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/rafdesouza/whos-in-charge-agentic-ai)

---

## The Concept

Meet Sarah. She's a facilities manager for a 20-storey office tower in Perth's CBD.
She has deep domain expertise — but no visibility and no bandwidth.
Every event, routine or critical, lands on her desk. Her expertise is consumed by noise.

The common response is to "add AI" and have Sarah validate AI decisions. That's the trap:

| Human-in-the-Loop | AI-in-the-Loop |
|---|---|
| AI makes decisions | AI handles routine with confidence |
| Human validates every one | AI flags uncertainty to human |
| Human anchors to AI framing | Human decides on genuine edge cases |
| Expertise erodes at scale | Expertise stays sharp |

The right question isn't *"should AI assist humans?"* — it's **"which decisions genuinely need human judgment?"**

The core mechanism is **confidence scoring**: the agent knows what it doesn't know.

| Confidence | Routing | Example from the demo |
|---|---|---|
| 80–100 | Automated | Morning peak lift routing — 94% |
| 50–79 | Automated + logged | Recurring sensor fault — 58% |
| 0–49 | Escalated to Sarah with full context | Unverified contractor, server room — 12% |

---

## Run the Demo

Three ways to get started — pick the one that fits your setup.

---

### Prerequisites

Install these before starting. The table shows which options need each one.

| Prerequisite | Option 1 | Option 2 | Option 3 | Download |
|---|:---:|:---:|:---:|---|
| **GitHub account** (free) | ✓ | ✓ | ✓ | [github.com/signup](https://github.com/signup) |
| **GitHub CLI** (`gh`) | ✓ | ✓ | ✓ | [cli.github.com](https://cli.github.com) |
| **Python 3.10+** | ✓ | — | ✓ | [python.org/downloads](https://www.python.org/downloads) |
| **Git** | ✓ | — | ✓ | [git-scm.com](https://git-scm.com/downloads) |
| **VS Code** (optional) | — | ✓ | — | [code.visualstudio.com](https://code.visualstudio.com) |

> Option 2 (Codespaces) runs entirely in the cloud — no Python or Git needed locally.
> VS Code is optional; the Codespace can also open in the browser.

**Install GitHub CLI**

Open a terminal (PowerShell on Windows, Terminal on macOS/Linux):

```bash
# Windows
winget install --id GitHub.cli

# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh
```

Close and reopen the terminal after installing, then verify:

```bash
gh --version
# expected: gh version 2.x.x
```

**Install Python** (Option 1 and 3 only)

Download the installer from [python.org/downloads](https://www.python.org/downloads).
On Windows, check **"Add Python to PATH"** during installation.

Verify:

```bash
python --version
# expected: Python 3.10.x or higher
```

**Install Git** (Option 1 and 3 only)

Download from [git-scm.com](https://git-scm.com/downloads) and run the installer.

Verify:

```bash
git --version
# expected: git version 2.x.x
```

Once all prerequisites are in place, pick your option below.

---

### Option 1 — Clone and run locally

**What you need:** Python 3.10+, Git, GitHub CLI — all installed above.

**Step 1 — Install the GitHub CLI**

Open a terminal (PowerShell on Windows, Terminal on macOS/Linux) and run:

```bash
# Windows
winget install --id GitHub.cli

# macOS
brew install gh
```

Close and reopen the terminal, then confirm it worked:

```bash
gh --version
# expected output: gh version 2.x.x
```

**Step 2 — Authenticate with GitHub**

```bash
gh auth login
```

- Select **GitHub.com**
- Select **HTTPS**
- Select **Login with a web browser**
- Copy the one-time code shown, press Enter — your browser opens
- Paste the code, authorise the app, return to the terminal
- You should see: `Logged in as <your-username>`

**Step 3 — Clone the repo**

```bash
gh repo clone rafdesouza/whos-in-charge-agentic-ai
```

You will see the repo being cloned into a new folder called `whos-in-charge-agentic-ai`.

**Step 4 — Move into the project folder**

```bash
cd whos-in-charge-agentic-ai
```

**Step 5 — Install dependencies**

```bash
pip install -r requirements.txt
```

This installs Streamlit, LangChain, and everything else the app needs.
It takes 1–2 minutes on a fresh machine.

**Step 6 — Run the app**

```bash
streamlit run app.py
```

Your browser opens automatically at `http://localhost:8501`.
The app starts in **demo mode** — pre-computed decisions, no credentials needed.
Use the sidebar to navigate between the three demo pages.

To stop the app, press `Ctrl + C` in the terminal.

---

### Option 2 — GitHub Codespaces (zero local setup)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/rafdesouza/whos-in-charge-agentic-ai)

**What you need:** A GitHub account. That's it.
No Python, no pip, no local ports — the environment runs entirely in the cloud.

Click the button above — or follow the steps below if you prefer the terminal.

**Step 1 — Create the Codespace**

```bash
gh codespace create --repo rafdesouza/whos-in-charge-agentic-ai
```

GitHub spins up a cloud machine pre-configured with Python 3.11.
You will be prompted to choose a machine type — the default (2-core) is fine.
The Codespace name is printed when it's ready (e.g. `fuzzy-space-potato-abc123`).

**Step 2 — Open it in VS Code**

```bash
gh codespace code
```

If you have VS Code installed, it opens automatically connected to the Codespace.
If not, add `--web` to open it in the browser:

```bash
gh codespace code --web
```

**Step 3 — Run the app**

In the VS Code terminal (`` Ctrl + ` `` to open it), type:

```bash
streamlit run app.py --server.headless true
```

VS Code detects port 8501 and shows a pop-up: **"Open in Browser"** — click it.
The app opens in your browser. Done.

**Step 4 — Clean up when finished**

```bash
gh codespace delete
```

---

### Option 3 — Fork and adapt to your own domain

The agent's confidence scoring logic is domain-agnostic. Swap out the building events
and system prompt, and it works for a hospital, data centre, warehouse — any environment
where humans and AI share decision-making.

**Step 1 — Fork and clone in one command**

```bash
gh repo fork rafdesouza/whos-in-charge-agentic-ai --clone
```

This creates a copy under your own GitHub account and clones it locally.

**Step 2 — Move into the project folder**

```bash
cd whos-in-charge-agentic-ai
```

**Step 3 — Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 4 — Swap in your domain events**

Open `agent/events.py` in any editor. Replace or add entries in `SARAHS_DAY`:

```python
BuildingEvent(
    id="EVT-011",
    time="09:30",
    category=EventCategory.SECURITY,
    description="Unusual login pattern — admin account, three failed attempts",
    location="Cloud infrastructure",
    severity=EventSeverity.HIGH,
    context={"attempts": 3, "source_ip": "unknown", "account": "svc-admin"},
)
```

**Step 5 — Update the agent's domain knowledge**

Open `agent/building_agent.py`. Find `SYSTEM_PROMPT` near the top and replace the
building management context with your own domain. The confidence scoring bands
(`0–49 escalate`, `50–79 auto+log`, `80–100 automate`) need no changes.

**Step 6 — Run your version**

```bash
streamlit run app.py
```

**Step 7 — Push to your fork**

```bash
git add .
git commit -m "adapt to my domain"
git push
```

Your customised version is now live at `github.com/<your-username>/whos-in-charge-agentic-ai`.

---

### Connect a live AI model (optional for all options)

By default the demo uses pre-computed decisions — it works offline, instantly, with no
credentials. To connect a real model:

**Step 1 — Copy the environment template**

```bash
# macOS / Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

**Step 2 — Open `.env` in any text editor and fill in your values**

To use a **local model via Ollama:**

1. Install Ollama from [ollama.com](https://ollama.com)
2. Open a new terminal and run: `ollama pull llama3.2`
3. In `.env`, set: `LOCAL_MODEL=llama3.2`

To use **Azure OpenAI:**

In `.env`, set:
```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

**Step 3 — Restart the app**

```bash
streamlit run app.py
```

The home page shows which mode is active: **Ollama**, **Azure OpenAI**, or **Demo**.

**Recommended Ollama models:**

| Model | Download size | Notes |
|---|---|---|
| `llama3.2` | 2 GB | Fastest, runs on any laptop |
| `mistral` | 4 GB | Most reliable structured output |
| `qwen2.5:7b` | 5 GB | Strong reasoning |
| `phi4` | 9 GB | Best quality |

---

## The Three Demo Pages

**1 — Sarah's Reactive Day**
Step through all 10 building events. Every one lands on Sarah's desk with no triage.
See how many genuinely needed her expertise.

**2 — AI-in-the-Loop**
The same events through the agent. Each receives a confidence score and is routed:
automated silently, or escalated to Sarah with full context and a recommended action.
Sarah's decisions are logged and feed back into the system.

**3 — Paradigm Comparison**
Side-by-side: Human-in-the-Loop vs AI-in-the-Loop processing the same event stream.
Confidence chart, event-by-event routing table, and the five questions.

---

## Project Structure

```
agent/
  events.py             BuildingEvent schema, 10 curated demo events
  building_agent.py     LangChain LCEL chain, confidence scoring, backend switching
  feedback.py           Logs Sarah's decisions for the feedback loop

pages/
  1_Sarahs_Reactive_Day.py    The problem — no AI triage
  2_AI_In_The_Loop.py         The solution — confidence-based routing
  3_Paradigm_Comparison.py    Side-by-side comparison

app.py                  Home page and setup status
docs/
  ARCHITECTURE.md       Technical deep-dive — chain design, schema, extending, production path
  FUNCTIONAL_DESIGN.md  Component-by-component design with team skill mapping
```

---

## The Five Questions

Before building your next agentic system:

1. Are humans **making decisions** — or just validating them?
2. Will expertise **stay sharp** — or erode over time?
3. What happens when the system encounters something it **wasn't trained for**?
4. Who's **actually in control** if something goes wrong?
5. What **diverse perspectives** are missing from the team that built this?

---

## Documentation

- [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) — Full setup guide with troubleshooting
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — LangChain LCEL chain, structured output, confidence scoring design, extending the demo, production considerations
- [`docs/FUNCTIONAL_DESIGN.md`](docs/FUNCTIONAL_DESIGN.md) — Component-by-component functional design with team skill profiles mapped to each part of the system

---

## About

**Rafael Souza** — AI Solution Architect

Background in physics, flow modelling, and geophysics — pivoted into AI solutioning
and delivery. Works on agentic AI design, human-AI teaming, and responsible AI
implementation for enterprise clients.

*Developed with the assistance of [Claude](https://claude.ai) (Anthropic)*

---

## Slides

Talk slides will be added after the event.

## Further Reading

- [LangChain LCEL docs](https://python.langchain.com/docs/concepts/lcel/)
- [Structured output with LangChain](https://python.langchain.com/docs/concepts/structured_outputs/)
- [Ollama model library](https://ollama.com/library)
- [Azure OpenAI structured outputs](https://learn.microsoft.com/azure/ai-services/openai/how-to/structured-outputs)
