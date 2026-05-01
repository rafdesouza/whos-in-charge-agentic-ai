import streamlit as st
from agent.events import SARAHS_DAY, SEVERITY_COLOR, CATEGORY_ICON
from agent.building_agent import assess_event, AgentDecision, is_configured
from agent.feedback import log_decision

st.set_page_config(page_title="AI-in-the-Loop", page_icon="🏢", layout="wide")

st.title("AI-in-the-Loop")
st.markdown(
    "Same building. Same events. Different system. "
    "The agent assesses each event, assigns a confidence score, and routes accordingly."
)
st.divider()

# ── Session state ──────────────────────────────────────────────────────────────
if "aitl_index" not in st.session_state:
    st.session_state.aitl_index = 0
if "aitl_automated" not in st.session_state:
    st.session_state.aitl_automated = []
if "aitl_escalated" not in st.session_state:
    st.session_state.aitl_escalated = []
if "aitl_decisions" not in st.session_state:
    st.session_state.aitl_decisions = {}
if "aitl_sarah_responses" not in st.session_state:
    st.session_state.aitl_sarah_responses = {}

total = len(SARAHS_DAY)
processed = st.session_state.aitl_index
automated = len(st.session_state.aitl_automated)
escalated = len(st.session_state.aitl_escalated)

# ── Mode indicator ─────────────────────────────────────────────────────────────
if is_configured():
    st.success("Live mode — Azure OpenAI is active")
else:
    st.info("Demo mode — pre-computed decisions loaded. Add Azure credentials to .env for live AI.")

# ── Top metrics ────────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Events processed", processed)
m2.metric("Automated", automated)
m3.metric("Escalated to Sarah", escalated)
m4.metric("Sarah's focus", f"{escalated}/{processed}" if processed else "—")
auto_pct = int(automated / processed * 100) if processed else 0
m5.metric("Automation rate", f"{auto_pct}%")

st.progress(processed / total if total else 0)
st.divider()

# ── Controls ───────────────────────────────────────────────────────────────────
ctrl_left, ctrl_right = st.columns([1, 1])

with ctrl_left:
    can_advance = st.session_state.aitl_index < total
    btn_label = "Process Next Event →" if can_advance else "All Events Processed"

    if st.button(btn_label, type="primary", disabled=not can_advance, use_container_width=True):
        event = SARAHS_DAY[st.session_state.aitl_index]
        with st.spinner(f"Agent assessing {event.id}…"):
            decision = assess_event(event)
        st.session_state.aitl_decisions[event.id] = decision
        if decision.auto_handle:
            st.session_state.aitl_automated.append(event)
        else:
            st.session_state.aitl_escalated.append(event)
        st.session_state.aitl_index += 1
        st.rerun()

with ctrl_right:
    if st.button("Reset Demo", use_container_width=True):
        for key in ["aitl_index", "aitl_automated", "aitl_escalated", "aitl_decisions", "aitl_sarah_responses"]:
            del st.session_state[key]
        st.rerun()

st.divider()

# ── Main layout ────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1])


def confidence_color(score: int) -> str:
    if score >= 75:
        return "#2ECC71"
    if score >= 50:
        return "#F39C12"
    return "#E74C3C"


def confidence_label(score: int) -> str:
    if score >= 75:
        return "AUTO"
    if score >= 50:
        return "AUTO + LOG"
    return "ESCALATE"


def event_card(event, decision: AgentDecision, show_decision: bool = True) -> str:
    sev_color = SEVERITY_COLOR.get(event.severity, "#888")
    icon = CATEGORY_ICON.get(event.category, "📋")
    conf_color = confidence_color(decision.confidence)
    label = confidence_label(decision.confidence)

    decision_html = ""
    if show_decision:
        decision_html = f"""
  <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #333;">
    <span style="background:{conf_color}; color:#000; font-size:0.7rem; font-weight:700;
                 padding: 2px 8px; border-radius: 12px;">{label}</span>
    <span style="color:{conf_color}; font-weight:700; margin-left:8px;">{decision.confidence}%</span>
    <div style="font-size:0.78rem; color:#bbb; margin-top:4px;">{decision.action_summary}</div>
  </div>
"""

    return f"""
<div style="border-left: 4px solid {sev_color}; padding: 10px 14px; margin-bottom: 10px;
            background: #1a1a2e; border-radius: 4px;">
  <div style="font-size: 0.75rem; color: #aaa;">{event.time} &nbsp;·&nbsp; {event.category.value} &nbsp;·&nbsp;
    <span style="color:{sev_color}; font-weight:600;">{event.severity.value}</span>
  </div>
  <div style="font-size: 0.95rem; font-weight: 600; margin: 4px 0;">{icon} {event.description}</div>
  <div style="font-size: 0.8rem; color: #bbb;">{event.location}</div>
  {decision_html}
</div>
"""


with left_col:
    st.markdown("### Automated Actions")
    st.markdown(f"*{len(st.session_state.aitl_automated)} events handled — Sarah not required*")

    if not st.session_state.aitl_automated:
        st.info("No events automated yet. Press 'Process Next Event' to begin.")
    else:
        for event in reversed(st.session_state.aitl_automated):
            decision = st.session_state.aitl_decisions.get(event.id)
            if decision:
                st.markdown(event_card(event, decision), unsafe_allow_html=True)
                with st.expander(f"Actions taken — {event.id}", expanded=False):
                    st.markdown(decision.recommended_action)
                    st.caption(f"Confidence rationale: {decision.reasoning}")

with right_col:
    st.markdown("### Sarah's Console")
    st.markdown(f"*{len(st.session_state.aitl_escalated)} escalations — decisions that need her judgment*")

    if not st.session_state.aitl_escalated:
        if st.session_state.aitl_index == 0:
            st.info("Sarah's console is quiet. Escalations with full context will appear here.")
        else:
            st.success("Nothing escalated yet — agent is handling routine events autonomously.")
    else:
        for event in reversed(st.session_state.aitl_escalated):
            decision = st.session_state.aitl_decisions.get(event.id)
            if not decision:
                continue

            sev_color = SEVERITY_COLOR.get(event.severity, "#888")
            icon = CATEGORY_ICON.get(event.category, "📋")

            with st.container(border=True):
                st.markdown(
                    f"<div style='color:{sev_color}; font-weight:700; font-size:0.8rem;'>"
                    f"{event.time} — {event.severity.value} — Confidence: "
                    f"<span style='font-size:1.1rem'>{decision.confidence}%</span></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{icon} {event.description}**")
                st.caption(event.location)

                st.markdown("**Context for your decision:**")
                st.info(decision.escalation_context)

                st.markdown("**Agent recommends:**")
                st.code(decision.recommended_action, language=None)

                st.caption(f"Reasoning: {decision.reasoning}")

                response_key = f"response_{event.id}"
                accepted_key = f"accepted_{event.id}"

                if event.id not in st.session_state.aitl_sarah_responses:
                    with st.form(key=f"form_{event.id}"):
                        sarah_input = st.text_area(
                            "Your decision / notes:",
                            placeholder="Accept recommendation, modify, or enter your own response…",
                            height=80,
                        )
                        col_a, col_b = st.columns(2)
                        accept = col_a.form_submit_button("Accept Recommendation", type="primary")
                        override = col_b.form_submit_button("Submit Custom Decision")

                        if accept or override:
                            final_response = decision.recommended_action if accept else sarah_input
                            was_accepted = accept and not sarah_input.strip()
                            log_decision(event, decision, final_response, was_accepted)
                            st.session_state.aitl_sarah_responses[event.id] = {
                                "response": final_response,
                                "accepted": was_accepted,
                            }
                            st.rerun()
                else:
                    saved = st.session_state.aitl_sarah_responses[event.id]
                    if saved["accepted"]:
                        st.success("Sarah accepted the agent's recommendation.")
                    else:
                        st.warning("Sarah provided a custom decision.")
                    st.caption(f"Decision logged: {saved['response'][:120]}…" if len(saved["response"]) > 120 else f"Decision logged: {saved['response']}")

# ── End-of-demo summary ────────────────────────────────────────────────────────
if st.session_state.aitl_index >= total:
    st.divider()
    st.markdown("### Demo Complete — Summary")

    sa, sb, sc, sd = st.columns(4)
    sa.metric("Total events", total)
    sb.metric("Automated by AI", automated, f"{auto_pct}% of all events")
    sc.metric("Escalated to Sarah", escalated)
    feedback_count = len(st.session_state.aitl_sarah_responses)
    sd.metric("Sarah's responses logged", feedback_count, "feed back into the agent")

    if automated > 0:
        st.success(
            f"Sarah made **{escalated} genuine decisions** today — all of them where her expertise actually mattered. "
            f"The agent handled the other {automated} autonomously.\n\n"
            "**Her judgment is still sharp. She's planning, not firefighting.**"
        )
