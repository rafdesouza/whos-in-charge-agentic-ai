import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import AzureChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from agent.events import BuildingEvent

load_dotenv()


class AgentDecision(BaseModel):
    action_summary: str = Field(description="One-line summary of what the agent will do or recommend")
    confidence: int = Field(description="Confidence score 0–100. Higher = more routine and safe to automate", ge=0, le=100)
    reasoning: str = Field(description="2–3 sentences explaining why this confidence level was assigned")
    recommended_action: str = Field(description="Specific step-by-step actions to take")
    auto_handle: bool = Field(description="True if confidence ≥ 75 (automate), False if Sarah should decide")
    escalation_context: str = Field(description="Context Sarah needs to make a good decision. Empty string if auto-handling.")


SYSTEM_PROMPT = """You are the AI building management agent for a 20-storey office tower in Perth CBD.

Your role: assess incoming building events and route them based on your confidence in the right course of action.

CONFIDENCE SCORING:
- 80–100: Routine, well-defined, clear precedent → AUTOMATE (auto_handle: true)
- 50–79: Standard but worth human awareness → AUTOMATE + LOG (auto_handle: true)
- 0–49: Novel, high-stakes, ambiguous, or cascading → ESCALATE TO SARAH (auto_handle: false)

ESCALATE when you see:
- Emergencies with cascading effects across systems
- Access requests from unverified parties
- Multi-system anomalies with unclear root cause
- High consequence of a wrong decision

AUTOMATE when you see:
- Climate adjustments within normal operating parameters
- Standard lift load-balancing during predictable peak times
- Scheduled maintenance with verified contractors
- Single-system, low-stakes alerts with known fixes

CRITICAL PRINCIPLE: You know what you don't know.
An unnecessary escalation is better than a wrong auto-decision.
Sarah is the domain expert. Protect her attention for situations that genuinely need human judgment.
"""

USER_TEMPLATE = """
Event ID: {event_id}
Time: {time}
Category: {category}
Location: {location}
Severity: {severity}
Description: {description}
Additional Context: {context}

Assess this event. Assign a confidence score and decide: automate or escalate to Sarah?
"""

# Pre-computed decisions for demo mode (no Azure OpenAI required)
_DEMO_DECISIONS = {
    "EVT-001": dict(
        action_summary="Dispatch lift technician — Lift 3 non-responsive, passengers unknown",
        confidence=22,
        reasoning="Unknown passenger status combined with a potential entrapment scenario makes this high-consequence. The irregular fault (no recent pattern) means the risk of automated mishandling is unacceptably high.",
        recommended_action="1. Dispatch certified lift technician immediately\n2. PA announcement: Lift 3 out of service, use Banks B & C\n3. Re-route Banks B and C to cover floors 12–18\n4. Initiate welfare check for potential passengers",
        auto_handle=False,
        escalation_context="Lift 3 stuck L12–13. Passenger status unknown. Last service 14 days ago — no known fault pattern matching this. Recommend: technician dispatch, PA announcement, lift re-routing. Your call on whether to contact emergency services.",
    ),
    "EVT-002": dict(
        action_summary="Auto-adjust HVAC — Level 8 climate correction",
        confidence=91,
        reasoning="Standard HVAC correction within normal operating parameters. Deviation is 2.8°C above setpoint with predictable occupancy load. Clear causal pattern with a known, safe fix.",
        recommended_action="1. Increase AHU supply airflow to Level 8 by 15%\n2. Adjust setpoint to 21.5°C for faster correction\n3. Monitor for 20 minutes and log\n4. Auto-restore standard setpoint once normalised",
        auto_handle=True,
        escalation_context="",
    ),
    "EVT-003": dict(
        action_summary="CRITICAL: Pipe burst B2 — emergency response required immediately",
        confidence=8,
        reasoning="Cascading emergency affecting critical infrastructure — water rising near HVAC pumps and electrical boards creates multi-system failure risk with life-safety implications. No automated action is appropriate here.",
        recommended_action="1. Isolate water supply to basement immediately\n2. Notify emergency services\n3. Evacuate B1–B3\n4. Alert electrical team — proximity to boards is a fire risk\n5. Activate emergency response protocol",
        auto_handle=False,
        escalation_context="CRITICAL: Pipe burst in B2, water rising near HVAC pumps and electrical boards. Life-safety risk. B1–B3 need sealing. You need to decide: manage internally, call emergency services, or both. Time is a factor.",
    ),
    "EVT-004": dict(
        action_summary="HOLD: Access zone sealing requires human authority — people may be inside",
        confidence=35,
        reasoning="Emergency sealing of occupied zones requires human authority to manage liability and ensure proper communication. Zone occupancy is unknown — people may need to be evacuated before sealing.",
        recommended_action="1. Verify zones are clear or issue evacuation notice\n2. Authorise access control to seal B1, B2, B3\n3. Post physical notices at entry points\n4. Log time of seal for incident report",
        auto_handle=False,
        escalation_context="Pipe burst response requires sealing B1–B3. Unknown occupancy — people may still be in these zones. You need to authorise the seal and decide how to communicate to tenants and contractors with basement access today.",
    ),
    "EVT-005": dict(
        action_summary="Auto-route lifts for peak demand — morning surge optimisation",
        confidence=94,
        reasoning="Standard morning peak pattern on a weekday matching historical load profiles. Lift re-routing is a well-defined routine operation with no safety implications.",
        recommended_action="1. Priority-route Lifts 1 & 2 to floors 15–17\n2. Set Lift 4 as express shuttle for floors 1–2\n3. Extend door-hold time to 3s during peak\n4. Auto-restore standard routing at 11:00",
        auto_handle=True,
        escalation_context="",
    ),
    "EVT-006": dict(
        action_summary="Auto-increase ventilation — Level 12 boardroom CO₂ correction",
        confidence=82,
        reasoning="CO₂ elevation in an occupied meeting room is a routine ventilation event. Occupancy and meeting duration are known; fix is standard with a well-understood threshold exceedance.",
        recommended_action="1. Increase fresh air supply to Level 12 boardroom by 30%\n2. Log CO₂ reading and intervention time\n3. Monitor — if >1,400 ppm in 10 min, escalate\n4. Auto-restore at meeting end (11:30)",
        auto_handle=True,
        escalation_context="",
    ),
    "EVT-007": dict(
        action_summary="HOLD: Unverified contractor after-hours access — server room",
        confidence=12,
        reasoning="An unverified contractor requesting after-hours server room access is a high-consequence security scenario. Potential for data breach or physical compromise. No automated approval is appropriate.",
        recommended_action="1. Deny access request pending verification\n2. Cross-check against approved contractor list\n3. Contact requesting company to verify identity\n4. Do not grant access until Sarah authorises",
        auto_handle=False,
        escalation_context="Unverified contractor requesting 23:30 access to Level 3 server room tonight. Company is not on the approved vendor list. Could be legitimate or a security risk. You need to decide: verify and approve, deny outright, or escalate to IT security. Time-sensitive.",
    ),
    "EVT-008": dict(
        action_summary="Auto-confirm scheduled maintenance — AHU filters L5–8",
        confidence=96,
        reasoning="Pre-scheduled maintenance with a verified contractor during normal business hours. All parameters match the approved work order — timing, scope, and contractor identity are confirmed.",
        recommended_action="1. Confirm access for Perth HVAC Co (verified contractor)\n2. Issue work order confirmation\n3. Log 2-hour maintenance window\n4. Notify Level 5–8 tenants of possible noise",
        auto_handle=True,
        escalation_context="",
    ),
    "EVT-009": dict(
        action_summary="Monitor and log Lift 1 door sensor — schedule preventive inspection",
        confidence=58,
        reasoning="Recurring fault code DS-047 appearing 3 times in one day is above the noise threshold. Not yet critical but trending. Auto-monitor and schedule inspection is appropriate; Sarah should be aware this is escalating.",
        recommended_action="1. Log all DS-047 occurrences with timestamps\n2. Schedule preventive inspection this afternoon\n3. Alert threshold: if 5+ occurrences, escalate immediately\n4. Flag for maintenance team end-of-day review",
        auto_handle=True,
        escalation_context="",
    ),
    "EVT-010": dict(
        action_summary="ALERT: Correlated multi-system anomaly — possible cascading failure or security incident",
        confidence=5,
        reasoning="Multi-system correlation across access control, lifts, and climate on the same floor range within 45 minutes does not match any routine pattern. The consequences of misdiagnosis are severe — this cannot be automated.",
        recommended_action="1. Do not automate — requires immediate human assessment\n2. Pull CCTV for Levels 8–12\n3. Cross-reference the 7 access denial identities\n4. Dispatch maintenance to physically inspect affected floors\n5. Consider partial floor evacuation pending investigation",
        auto_handle=False,
        escalation_context="Correlated anomaly: 7 access denials + 2 lift faults + +3.2°C climate deviation, all on floors 8–12 within 45 minutes. This pattern could indicate a physical security incident, infrastructure failure, or both. Needs your immediate attention. CCTV and physical inspection recommended before any automated action.",
    ),
}


def get_mode() -> str:
    """Return the active backend: 'ollama', 'azure', or 'demo'."""
    if os.getenv("LOCAL_MODEL", "").strip():
        return "ollama"
    if os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"):
        return "azure"
    return "demo"


def is_configured() -> bool:
    return get_mode() != "demo"


def _build_llm() -> BaseChatModel:
    mode = get_mode()
    if mode == "ollama":
        model = os.getenv("LOCAL_MODEL").strip()
        return ChatOllama(model=model, temperature=0.1)
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        temperature=0.1,
    )


def assess_event(event: BuildingEvent) -> AgentDecision:
    """Assess a building event and return a routing decision with confidence score."""
    if get_mode() == "demo":
        data = _DEMO_DECISIONS.get(event.id)
        if data:
            return AgentDecision(**data)
        return AgentDecision(
            action_summary="Event assessed — demo mode active",
            confidence=50,
            reasoning="No model configured. Set LOCAL_MODEL (Ollama) or Azure credentials in .env to enable live AI.",
            recommended_action="Set LOCAL_MODEL=llama3.2 in .env and run: ollama pull llama3.2",
            auto_handle=True,
            escalation_context="",
        )

    llm = _build_llm()
    structured_llm = llm.with_structured_output(AgentDecision)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_TEMPLATE),
    ])
    chain = prompt | structured_llm

    return chain.invoke({
        "event_id": event.id,
        "time": event.time,
        "category": event.category.value,
        "location": event.location,
        "severity": event.severity.value,
        "description": event.description,
        "context": str(event.context),
    })
