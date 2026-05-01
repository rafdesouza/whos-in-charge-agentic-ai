import streamlit as st
from agent.building_agent import is_configured

st.set_page_config(
    page_title="Who's Really in Charge?",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Who's Really in Charge?")
st.subheader("The People Puzzle Behind Agentic AI")
st.caption("Microsoft Azure Data Analytics Meetup — Perth, Western Australia")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
### The Problem

Meet Sarah. She's a facilities manager for a 20-storey office tower in Perth's CBD.
She has deep domain expertise. She knows the building, the tenants, the quirks.

But she has no visibility and no bandwidth.

Every event — routine or critical — lands on her desk.
Her expertise is consumed by noise.

---

### What This Demo Explores

This repository accompanies a talk on **AI-in-the-Loop** design:
the idea that the right question isn't *"should AI assist humans?"* — it's
*"which decisions genuinely need human judgment?"*

The core mechanism is **confidence scoring**: the agent knows what it doesn't know.

| Confidence | Routing |
|---|---|
| 80–100 | Automated |
| 50–79 | Automated + logged |
| 0–49 | Escalated to Sarah with full context |

---

### The Three Demos

Navigate using the sidebar:

1. **Sarah's Reactive Day** — The problem. Watch every event land on Sarah's desk.
2. **AI-in-the-Loop** — The solution. Confidence scoring routes events intelligently.
3. **Paradigm Comparison** — Side-by-side: Human-in-the-Loop vs AI-in-the-Loop.

---

### The Warning

> *"The danger isn't sentience. It's losing control through design laziness."*

When humans validate every AI decision, they become rubber stamps.
Expertise erodes. The safety net dissolves.

The goal isn't to remove humans from the loop.
It's to keep them genuinely in charge of what matters.
""")

with col2:
    st.markdown("### Setup Status")

    if is_configured():
        st.success("Azure OpenAI connected — live AI mode active")
    else:
        st.warning("Running in demo mode")
        st.markdown("""
Pre-computed decisions are loaded for all 10 events.
To enable live Azure OpenAI:

```bash
cp .env.example .env
# Fill in your Azure credentials
```
""")

    st.divider()
    st.markdown("### Quick Start")
    st.code("""git clone <repo-url>
cd whos-in-charge-agentic-ai
pip install -r requirements.txt
cp .env.example .env   # add your credentials
streamlit run app.py""", language="bash")

    st.divider()
    st.markdown("""
### Talk Reference
**"Who's Really in Charge?"**
Rafael Souza — AI Solution Architect
Microsoft Azure Data Analytics Meetup, Perth WA

*Built with the assistance of Claude (Anthropic)*
""")
