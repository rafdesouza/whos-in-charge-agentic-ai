import time
import streamlit as st
from agent.events import SARAHS_DAY, SEVERITY_COLOR, CATEGORY_ICON

st.set_page_config(page_title="Sarah's Reactive Day", page_icon="🏢", layout="wide")

st.title("Sarah's Reactive Day")
st.markdown(
    "Every event — routine or critical — lands on Sarah's desk. "
    "No triage. No automation. No filtering."
)
st.divider()

# ── Session state ──────────────────────────────────────────────────────────────
if "reactive_index" not in st.session_state:
    st.session_state.reactive_index = 0
if "reactive_events" not in st.session_state:
    st.session_state.reactive_events = []
if "reactive_done" not in st.session_state:
    st.session_state.reactive_done = False

total = len(SARAHS_DAY)
processed = len(st.session_state.reactive_events)

# ── Top metrics ────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Events today", processed)
m2.metric("On Sarah's desk", processed)
m3.metric("Automated", "0")
m4.metric("Queue load", f"{int(processed / total * 100)}%" if total else "0%")

st.progress(processed / total if total else 0)
st.divider()

# ── Layout ─────────────────────────────────────────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.markdown("### Incoming Events")

    if not st.session_state.reactive_done:
        if st.session_state.reactive_index < total:
            if st.button("Next Event →", type="primary", use_container_width=True):
                event = SARAHS_DAY[st.session_state.reactive_index]
                st.session_state.reactive_events.append(event)
                st.session_state.reactive_index += 1
                if st.session_state.reactive_index >= total:
                    st.session_state.reactive_done = True
                st.rerun()
        else:
            st.session_state.reactive_done = True
    else:
        st.button("Next Event →", disabled=True, use_container_width=True)
        st.success("All events processed — Sarah's day is complete.")

    if st.button("Reset Demo", use_container_width=True):
        st.session_state.reactive_index = 0
        st.session_state.reactive_events = []
        st.session_state.reactive_done = False
        st.rerun()

    st.divider()

    for event in reversed(st.session_state.reactive_events):
        color = SEVERITY_COLOR.get(event.severity, "#888")
        icon = CATEGORY_ICON.get(event.category, "📋")
        st.markdown(
            f"""
<div style="border-left: 4px solid {color}; padding: 10px 14px; margin-bottom: 10px;
            background: #1a1a2e; border-radius: 4px;">
  <div style="font-size: 0.75rem; color: #aaa;">{event.time} &nbsp;·&nbsp; {event.category.value} &nbsp;·&nbsp;
    <span style="color:{color}; font-weight:600;">{event.severity.value}</span>
  </div>
  <div style="font-size: 0.95rem; font-weight: 600; margin: 4px 0;">{icon} {event.description}</div>
  <div style="font-size: 0.8rem; color: #bbb;">{event.location}</div>
</div>
""",
            unsafe_allow_html=True,
        )

with right:
    st.markdown("### Sarah's Desk")

    if not st.session_state.reactive_events:
        st.info("Sarah's day starts here. Press 'Next Event' to begin.")
    else:
        queue_pct = processed / total
        if queue_pct < 0.4:
            desk_color = "#2ECC71"
            status = "Under control"
        elif queue_pct < 0.7:
            desk_color = "#F39C12"
            status = "Getting busy"
        else:
            desk_color = "#E74C3C"
            status = "Overwhelmed"

        st.markdown(
            f"""
<div style="border: 2px solid {desk_color}; border-radius: 8px; padding: 20px; text-align: center;
            background: #1a1a2e; margin-bottom: 16px;">
  <div style="font-size: 2.5rem; font-weight: 700; color: {desk_color};">{processed}</div>
  <div style="font-size: 1rem; color: #ccc;">decisions waiting for Sarah</div>
  <div style="font-size: 0.85rem; color: {desk_color}; margin-top: 8px; font-weight: 600;">{status}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        for event in st.session_state.reactive_events:
            icon = CATEGORY_ICON.get(event.category, "📋")
            st.markdown(
                f"- **{event.time}** &nbsp; {icon} &nbsp; {event.description[:60]}{'…' if len(event.description) > 60 else ''}",
                unsafe_allow_html=True,
            )

# ── Reveal section ─────────────────────────────────────────────────────────────
if st.session_state.reactive_done:
    st.divider()
    st.markdown("### The Question")
    st.markdown(
        f"Sarah handled **{total} events** today. "
        "All of them. No exceptions. No filtering."
    )

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Events Sarah handled", total)
    col_b.metric("Events needing Sarah's expertise", "3", help="EVT-003 (pipe burst), EVT-007 (unverified access), EVT-010 (cascading anomaly)")
    col_c.metric("Events that could have been automated", "7", help="Routine climate, lift routing, scheduled maintenance, standard monitoring")

    st.warning(
        "7 out of 10 events were routine. "
        "Sarah's domain expertise was wasted on noise. "
        "Her judgment — the thing that actually matters — was consumed by lift routing and climate adjustments.\n\n"
        "**Now go to Page 2 to see what changes when AI handles triage.**"
    )
