# Who's Really in Charge?
### The People Puzzle Behind Agentic AI

> *"The danger isn't sentience. It's losing control through design laziness."*

A working demonstration of **AI-in-the-Loop** design — a building management agent
that uses LLM-generated confidence scores to route decisions: automate what it knows,
escalate what it doesn't, and preserve human expertise for what genuinely needs it.

Companion repository for the talk by **Rafael Souza** at the
Microsoft Azure Data Analytics Meetup — Perth, Western Australia.

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

## Setup

```bash
git clone https://github.com/rafdesouza/whos-in-charge-agentic-ai.git
cd whos-in-charge-agentic-ai
pip install -r requirements.txt
streamlit run app.py
```

Runs immediately in **demo mode** — pre-computed decisions, no credentials needed.

### Backends

| Mode | How to enable |
|---|---|
| **Demo** (default) | Nothing — just run |
| **Ollama** (local, offline) | `LOCAL_MODEL=llama3.2` in `.env` — requires [ollama.com](https://ollama.com) |
| **Azure OpenAI** (cloud) | Azure credentials in `.env` — see `.env.example` |

```bash
cp .env.example .env   # fill in your values
```

**Recommended Ollama models:**

| Model | Size | Notes |
|---|---|---|
| `llama3.2` | 2 GB | Fastest, runs on any laptop |
| `mistral` | 4 GB | Most reliable structured output |
| `qwen2.5:7b` | 5 GB | Strong reasoning |
| `phi4` | 9 GB | Best quality — Microsoft model |

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

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — LangChain LCEL chain, structured output, confidence scoring design, extending the demo, production considerations
- [`docs/FUNCTIONAL_DESIGN.md`](docs/FUNCTIONAL_DESIGN.md) — Component-by-component functional design with team skill profiles mapped to each part of the system

---

## About

**Rafael Souza** — AI Solution Architect, Accenture / Avanade

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
