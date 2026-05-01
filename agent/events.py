from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventCategory(str, Enum):
    LIFT = "Lift"
    CLIMATE = "Climate"
    ACCESS = "Access Control"
    MAINTENANCE = "Maintenance"
    EMERGENCY = "Emergency"
    SECURITY = "Security"


class EventSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class BuildingEvent:
    id: str
    time: str
    category: EventCategory
    description: str
    location: str
    severity: EventSeverity
    context: dict[str, Any] = field(default_factory=dict)


# Sarah's day — the exact sequence from the talk
SARAHS_DAY: list[BuildingEvent] = [
    BuildingEvent(
        "EVT-001", "07:00",
        EventCategory.LIFT,
        "Lift 3 unresponsive — stuck between floors 12 and 13",
        "Lift Bank A, L12–13",
        EventSeverity.HIGH,
        {"affected_floors": "12–18", "passengers": "unknown", "last_service": "14 days ago"},
    ),
    BuildingEvent(
        "EVT-002", "07:15",
        EventCategory.CLIMATE,
        "Temperature complaints — Level 8 open plan too hot",
        "Level 8 Open Plan",
        EventSeverity.LOW,
        {"current_temp": "24.8°C", "setpoint": "22°C", "occupancy": "42 people"},
    ),
    BuildingEvent(
        "EVT-003", "09:00",
        EventCategory.EMERGENCY,
        "Pipe burst — basement mechanical room, water rising near electrical boards",
        "Basement B2",
        EventSeverity.CRITICAL,
        {"affected_systems": "HVAC pumps, electrical boards", "water_level": "rising rapidly"},
    ),
    BuildingEvent(
        "EVT-004", "09:05",
        EventCategory.ACCESS,
        "Emergency access zone sealing required for basement wings B1–B3",
        "Basement B1–B3",
        EventSeverity.HIGH,
        {"reason": "Pipe burst response", "zones": "B1, B2, B3"},
    ),
    BuildingEvent(
        "EVT-005", "10:30",
        EventCategory.LIFT,
        "Routine lift demand surge — morning peak, floors 1–17 congested",
        "All Lift Banks",
        EventSeverity.LOW,
        {"current_load": "87%", "peak_floors": "1, 2, 15, 16, 17"},
    ),
    BuildingEvent(
        "EVT-006", "10:45",
        EventCategory.CLIMATE,
        "CO₂ levels elevated in Level 12 boardroom during active meeting",
        "Level 12 Boardroom",
        EventSeverity.MEDIUM,
        {"co2_ppm": "1,100", "threshold": "800", "occupancy": "18 people", "meeting_ends": "11:30"},
    ),
    BuildingEvent(
        "EVT-007", "11:00",
        EventCategory.ACCESS,
        "Unusual after-hours access request — unverified contractor, server room",
        "Level 3 Server Room",
        EventSeverity.HIGH,
        {"requester": "Unknown contractor", "company": "Unverified", "scheduled_time": "23:30 tonight"},
    ),
    BuildingEvent(
        "EVT-008", "11:30",
        EventCategory.MAINTENANCE,
        "Scheduled AHU filter replacement — Levels 5–8, verified contractor",
        "Levels 5–8",
        EventSeverity.LOW,
        {"units": "4 AHU units", "duration": "2 hours", "contractor": "Perth HVAC Co (verified)"},
    ),
    BuildingEvent(
        "EVT-009", "13:00",
        EventCategory.LIFT,
        "Lift 1 intermittent door sensor fault — recurring 3 times today",
        "Lift Bank B, Lift 1",
        EventSeverity.MEDIUM,
        {"fault_code": "DS-047", "occurrences_today": "3", "pattern": "irregular"},
    ),
    BuildingEvent(
        "EVT-010", "14:00",
        EventCategory.SECURITY,
        "Cascading anomaly — access denials, lift faults, and climate deviation correlated across Levels 8–12",
        "Levels 8–12",
        EventSeverity.CRITICAL,
        {"access_denials": "7 in 45 min", "lift_faults": "2", "climate_deviation": "+3.2°C", "timespan": "45 minutes"},
    ),
]

SEVERITY_COLOR = {
    EventSeverity.LOW: "#2ECC71",
    EventSeverity.MEDIUM: "#F39C12",
    EventSeverity.HIGH: "#E67E22",
    EventSeverity.CRITICAL: "#E74C3C",
}

CATEGORY_ICON = {
    EventCategory.LIFT: "🛗",
    EventCategory.CLIMATE: "🌡️",
    EventCategory.ACCESS: "🔐",
    EventCategory.MAINTENANCE: "🔧",
    EventCategory.EMERGENCY: "🚨",
    EventCategory.SECURITY: "⚠️",
}
