# Architecture Deep Dive

This document covers the technical design of the building management agent demo —
implementation choices, trade-offs, and how each piece connects.

---

## Data Flow

```
BuildingEvent
     │
     │  id, time, category, description, location, severity, context
     ▼
ChatPromptTemplate.invoke()
     │
     │  formats system prompt + user template → List[BaseMessage]
     ▼
BaseChatModel  (AzureChatOpenAI or ChatOllama)
     │
     │  .with_structured_output(AgentDecision)
     │    → OpenAI: function/tool calling
     │    → Ollama: JSON mode + schema validation
     ▼
AgentDecision (Pydantic model, validated)
     │
     ├─ confidence ≥ 75  ──→  automated action logged
     │
     └─ confidence < 50  ──→  FeedbackEntry written to feedback_log.json
                               Sarah's decision captured via Streamlit form
```

---

## The LangChain LCEL Chain

The agent is built using LangChain Expression Language (LCEL).
The `|` operator composes runnables into a pipeline:

```python
chain = prompt | structured_llm
result = chain.invoke(event_dict)
```

Each step is a `Runnable`. LCEL handles:
- Input/output type coercion between steps
- Streaming (not used here, but available)
- Async execution (`.ainvoke()`, not used here)
- Retry logic (via `.with_retry()` wrapper if needed)

The full chain in `building_agent.py`:

```python
llm = _build_llm()                                    # BaseChatModel
structured_llm = llm.with_structured_output(AgentDecision)  # Runnable[dict, AgentDecision]

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", USER_TEMPLATE),
])                                                    # Runnable[dict, List[BaseMessage]]

chain = prompt | structured_llm                       # Runnable[dict, AgentDecision]

decision = chain.invoke({
    "event_id": event.id,
    "time": event.time,
    "category": event.category.value,
    "location": event.location,
    "severity": event.severity.value,
    "description": event.description,
    "context": str(event.context),
})
```

---

## Structured Output: Under the Hood

`.with_structured_output(AgentDecision)` does different things depending on the backend:

### Azure OpenAI / OpenAI
Converts `AgentDecision` to a JSON Schema function definition and calls the model
with `tool_choice="required"`. The model is forced to call the tool with valid arguments.
LangChain parses the tool call response back into an `AgentDecision` instance.

```json
{
  "tools": [{
    "type": "function",
    "function": {
      "name": "AgentDecision",
      "parameters": {
        "type": "object",
        "properties": {
          "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
          "auto_handle": {"type": "boolean"},
          ...
        },
        "required": ["action_summary", "confidence", "reasoning", ...]
      }
    }
  }],
  "tool_choice": {"type": "function", "function": {"name": "AgentDecision"}}
}
```

### Ollama
Uses JSON mode (`format="json"`) and appends the schema to the system prompt.
Ollama constrains token generation to valid JSON matching the schema.
LangChain parses the JSON response and validates against the Pydantic model.

The calling code is identical regardless — the adapter handles the difference.

---

## The AgentDecision Schema

```python
class AgentDecision(BaseModel):
    action_summary: str     # One-line label for the UI card
    confidence: int         # 0–100; constrained by ge=0, le=100
    reasoning: str          # Shown in expander — explains the confidence
    recommended_action: str # Step-by-step; shown in Sarah's console
    auto_handle: bool       # Routing gate — drives the UI split
    escalation_context: str # Context digest for Sarah; empty if auto-handling
```

Design notes:

- `confidence` is `int`, not `float`. The LLM doesn't produce meaningful sub-1% precision;
  integer forces the model to commit to a round number.
- `auto_handle` is redundant with `confidence >= 75` but explicit. It lets the LLM
  override routing for edge cases (e.g. confidence=76 but the LLM still wants human review).
  In practice the LLM keeps them consistent; the field makes intent readable.
- `escalation_context` is a separate field from `reasoning`. Reasoning explains *why* to
  the operator/log. Escalation context is written *for Sarah* — shorter, actionable,
  no jargon. The distinction matters for UI design.

---

## Confidence Scoring Design

Confidence is **LLM-reasoned**, not rule-computed. The system prompt defines the scoring
contract and the model applies it to novel inputs:

```
CONFIDENCE SCORING:
- 80–100: Routine, well-defined, clear precedent → AUTOMATE
- 50–79: Standard but worth human awareness     → AUTOMATE + LOG
- 0–49:  Novel, high-stakes, ambiguous          → ESCALATE
```

Why let the LLM score rather than using a classifier or rules engine?

| Approach | Pros | Cons |
|---|---|---|
| Rules engine | Deterministic, auditable | Brittle, requires domain expert to enumerate all cases |
| Classifier | Fast, consistent | Requires labelled training data; retraining when domain shifts |
| LLM-generated score | Generalises from description, no training data | Non-deterministic, slower, prompt-sensitive |

For a demo: LLM-generated wins — no training data, works from day one.
For production: consider a hybrid — classifier for known event types, LLM for
out-of-distribution inputs flagged by low classifier confidence.

### Threshold tuning

The 75 / 50 thresholds are not derived from data — they were chosen deliberately
conservative for a safety-critical domain. A wrong automation in building management
has physical consequences; an unnecessary escalation costs attention, not lives.

To tune: lower the escalation threshold (raise the automation bar) to reduce
Sarah's workload once the system has accumulated confidence from the feedback log.
Raise it during incident periods or for high-stakes event categories.

---

## Backend Abstraction

```python
def get_mode() -> str:
    if os.getenv("LOCAL_MODEL", "").strip():   return "ollama"
    if os.getenv("AZURE_OPENAI_ENDPOINT"):     return "azure"
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

`get_mode()` is pure (no side effects, no imports). It is called by the Streamlit
home page to render the status badge without instantiating a model.

`_build_llm()` is called only inside `assess_event()` — once per event, not once
at startup. This avoids credential errors on cold start and makes mode switching
at runtime possible (change `.env`, restart the app).

---

## Streamlit Architecture

### Multi-page structure

```
app.py              → st.set_page_config + home content
pages/
  1_*.py            → loaded by Streamlit as page 1
  2_*.py            → loaded as page 2
  3_*.py            → loaded as page 3
```

Streamlit discovers pages from the `pages/` directory at startup. The numeric prefix
controls sidebar order. Each page is an independent script; state is shared via
`st.session_state`.

### Session state design

Each demo page uses namespaced session state keys to avoid collisions:

```python
# Page 2 state
st.session_state.aitl_index       # int: next event to process
st.session_state.aitl_automated   # list[BuildingEvent]
st.session_state.aitl_escalated   # list[BuildingEvent]
st.session_state.aitl_decisions   # dict[event_id, AgentDecision]
st.session_state.aitl_sarah_responses  # dict[event_id, {response, accepted}]
```

State persists across reruns (button clicks trigger reruns). The "Reset Demo" button
deletes all namespaced keys and triggers a rerun — equivalent to a fresh page load
without losing state on other pages.

### Agent calls in Streamlit

LangChain calls are synchronous. In Streamlit, a synchronous call blocks the main
thread during the spinner. This is acceptable for a demo — typical latency is
0.5–3s per event depending on backend.

For production use, wrap in `asyncio` + `st.write_stream()` for streaming responses,
or cache decisions in a background thread.

---

## Feedback Loop

`feedback.py` defines two concerns:

**1. Data model**

```python
@dataclass
class FeedbackEntry:
    event_id: str
    event_description: str
    agent_confidence: int
    agent_recommendation: str
    sarah_decision: str
    sarah_accepted_recommendation: bool   # key signal
    timestamp: str
```

`sarah_accepted_recommendation` is the primary training signal. An acceptance rate
below ~70% suggests the confidence thresholds are miscalibrated or the system prompt
needs refinement. An acceptance rate above ~95% suggests the agent may be over-escalating.

**2. Persistence**

```python
def _append_to_log(entry: FeedbackEntry) -> None:
    existing = json.load(open(FEEDBACK_FILE)) if exists else []
    existing.append(asdict(entry))
    json.dump(existing, open(FEEDBACK_FILE, "w"), indent=2)
```

Append-only JSON. Intentionally simple — the audience can open the file during the
demo and read every decision made. In production this would be a database write with
a foreign key to the event and the operator ID.

### Production feedback paths

| Signal | Production use |
|---|---|
| `sarah_accepted = False` + `sarah_decision` | Preference pair for DPO / RLHF fine-tuning |
| `agent_confidence` distribution | Calibration monitoring — alert if average drops |
| Full `FeedbackEntry` | RAG retrieval — "here are 5 past similar events Sarah decided on" |
| Acceptance rate over time | Drift detection — model behaviour changing? |

---

## Event Schema

```python
@dataclass
class BuildingEvent:
    id: str              # EVT-001 … EVT-010 in the demo
    time: str            # HH:MM string
    category: EventCategory   # Enum: Lift, Climate, Access Control, ...
    description: str     # Plain English — what happened
    location: str        # Physical location in the building
    severity: EventSeverity   # Enum: Low, Medium, High, Critical
    context: dict        # Domain-specific key-value metadata
```

`context` is deliberately untyped (`dict[str, Any]`). Different event categories
carry fundamentally different metadata (a lift fault has `fault_code`; a climate
event has `co2_ppm`). Forcing a common schema would lose information. The LLM
receives `str(event.context)` and handles heterogeneous context naturally.

---

## Demo Mode: Pre-Computed Decisions

`_DEMO_DECISIONS` in `building_agent.py` contains the 10 pre-computed decisions that
were generated by GPT-4o and manually curated to match the exact confidence levels
discussed in the talk:

```python
"EVT-009": dict(
    confidence=58,     # in the "auto + log" zone — monitoring but not critical
    auto_handle=True,  # doesn't need Sarah yet
    ...
)
```

This makes the demo:
- **Deterministic** — same result every run, presentation-safe
- **Offline** — no credentials, no network, no latency
- **Curated** — confidence values illustrate the thresholds exactly as described in the talk

In live mode (Ollama or Azure), the LLM may produce different confidence scores.
This is expected and worth showing — it illustrates that the system reasons, not matches.

---

## What a Production Version Looks Like

This demo compresses several production concerns for clarity:

```
Demo                          Production equivalent
─────────────────────────────────────────────────────────────────
SARAHS_DAY list               Kafka / Azure Event Hub consumer
Manual "Next Event" button    Real-time event ingestion pipeline
Single LLM call per event     ReAct agent with tool use (query DB,
                              check maintenance schedules, look up
                              contractor registry)
feedback_log.json             PostgreSQL + MLflow experiment tracking
st.session_state              Redis session store + persistent audit log
No auth                       RBAC — Sarah has operator role, read-only
                              for others
Pre-computed fallback         Redis cache + circuit breaker pattern
Streamlit UI                  Production: React frontend or Teams bot
```

The agent logic (`building_agent.py`) is production-ready as written.
The infra around it is what needs to scale.
