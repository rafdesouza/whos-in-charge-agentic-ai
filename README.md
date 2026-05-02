# Who's Really in Charge?
### The People Puzzle Behind Agentic AI

> *"The danger isn't sentience. It's losing control through design laziness."*

A working demonstration of **AI-in-the-Loop** design — a building management agent
that uses LLM-generated confidence scores to route decisions: automate what it knows,
escalate what it doesn't, and preserve human expertise for what genuinely needs it.

Companion repository for the talk by **Rafael Souza** at the
Microsoft Azure Data Analytics Meetup — Perth, Western Australia.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  BUILDING EVENT STREAM                   │
│  sensors · access logs · maintenance requests           │
└────────────────────────┬────────────────────────────────┘
                         │  BuildingEvent(id, category,
                         │    description, severity, context)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    BUILDING AGENT                        │
│                                                          │
│   ChatPromptTemplate (system + user)                     │
│              │                                           │
│              ▼                                           │
│   BaseChatModel  ◄── AzureChatOpenAI  (cloud)            │
│   (runtime)      ◄── ChatOllama       (local)            │
│              │                                           │
│              ▼  .with_structured_output(AgentDecision)   │
│   AgentDecision                                          │
│     • confidence: int   (0–100)                          │
│     • auto_handle: bool                                  │
│     • reasoning: str                                     │
│     • recommended_action: str                            │
│     • escalation_context: str                            │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
   confidence ≥ 75       confidence < 50
        │                     │
        ▼                     ▼
┌───────────────┐   ┌─────────────────────────┐
│  AUTOMATED    │   │  SARAH'S CONSOLE         │
│  ACTIONS      │   │  • event + context       │
│               │   │  • agent recommendation  │
│  logged,      │   │  • decision form         │
│  no human     │   └────────────┬────────────┘
│  required     │                │
└───────────────┘                ▼
                      ┌─────────────────────┐
                      │   FEEDBACK LOG      │
                      │   feedback_log.json │
                      │                     │
                      │  event_id           │
                      │  agent_confidence   │
                      │  agent_recommendation│
                      │  sarah_decision     │
                      │  sarah_accepted (bool)│
                      └─────────────────────┘
```

---

## How It Works

### 1. LangChain LCEL chain

The core is a single LangChain Expression Language chain:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

llm = AzureChatOpenAI(model="gpt-4o", temperature=0.1)

chain = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", USER_TEMPLATE),
]) | llm.with_structured_output(AgentDecision)

decision: AgentDecision = chain.invoke({
    "event_id": event.id,
    "description": event.description,
    ...
})
```

The same chain works unchanged across Azure OpenAI and Ollama — only `_build_llm()`
changes based on the active backend. See [`agent/building_agent.py`](agent/building_agent.py).

### 2. Structured output — not prompt-hacking

Instead of parsing free-text LLM responses, the agent uses Pydantic-enforced structured
output via LangChain's `.with_structured_output()`. The model returns a valid
`AgentDecision` object or raises — no brittle regex, no JSON extraction logic.

```python
class AgentDecision(BaseModel):
    action_summary: str   = Field(description="One-line summary of recommended action")
    confidence: int       = Field(description="0–100. Higher = more routine, safer to automate", ge=0, le=100)
    reasoning: str        = Field(description="2–3 sentences explaining the confidence level")
    recommended_action: str = Field(description="Step-by-step actions to take")
    auto_handle: bool     = Field(description="True if confidence ≥ 75")
    escalation_context: str = Field(description="Context for Sarah's decision. Empty if auto-handling.")
```

Under the hood, LangChain translates this to tool/function calling for OpenAI-compatible
models, and JSON mode for Ollama. The calling code sees only `AgentDecision`.

### 3. Confidence is LLM-reasoned, not rule-based

The confidence score isn't computed by a classifier or rules engine — it's produced by
the LLM itself, guided by system prompt instructions that define what makes a decision
high- vs low-confidence. This means the same prompt works across domains by changing
the domain framing alone.

The system prompt sets the scoring contract:

```
CONFIDENCE SCORING:
- 80–100: Routine, well-defined, clear precedent → AUTOMATE
- 50–79: Standard but worth human awareness → AUTOMATE + LOG
- 0–49: Novel, high-stakes, ambiguous, or cascading → ESCALATE

CRITICAL PRINCIPLE: You know what you don't know.
An unnecessary escalation is better than a wrong auto-decision.
```

The LLM reasons about novelty, consequence, and ambiguity — not pattern matching.

### 4. Model-agnostic backend

```python
def get_mode() -> str:           # 'ollama' | 'azure' | 'demo'
    if os.getenv("LOCAL_MODEL"):
        return "ollama"
    if os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"):
        return "azure"
    return "demo"

def _build_llm() -> BaseChatModel:
    if get_mode() == "ollama":
        return ChatOllama(model=os.getenv("LOCAL_MODEL"), temperature=0.1)
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        temperature=0.1,
    )
```

`BaseChatModel` is the type contract. Swap the backend; the chain doesn't change.

### 5. Feedback loop

Every decision Sarah makes on an escalated event is persisted:

```json
{
  "event_id": "EVT-007",
  "agent_confidence": 12,
  "agent_recommendation": "Deny access pending verification...",
  "sarah_decision": "Escalated to IT security team.",
  "sarah_accepted_recommendation": false,
  "timestamp": "2026-05-01T14:22:11"
}
```

In this demo, `feedback_log.json` accumulates locally. In a production system this
data is the training signal — RLHF, preference pairs, fine-tuning datasets, or RAG
retrieval context for future similar events.

---

## Setup

```bash
git clone https://github.com/rafdesouza/whos-in-charge-agentic-ai.git
cd whos-in-charge-agentic-ai
pip install -r requirements.txt
streamlit run app.py          # demo mode, no credentials needed
```

### Backends

| Mode | Config | Notes |
|---|---|---|
| **Demo** | nothing | Pre-computed decisions, instant, fully offline |
| **Ollama** | `LOCAL_MODEL=llama3.2` in `.env` | Fully offline, requires [ollama.com](https://ollama.com) |
| **Azure OpenAI** | Azure vars in `.env` | Cloud, requires Azure subscription |

```bash
cp .env.example .env   # then edit with your values
```

**Ollama model recommendations:**

| Model | Size | Structured output | Notes |
|---|---|---|---|
| `llama3.2` | 2 GB | Good | Best for laptops, fastest |
| `mistral` | 4 GB | Excellent | Most reliable structured output |
| `qwen2.5:7b` | 5 GB | Excellent | Strong reasoning |
| `phi4` | 9 GB | Good | Microsoft model — relevant for this event |

```bash
ollama pull llama3.2   # then set LOCAL_MODEL=llama3.2 in .env
```

---

## Project Structure

```
agent/
  events.py           BuildingEvent dataclass, EventCategory/Severity enums,
                      SARAHS_DAY list (10 curated events from the talk)
  building_agent.py   AgentDecision schema, LCEL chain, backend switching,
                      pre-computed demo decisions
  feedback.py         FeedbackEntry dataclass, log_decision(), acceptance_rate()

pages/
  1_Sarahs_Reactive_Day.py    Event-by-event demo of the problem (no AI triage)
  2_AI_In_The_Loop.py         Live agent demo — confidence scoring + routing
  3_Paradigm_Comparison.py    Static side-by-side comparison with Plotly chart

app.py                Home page, setup status, backend mode indicator
docs/
  ARCHITECTURE.md     Full technical deep-dive
```

---

## Extending

### Add a new building event

```python
# agent/events.py
from agent.events import BuildingEvent, EventCategory, EventSeverity

SARAHS_DAY.append(BuildingEvent(
    id="EVT-011",
    time="15:30",
    category=EventCategory.SECURITY,
    description="Tailgating detected at Level 6 access point",
    location="Level 6 North Entry",
    severity=EventSeverity.MEDIUM,
    context={"camera_id": "CAM-6N-01", "persons_detected": 3, "badge_swipes": 1},
))
```

If running in demo mode, add a matching entry to `_DEMO_DECISIONS` in
`building_agent.py`. In live mode, the LLM assesses it automatically.

### Tune the confidence thresholds

Thresholds are applied in `pages/2_AI_In_The_Loop.py`:

```python
def confidence_label(score: int) -> str:
    if score >= 75:   return "AUTO"
    if score >= 50:   return "AUTO + LOG"
    return "ESCALATE"
```

And in the system prompt in `agent/building_agent.py`. Both should be updated
together to stay consistent. Lower the escalation threshold to be more conservative;
raise it to automate more aggressively.

### Plug in a real sensor stream

Replace `SARAHS_DAY` with a live generator:

```python
def stream_events(source: str) -> Iterator[BuildingEvent]:
    # e.g. Kafka, Azure Event Hub, MQTT, REST polling
    for raw in kafka_consumer(source):
        yield BuildingEvent(
            id=raw["id"],
            category=EventCategory(raw["type"]),
            ...
        )
```

The agent pipeline is stateless per event — no changes needed downstream.

### Add a new backend

Any LangChain-compatible `BaseChatModel` works:

```python
# Example: Google Vertex AI
from langchain_google_vertexai import ChatVertexAI

def _build_llm() -> BaseChatModel:
    if os.getenv("USE_VERTEX"):
        return ChatVertexAI(model="gemini-1.5-pro", temperature=0.1)
    ...
```

---

## Design Decisions

**1. LLM-generated confidence, not a classifier.**
A classifier requires labelled training data and retraining when the domain changes.
An LLM with a well-designed system prompt generalises across event types from day one.
The trade-off: non-determinism. The same event may score differently across runs.
For production, cache scores per event fingerprint or use a lower temperature.

**2. Structured output over text parsing.**
Free-text LLM responses require brittle extraction logic that breaks on model updates.
`.with_structured_output(AgentDecision)` delegates schema enforcement to the LangChain
adapter layer (function calling for OpenAI; JSON mode for Ollama). Failures are
exceptions, not silent data corruption.

**3. Pre-computed demo decisions.**
The demo works fully offline without credentials. Pre-computed decisions in
`_DEMO_DECISIONS` are not random — they were generated by GPT-4o and curated to match
the exact confidence calibration described in the talk (EVT-001 at 22%, EVT-005 at 94%,
etc.). This makes the demo deterministic and presentation-safe.

**4. `feedback_log.json` as the simplest viable feedback store.**
A production system would write to a vector store, a fine-tuning dataset, or an RLHF
pipeline. For this demo, a local JSON file makes the feedback loop *visible* — the
audience can open it and read every decision Sarah made. Transparency over engineering.

**5. Streamlit session state for demo control.**
All agent state (processed events, decisions, Sarah's responses) lives in
`st.session_state`. Each page is independent and resettable. This is intentional:
the demo is designed to be run, reset, and run again during a live presentation.

---

## What's Deliberately Simplified

This is a conference demo, not a production system. The following are conscious simplifications:

| Simplified | Production equivalent |
|---|---|
| `feedback_log.json` | Vector store, fine-tuning pipeline, or RLHF dataset |
| Manual "Next Event" button | Event stream (Kafka, Azure Event Hub, MQTT) |
| Single-turn LLM assessment | Multi-step reasoning chain or ReAct agent |
| In-memory session state | Persistent database + audit trail |
| No authentication | Role-based access control for Sarah's console |
| Pre-computed demo decisions | Online inference with caching + fallback |

---

## The Core Argument

**Human-in-the-Loop** sounds safe. It isn't.

When humans validate every AI decision at scale, three things happen:

- **Cognitive anchoring**: reviewers stop thinking independently and anchor to the AI's framing. The better the AI, the worse this gets.
- **Decision fatigue**: at 10,000 decisions/day, oversight becomes checkbox-ticking.
- **Expertise atrophy**: when humans validate instead of decide, their skills degrade. The safety net dissolves.

**AI-in-the-Loop** inverts the burden: the AI handles what it can be confident about,
and humans engage only where their judgment is genuinely needed.
Sarah makes *fewer* decisions — but they're the ones that matter,
and her expertise stays sharp because she's always working at the edge of her domain.

---

## The Five Questions

Before building your next agentic system:

1. Are humans **making decisions** — or just validating them?
2. Will expertise **stay sharp** — or erode over time?
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

Talk slides will be added after the event.

## Further Reading

- [LangChain LCEL docs](https://python.langchain.com/docs/concepts/lcel/)
- [Structured output with LangChain](https://python.langchain.com/docs/concepts/structured_outputs/)
- [Ollama model library](https://ollama.com/library)
- [Azure OpenAI structured outputs](https://learn.microsoft.com/azure/ai-services/openai/how-to/structured-outputs)
