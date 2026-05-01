import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from agent.events import BuildingEvent
from agent.building_agent import AgentDecision

FEEDBACK_FILE = "feedback_log.json"


@dataclass
class FeedbackEntry:
    event_id: str
    event_description: str
    event_location: str
    event_time: str
    agent_confidence: int
    agent_recommendation: str
    sarah_decision: str
    sarah_accepted_recommendation: bool
    timestamp: str


def log_decision(
    event: BuildingEvent,
    decision: AgentDecision,
    sarah_response: str,
    accepted: bool,
) -> FeedbackEntry:
    entry = FeedbackEntry(
        event_id=event.id,
        event_description=event.description,
        event_location=event.location,
        event_time=event.time,
        agent_confidence=decision.confidence,
        agent_recommendation=decision.recommended_action,
        sarah_decision=sarah_response,
        sarah_accepted_recommendation=accepted,
        timestamp=datetime.now().isoformat(),
    )
    _append_to_log(entry)
    return entry


def _append_to_log(entry: FeedbackEntry) -> None:
    existing: list[dict] = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []

    existing.append(asdict(entry))
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(existing, f, indent=2)


def load_feedback_log() -> list[dict]:
    if not os.path.exists(FEEDBACK_FILE):
        return []
    try:
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def acceptance_rate(log: Optional[list[dict]] = None) -> float:
    entries = log if log is not None else load_feedback_log()
    if not entries:
        return 0.0
    accepted = sum(1 for e in entries if e.get("sarah_accepted_recommendation"))
    return accepted / len(entries)
