# Who's Really in Charge?
### The People Puzzle Behind Agentic AI

> *"The danger isn't sentience. It's losing control through design laziness."*

This repository accompanies the talk **"Who's Really in Charge? The People Puzzle Behind Agentic AI"**
by Rafael Souza, presented at the Microsoft Azure Data Analytics Meetup — Perth, Western Australia.

It is a working demonstration of **AI-in-the-Loop** design: a building management agent that uses
confidence scoring to decide what to automate and what to escalate to a human expert.

---

## The Concept

Meet Sarah. She's a facilities manager for a 20-storey office tower in Perth's CBD.

She has deep domain expertise. She knows the building. She knows her tenants.

But she has **no visibility and no bandwidth**. Every event — routine or critical — lands on her desk.
Her expertise is consumed by noise.

The common response is to "add AI" and have Sarah validate the AI's decisions. But this is the trap:

| Human-in-the-Loop | AI-in-the-Loop |
|---|---|
| AI makes decisions | AI handles routine with confidence |
| Human validates every one | AI flags uncertainty to human |
| Human anchors to AI framing | Human decides on genuine edge cases |
| Expertise erodes at scale | Expertise stays sharp |

The question isn't *"should AI assist humans?"* — it's **"which decisions genuinely need human judgment?"**

---

## The Core Mechanism: Confidence Scoring

The agent doesn't just decide. It knows what it doesn't know.

| Confidence | Routing | Example |
|---|---|---|
| 80–100 | Automated | Lift routing — morning peak (94%) |
| 50–79 | Automated + logged | Recurring sensor fault — monitoring (58%) |
| 0–49 | Escalated to Sarah with full context | Unverified contractor, server room, 23:30 (12%) |

When Sarah decides on an escalated case, her decision feeds back into the agent — continuous improvement,
without replacing her judgment.

---

## Demo Structure

```
app.py                          Home page — overview and setup status
pages/
  1_Sarahs_Reactive_Day.py      The problem: every event goes to Sarah
  2_AI_In_The_Loop.py           The solution: confidence-based routing, live agent
  3_Paradigm_Comparison.py      Side-by-side: Human-in-the-Loop vs AI-in-the-Loop
agent/
  events.py                     Building event types and Sarah's story (10 events)
  building_agent.py             LangChain + Azure OpenAI agent with structured output
  feedback.py                   Logs Sarah's decisions for the feedback loop
```

The demo works in two modes:
- **Demo mode** (default): pre-computed decisions load instantly, no credentials needed
- **Live mode**: connects to Azure OpenAI for real-time AI assessment

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/whos-in-charge-agentic-ai.git
cd whos-in-charge-agentic-ai
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI (optional — demo mode works without this)

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

### 3. Run

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## The Three Demo Pages

### Page 1 — Sarah's Reactive Day
Step through all 10 building events. Every single one lands on Sarah's desk.
Watch the queue grow. At the end, see how many events actually needed her expertise.

### Page 2 — AI-in-the-Loop
Process the same events through the AI agent. Each event receives a confidence score.
- High confidence: automated, logged, Sarah not involved
- Low confidence: escalated with full context, agent recommendation, and space for Sarah's decision
- Sarah's responses are logged and feed back into the system

### Page 3 — Paradigm Comparison
Side-by-side view of both paradigms processing the same event stream.
Confidence chart, routing table, and the five questions to ask before building your next agentic system.

---

## Technology

- **Python 3.10+**
- **LangChain** — agent orchestration and structured output
- **Azure OpenAI** — GPT-4o for event assessment (demo mode available without credentials)
- **Streamlit** — interactive demo UI
- **Pydantic** — typed agent decision model

---

## Key Ideas from the Talk

**Cognitive anchoring**: Humans reviewing AI output stop thinking independently.
The better the AI, the worse this gets.

**Decision fatigue at scale**: 10 reviews is fine. 10,000 is not.
Oversight collapses. Humans become rubber stamps.

**Expertise atrophy**: When humans validate instead of decide, their skills degrade.
The safety net slowly dissolves.

**The Ghost in the Machine**: The danger isn't that AI becomes sentient.
It's that humans lose control through design laziness — building systems where
they technically approve every decision but genuinely control none of them.

---

## The Five Questions

Before building your next agentic AI system:

1. Are humans **making decisions** — or just validating them?
2. Will expertise **stay sharp** — or erode?
3. What happens when the system encounters something it **wasn't trained for**?
4. Who's **actually in control** if something goes wrong?
5. What **diverse perspectives** are missing from the team that built this?

---

## About

**Rafael Souza** — AI Solution Architect, Accenture / Avanade

Background in physics, flow modelling, and geophysics — pivoted into AI solutioning
and delivery. Works on agentic AI design, human-AI teaming, and responsible AI
implementation for enterprise clients.

*Developed with the assistance of [Claude](https://claude.ai) (Anthropic)*

---

## Slides

The original talk slides will be added to this repository after the event.
