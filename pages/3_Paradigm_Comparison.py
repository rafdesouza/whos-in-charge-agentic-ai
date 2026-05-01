import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from agent.events import SARAHS_DAY, SEVERITY_COLOR, CATEGORY_ICON
from agent.building_agent import AgentDecision

st.set_page_config(page_title="Paradigm Comparison", page_icon="🏢", layout="wide")

st.title("Paradigm Comparison")
st.markdown("Same 10 events. Same building. Two different design philosophies.")
st.divider()

# ── Static data: pre-computed for comparison (no API calls needed) ─────────────
# confidence scores from the demo decisions
EVENT_DATA = [
    {"id": "EVT-001", "time": "07:00", "description": "Lift 3 stuck — passengers unknown",         "category": "Lift",          "severity": "High",     "confidence": 22,  "auto": False, "needs_sarah": True},
    {"id": "EVT-002", "time": "07:15", "description": "Level 8 temperature complaints",             "category": "Climate",       "severity": "Low",      "confidence": 91,  "auto": True,  "needs_sarah": False},
    {"id": "EVT-003", "time": "09:00", "description": "Pipe burst — basement flooding",             "category": "Emergency",     "severity": "Critical", "confidence": 8,   "auto": False, "needs_sarah": True},
    {"id": "EVT-004", "time": "09:05", "description": "Emergency basement zone sealing",            "category": "Access",        "severity": "High",     "confidence": 35,  "auto": False, "needs_sarah": True},
    {"id": "EVT-005", "time": "10:30", "description": "Morning peak lift congestion",               "category": "Lift",          "severity": "Low",      "confidence": 94,  "auto": True,  "needs_sarah": False},
    {"id": "EVT-006", "time": "10:45", "description": "CO₂ elevated — Level 12 boardroom",          "category": "Climate",       "severity": "Medium",   "confidence": 82,  "auto": True,  "needs_sarah": False},
    {"id": "EVT-007", "time": "11:00", "description": "Unverified contractor after-hours access",   "category": "Access",        "severity": "High",     "confidence": 12,  "auto": False, "needs_sarah": True},
    {"id": "EVT-008", "time": "11:30", "description": "Scheduled AHU filter replacement",           "category": "Maintenance",   "severity": "Low",      "confidence": 96,  "auto": True,  "needs_sarah": False},
    {"id": "EVT-009", "time": "13:00", "description": "Lift 1 recurring door sensor fault",         "category": "Lift",          "severity": "Medium",   "confidence": 58,  "auto": True,  "needs_sarah": False},
    {"id": "EVT-010", "time": "14:00", "description": "Cascading anomaly — Levels 8–12",            "category": "Security",      "severity": "Critical", "confidence": 5,   "auto": False, "needs_sarah": True},
]

df = pd.DataFrame(EVENT_DATA)
automated_count = df["auto"].sum()
escalated_count = (~df["auto"]).sum()

# ── Paradigm summary metrics ───────────────────────────────────────────────────
st.markdown("### At a Glance")

pa, pb = st.columns(2)

with pa:
    st.markdown(
        """
<div style="border: 2px solid #E74C3C; border-radius: 8px; padding: 20px; background: #1a1a2e;">
  <h4 style="color:#E74C3C; margin-top:0;">Human-in-the-Loop</h4>
  <p style="color:#ccc; font-size:0.9rem;">AI makes decisions. Human validates every one.</p>
  <ul style="color:#ccc; font-size:0.9rem;">
    <li>All 10 events routed to Sarah</li>
    <li>Sarah approves or rejects AI suggestions</li>
    <li>Her judgment anchors to the AI's framing</li>
    <li>At scale: cognitive anchoring, decision fatigue, expertise atrophy</li>
  </ul>
  <div style="font-size:2rem; font-weight:700; color:#E74C3C; text-align:center; margin-top:10px;">
    10 / 10 events → Sarah
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

with pb:
    st.markdown(
        f"""
<div style="border: 2px solid #2ECC71; border-radius: 8px; padding: 20px; background: #1a1a2e;">
  <h4 style="color:#2ECC71; margin-top:0;">AI-in-the-Loop</h4>
  <p style="color:#ccc; font-size:0.9rem;">AI handles what it knows. Humans decide what matters.</p>
  <ul style="color:#ccc; font-size:0.9rem;">
    <li>{automated_count} events automated autonomously</li>
    <li>{escalated_count} genuine edge cases escalated to Sarah</li>
    <li>Each escalation includes full context + reasoning</li>
    <li>Sarah's decisions feed back — agent improves over time</li>
  </ul>
  <div style="font-size:2rem; font-weight:700; color:#2ECC71; text-align:center; margin-top:10px;">
    {escalated_count} / 10 events → Sarah
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

st.divider()

# ── Confidence chart ───────────────────────────────────────────────────────────
st.markdown("### Confidence Scores — Where the Routing Happens")

colors = ["#2ECC71" if row["auto"] else "#E74C3C" for _, row in df.iterrows()]
labels = [f"{row['id']}<br>{row['time']}" for _, row in df.iterrows()]
hover = [
    f"<b>{row['description']}</b><br>Confidence: {row['confidence']}%<br>Routed: {'Automated' if row['auto'] else 'Escalated to Sarah'}"
    for _, row in df.iterrows()
]

fig = go.Figure()

fig.add_shape(type="rect", x0=-0.5, x1=9.5, y0=75, y1=100, fillcolor="rgba(46,204,113,0.08)", line_width=0)
fig.add_shape(type="rect", x0=-0.5, x1=9.5, y0=50, y1=75, fillcolor="rgba(243,156,18,0.08)", line_width=0)
fig.add_shape(type="rect", x0=-0.5, x1=9.5, y0=0, y1=50, fillcolor="rgba(231,76,60,0.08)", line_width=0)

fig.add_hline(y=75, line_dash="dash", line_color="#2ECC71", line_width=1,
              annotation_text="≥75 Automated", annotation_position="right")
fig.add_hline(y=50, line_dash="dash", line_color="#F39C12", line_width=1,
              annotation_text="≥50 Auto+Log", annotation_position="right")

fig.add_trace(go.Bar(
    x=labels,
    y=df["confidence"].tolist(),
    marker_color=colors,
    hovertext=hover,
    hoverinfo="text",
    text=[f"{c}%" for c in df["confidence"].tolist()],
    textposition="outside",
))

fig.update_layout(
    height=380,
    plot_bgcolor="#0E1117",
    paper_bgcolor="#0E1117",
    font=dict(color="#ccc"),
    xaxis=dict(gridcolor="#333", tickfont=dict(size=10)),
    yaxis=dict(title="Confidence Score", range=[0, 110], gridcolor="#333"),
    showlegend=False,
    margin=dict(t=20, b=20, l=40, r=80),
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Side-by-side event table ───────────────────────────────────────────────────
st.markdown("### Event-by-Event Routing")

header_html = """
<div style="display:grid; grid-template-columns:0.5fr 2.5fr 1fr 1fr 1fr; gap:8px;
            padding: 8px 12px; background:#333; border-radius:4px;
            font-size:0.8rem; font-weight:700; color:#fff; margin-bottom:4px;">
  <span>Time</span>
  <span>Event</span>
  <span>Severity</span>
  <span>Confidence</span>
  <span>AI-in-the-Loop</span>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

for row in EVENT_DATA:
    sev_color = {"Low": "#2ECC71", "Medium": "#F39C12", "High": "#E67E22", "Critical": "#E74C3C"}.get(row["severity"], "#888")
    conf = row["confidence"]
    conf_color = "#2ECC71" if conf >= 75 else ("#F39C12" if conf >= 50 else "#E74C3C")
    routing_hitl = "<span style='color:#E74C3C; font-weight:600;'>→ Sarah validates</span>"
    routing_aitl = (
        "<span style='color:#2ECC71; font-weight:600;'>Automated</span>"
        if row["auto"]
        else "<span style='color:#E74C3C; font-weight:600;'>→ Sarah decides</span>"
    )
    cat_icons = {"Lift": "🛗", "Climate": "🌡️", "Access Control": "🔐", "Maintenance": "🔧", "Emergency": "🚨", "Security": "⚠️"}
    icon = cat_icons.get(row["category"], "📋")

    st.markdown(
        f"""
<div style="display:grid; grid-template-columns:0.5fr 2.5fr 1fr 1fr 1fr; gap:8px;
            padding: 10px 12px; background:#1a1a2e; border-radius:4px;
            font-size:0.85rem; color:#ddd; margin-bottom:3px; align-items:center;">
  <span style="color:#aaa;">{row['time']}</span>
  <span>{icon} {row['description']}</span>
  <span style="color:{sev_color}; font-weight:600;">{row['severity']}</span>
  <span style="color:{conf_color}; font-weight:700;">{conf}%</span>
  <span>{routing_aitl}</span>
</div>
""",
        unsafe_allow_html=True,
    )

st.divider()

# ── The structural difference ──────────────────────────────────────────────────
st.markdown("### The Structural Difference")

c1, c2, c3 = st.columns([1, 0.1, 1])

with c1:
    st.markdown(
        """
<div style="background:#1a1a2e; border-radius:8px; padding:20px;">
<h4 style="color:#E74C3C;">Human-in-the-Loop</h4>
<div style="font-size:0.9rem; color:#ccc; line-height:2;">
AI makes decisions<br>
⬇️<br>
Human validates<br>
⬇️<br>
Human anchors to AI framing<br>
⬇️<br>
Expertise erodes at scale
</div>
</div>
""",
        unsafe_allow_html=True,
    )

with c2:
    st.markdown("<div style='text-align:center; font-size:1.5rem; padding-top:60px; color:#888;'>vs</div>", unsafe_allow_html=True)

with c3:
    st.markdown(
        """
<div style="background:#1a1a2e; border-radius:8px; padding:20px;">
<h4 style="color:#2ECC71;">AI-in-the-Loop</h4>
<div style="font-size:0.9rem; color:#ccc; line-height:2;">
AI handles routine with confidence<br>
⬇️<br>
AI flags uncertainty to human<br>
⬇️<br>
Human decides on genuine edge cases<br>
⬇️<br>
Expertise stays sharp
</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.divider()

st.markdown("### The Five Questions")
st.markdown("""
Before building your next agentic AI system, ask:

1. Are humans **making decisions** — or just validating them?
2. Will expertise **stay sharp** — or erode?
3. What happens when the system encounters something it **wasn't trained for**?
4. Who's **actually in control** if something goes wrong?
5. What **diverse perspectives** are missing from the team that built this?
""")

st.caption("*Who's Really in Charge? — Rafael Souza · Microsoft Azure Data Analytics Meetup, Perth WA*")
