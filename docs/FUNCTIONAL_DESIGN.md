# Functional Design Document
## Building Management Agentic System

> *"If any of these voices is missing, the system breaks in ways you won't see until it's in production."*

---

## Purpose of This Document

This document describes the functional design of each component in the building management
agentic system — what it does, how it reasons, and critically, **which team skills were
required to design it correctly**.

The argument is not philosophical. Each section demonstrates that missing a specific
team profile produces a concrete, identifiable failure in that component. Diverse teams
are a technical requirement, not a cultural one.

---

## Team Profiles Reference

The following profiles are referenced throughout this document. They are drawn directly
from the talk and represent the roles that must be present when designing, building,
and operating an agentic system.

| Profile | What they bring | What they miss alone |
|---|---|---|
| **Engineer** | Builds the system — code, architecture, integrations | Operational edge cases; what the system means to the people using it |
| **Domain Expert** | Knows what *should* happen — protocols, procedures, failure modes | Cannot implement it alone; struggles to specify requirements in code |
| **Ethicist** | Spots bias, liability, and unintended consequences | Caught downstream if not at the design table |
| **Systems Thinker** | Catches cascading failures across silos | Not visible within a single component; only apparent across the whole |
| **Communicator** | Makes the system trusted and usable by real people | Without them, technically correct systems get rejected or misused |

These map to six operational skills used to evaluate each component:

- **Domain Expertise** — knowing the building, tenants, protocols
- **Data Literacy** — knowing what sensors mean and what patterns reveal
- **Systems Thinking** — knowing how failures cascade across systems
- **Decision-Making Under Uncertainty** — knowing when to act without full information
- **Communication & Trust** — knowing how to explain AI decisions to the people affected
- **Ethics & Safety** — knowing how to spot edge cases the system was never trained for

---

## Component 1 — Event Data Model

**File:** `agent/events.py`

### What it does

Every interaction with the agent starts with a `BuildingEvent`. This is the data
contract between the physical building (sensors, access logs, maintenance requests,
human complaints) and the AI reasoning layer. Getting this schema right determines
everything downstream — the agent can only reason about what it receives.

### Step-by-step logic

1. An event occurs in the physical building (sensor trigger, access request, complaint).
2. It is represented as a `BuildingEvent` with six fields: `id`, `time`, `category`,
   `description`, `location`, `severity`.
3. A free-form `context` dictionary carries domain-specific metadata that varies by
   category — a lift event carries `fault_code` and `last_service`; a climate event
   carries `co2_ppm` and `occupancy`.
4. The event is passed to the agent. The LLM receives all fields as structured text
   and reasons across them holistically.

```python
@dataclass
class BuildingEvent:
    id: str
    time: str
    category: EventCategory     # Lift | Climate | Access Control | Maintenance | Emergency | Security
    description: str
    location: str
    severity: EventSeverity     # Low | Medium | High | Critical
    context: dict[str, Any]     # Domain-specific metadata — intentionally untyped
```

### Why `context` is untyped

A lift fault carries `fault_code`, `last_service`, and `passengers`.
A CO₂ event carries `co2_ppm`, `threshold`, `occupancy`, and `meeting_ends`.
These are fundamentally different shapes. Forcing a unified typed schema would require
either information loss (drop what doesn't fit) or a lowest-common-denominator design
that serves no domain well. The LLM handles heterogeneous context naturally — the calling
code does not need to.

### Skills required

**Domain Expert — critical**
The fields in `context` were not chosen by the engineer. They were chosen by asking:
*"What information does someone with deep operational knowledge of this building
actually need to make a good decision?"*

For a lift fault: knowing `last_service` is 14 days ago matters because it suggests
whether this is a pattern or an anomaly. Knowing `passengers` is "unknown" is the
detail that turns a maintenance event into a potential welfare emergency. An engineer
designing this schema without a domain expert would have captured `floor` and `fault_code`
and missed both of these.

**Data Literacy — important**
The context fields are only useful if they map to data that actually exists and is
reliably captured. A domain expert may specify `passengers: exact count` as a field,
but a data-literate person knows the sensor only captures occupancy estimates, not
individual counts. They calibrate what can be promised vs what is aspirational.

**Systems Thinker — important**
The `category` enum defines the silos: Lift, Climate, Access, Maintenance, Emergency,
Security. A systems thinker flags that EVT-010 — a *Security* event — is caused by
correlations across *Lift* + *Climate* + *Access* events. The schema needs to support
that cross-silo reference, or the agent sees a security event without the causal chain.

**What breaks without these profiles:**
- Without Domain Expert: `context` is sparse — the agent reasons on incomplete information
  and produces overconfident automation decisions.
- Without Data Literacy: `context` contains fields that are not reliably populated —
  the agent reasons on missing or stale data.
- Without Systems Thinker: cross-silo events are modelled as single-category events —
  the cascading nature of EVT-010 is invisible to the agent.

---

## Component 2 — Lift Systems Logic

**Events:** EVT-001 (stuck lift), EVT-005 (peak routing), EVT-009 (sensor fault)

### What it does

The lift component handles the most safety-critical routine events in the building.
It must distinguish between three fundamentally different scenarios that all present as
"lift issue": a welfare emergency (passengers possibly trapped), a performance
optimisation (peak-hour routing), and a predictive maintenance signal (recurring fault code).

### Step-by-step logic

**Scenario A — Stuck lift (EVT-001, confidence: 22)**

1. Lift 3 unresponsive between floors 12–13.
2. Agent checks `context`: passengers = "unknown", last_service = "14 days ago".
3. Unknown passenger status triggers immediate welfare concern — this is not automatable.
4. Confidence: 22%. Escalate to Sarah with full context.
5. Recommended action includes: technician dispatch, PA announcement, welfare check.
6. Sarah decides whether to involve emergency services.

**Scenario B — Peak routing (EVT-005, confidence: 94)**

1. Load across all banks at 87%, peak on floors 1, 2, 15–17 at 10:30 on a weekday.
2. Agent checks `context`: current_load = "87%", peak_floors = "1, 2, 15, 16, 17".
3. This matches a well-known pattern: morning peak, upper floors for tenant arrival.
4. Standard routing adjustment — Lifts 1 & 2 prioritised to floors 15–17,
   Lift 4 as lobby shuttle, extended door-hold.
5. Confidence: 94%. Automate. Sarah not involved.

**Scenario C — Recurring sensor fault (EVT-009, confidence: 58)**

1. Lift 1 fault code DS-047, three occurrences today, pattern irregular.
2. Not yet critical (no safety implication) but above normal noise threshold.
3. Auto-monitor and log: schedule preventive inspection, set alert at 5 occurrences.
4. Confidence: 58%. Automate with logging. Sarah informed at end of day, not interrupted now.

### The operational knowledge that drives this

The difference between 22%, 94%, and 58% is not in the code — it is in the system
prompt, which was written to encode operational knowledge:

- Peak hours in a Perth CBD office tower are 7–9 AM and 4–6 PM, with upper floors
  receiving morning traffic and lower floors (retail/hospitality) receiving afternoon traffic.
- DS-047 is a door edge sensor fault — it is nuisance-level at 1–2 occurrences, a
  maintenance indicator at 3, and a service-stop trigger at 5+.
- Passenger welfare in a stuck lift escalates from "nuisance" to "emergency" within
  approximately 20 minutes in a non-air-conditioned shaft in Perth summer.

None of this is in the code. It is in the system prompt. The system prompt is a product
of domain knowledge, not engineering.

### Skills required

**Domain Expert — indispensable**
A lift systems expert or experienced facilities manager is the only person who knows:
- What fault code DS-047 means in practice and at what frequency it becomes a service trigger
- That passenger unknown = welfare risk in this specific building (no intercom in these shafts)
- That "87% load, floors 15–17, 10:30 AM" is a Tuesday morning, not an anomaly
- That the 14-day service interval for Lift 3 is within spec and not a red flag

Without this knowledge, EVT-005 (routine) might be escalated, and EVT-001 (welfare risk)
might be automated. The confidence scores flip.

**Data Literacy — important**
The `current_load: "87%"` figure comes from weight sensors on the lift cars. A
data-literate person knows:
- Weight sensors drift and must be calibrated — 87% today may equal 91% on an
  uncalibrated sensor
- Occupancy data from building access cards lags by 2–3 minutes during peak periods
- DS-047 occurrence count resets at midnight — "3 today" on a Monday morning vs a
  Friday afternoon carry different risk profiles

**Systems Thinker — important**
A stuck lift on floors 12–13 affects:
- Stairwell traffic → increased load on emergency exit routes
- HVAC → higher body heat from stairwell use on upper floors
- Tenant satisfaction → complaints unrelated to the lift may spike
- Security → stairwell propping by tenants avoiding wait times

EVT-010 (cascading anomaly) is only intelligible if the systems thinker has already
flagged that lift faults, climate deviations, and access control events are correlated
in this building. The agent's ability to score EVT-010 at 5% confidence depends on
the systems thinker having embedded that correlation awareness in the system prompt.

**Ethics & Safety — critical**
The single hardest design decision in this component is: *should a stuck lift with
unknown passenger status be auto-escalated, or should there be an automated PA
announcement first?*

An engineer's instinct is to automate the PA announcement (it's low-risk, high-value).
An ethicist's response: automating a welfare announcement from an AI system without
human confirmation creates liability. If the PA says "passengers are safe" and they
are not, the building operator faces legal exposure. If the PA says "please evacuate"
and it's a false alarm, tenant trust in the building systems collapses. Sarah must
own this message.

**What breaks without these profiles:**
- Without Domain Expert: EVT-005 (routine) gets escalated; EVT-001 (welfare risk) gets
  automated. The confidence scores are inverted.
- Without Data Literacy: sensor drift and lag produce false positives that erode
  confidence calibration over time.
- Without Systems Thinker: EVT-010 is assessed as a single-category security event,
  not a multi-system failure signal.
- Without Ethics & Safety: automated PA announcements create liability exposure before
  legal review.

---

## Component 3 — Climate & Environmental Logic

**Events:** EVT-002 (temperature complaint), EVT-006 (CO₂ elevation)

### What it does

Climate events are the highest-volume routine category in most office buildings.
The agent must distinguish between a standard set-point correction (high confidence,
automate) and a scenario where the climate deviation is a symptom of something else
(low confidence, escalate).

### Step-by-step logic

**Scenario A — Temperature complaint (EVT-002, confidence: 91)**

1. Level 8 open plan reporting 24.8°C against a 22°C set-point.
2. Context: 42 people in the space — predictable thermal load.
3. Deviation is 2.8°C, within the range of a standard AHU adjustment.
4. No correlated events on adjacent systems (no access anomalies, no lift faults).
5. Automate: increase supply airflow 15%, adjust set-point to 21.5°C, monitor 20 minutes.
6. Confidence: 91%. No human involvement required.

**Scenario B — CO₂ elevation in boardroom (EVT-006, confidence: 82)**

1. CO₂ at 1,100 ppm in Level 12 boardroom (threshold: 800 ppm), 18 occupants, meeting ends 11:30.
2. Known occupancy, known meeting window, known fix (increase fresh air supply).
3. Single-system event, no correlated anomalies.
4. Automate: increase fresh air 30%, monitor, alert if >1,400 ppm.
5. Confidence: 82%. Automate with logging.

### What makes climate different from other categories

Climate events are the category most vulnerable to **automation overreach**. The agent
scores EVT-002 at 91% precisely because the context is fully specified and the fix is
well-understood. If the same temperature deviation appeared during a pipe burst
(EVT-003), the correct response is not to adjust the HVAC — it is to check whether
the thermal spike is caused by the loss of HVAC cooling from flooded pumps.

The system prompt must encode that climate events in isolation are routine, but climate
events correlated with other system failures are not.

### Skills required

**Domain Expert — important**
HVAC operational knowledge determines what constitutes "within normal parameters":
- A 2.8°C deviation on Level 8 with 42 occupants at midday in summer is standard
- The same deviation at 3 AM with 0 occupants is an anomaly worth escalating
- CO₂ at 1,100 ppm in a 18-person boardroom is predictable; at 1,100 ppm in a
  2-person office is an HVAC failure signal

Without this operational knowledge, the agent cannot distinguish between
"expected deviation for this occupancy and time" and "unexpected deviation
indicating a fault."

**Data Literacy — critical**
Climate data quality is the most common failure mode in this component:
- Temperature sensors in open-plan floors have dead zones — a single sensor
  reading 24.8°C may not represent the whole floor
- CO₂ sensor calibration drifts — a reading of 1,100 ppm on a sensor not
  calibrated in 6 months may actually be 950 ppm
- Occupancy data from badge readers is a proxy — 42 badges swiped ≠ 42 people
  currently on the floor

A data-literate person designs the context fields to include sensor IDs, last
calibration dates, and occupancy data sources, not just the raw readings.

**Systems Thinker — important**
The critical design question for this component: *under what conditions does a
climate event stop being a climate event?*

Answer: when it is correlated with another system failure within the same time
window and floor range. This is the design basis for EVT-010. The systems thinker
establishes the correlation rules in the system prompt.

**What breaks without these profiles:**
- Without Domain Expert: the agent treats all 2.8°C deviations the same regardless
  of context — time of day, occupancy, and building state are invisible.
- Without Data Literacy: the agent makes high-confidence automation decisions on
  stale or miscalibrated sensor data.
- Without Systems Thinker: climate events during a pipe burst get automated
  (HVAC adjustment) rather than escalated (the HVAC may be part of the failure).

---

## Component 4 — Access Control Logic

**Events:** EVT-004 (emergency zone sealing), EVT-007 (unverified contractor)

### What it does

Access control events are the highest-stakes category for liability and security.
The agent must distinguish between a routine access request (high confidence, automate
confirmation) and a scenario where automating an access decision creates legal, security,
or physical risk.

### Step-by-step logic

**Scenario A — Emergency zone sealing (EVT-004, confidence: 35)**

1. Pipe burst in B2 requires sealing of zones B1–B3.
2. Context: reason = "pipe burst response", affected zones = B1, B2, B3.
3. Unknown occupancy — people may still be in these zones.
4. Sealing an occupied zone without warning creates a physical safety risk.
5. Agent cannot verify zone occupancy from available data.
6. Confidence: 35%. Escalate to Sarah. She must authorise the seal and manage
   communication to affected tenants and contractors.

**Scenario B — Unverified contractor access (EVT-007, confidence: 12)**

1. Contractor requesting after-hours access to Level 3 server room at 23:30.
2. Context: requester = "unknown contractor", company = "unverified."
3. Company is not on the approved vendor list.
4. Server room after-hours = high consequence if wrong.
5. Confidence: 12%. Hard stop. Deny pending verification. Escalate to Sarah.
6. Sarah decides: verify and approve, deny outright, or escalate to IT security.

### The asymmetry of access decisions

The access control component illustrates a fundamental principle of agentic system
design: **the cost of a false negative (unnecessary escalation) and a false positive
(wrong automation) are not symmetric.**

For EVT-007:
- False negative: Sarah reviews a legitimate contractor request and approves it.
  Cost: 10 minutes of Sarah's attention.
- False positive: the system auto-approves an unauthorised person into the server room.
  Cost: data breach, physical security incident, regulatory exposure.

The asymmetry is extreme. The confidence threshold for access control automation
should be set higher than for climate or lift routing. This is a design decision
that requires explicit ethical reasoning — it is not derivable from the data alone.

### Skills required

**Domain Expert — indispensable**
The facilities manager knows:
- Which contractors are on the approved vendor list and how that list is maintained
- That server room access after-hours requires IT security notification regardless
  of contractor status
- That sealing B1–B3 without a welfare check first violates the building's emergency
  response protocol (likely an insurance and regulatory requirement)
- What "verified contractor" actually means operationally (signed NDA, insurance
  certificate, prior site induction)

Without this knowledge, the agent cannot write an escalation context that gives Sarah
what she needs to make a good decision. She receives a flag without actionable information.

**Ethics & Safety — critical**
This component contains two of the most ethically fraught design questions in the system:

1. Should an AI system ever auto-approve access to a secured area without a human
   in the loop? The answer in this design is: no, for anything below a very high
   confidence bar. This is a design principle, not a technical default.

2. Should an AI system auto-seal an occupied zone in an emergency? The answer is:
   not without a welfare check, even if time-critical. An ethicist establishes this
   boundary before the engineer builds the automation.

Neither of these defaults is obvious. An engineer optimising for response time would
automate both. An ethicist identifies the liability and safety exposure.

**Decision-Making Under Uncertainty — important**
EVT-007 presents the agent with a scenario where acting (auto-approve) and not acting
(deny, escalate) both carry risk. An unverified contractor might be a legitimate
last-minute engagement or a social engineering attempt. The system cannot know.

The design decision — deny and escalate, with Sarah deciding — is an explicit choice
to place uncertainty-driven decisions with the human. This needs to be encoded in the
system prompt as a principle, not a rule. The person who can articulate this principle
clearly is someone with explicit training in decision-making under uncertainty.

**Communicator — important**
When Sarah denies an access request or seals a zone, someone has to communicate that
decision to the affected party. The agent's `recommended_action` for EVT-007 includes:
"Contact requesting company to verify identity." This is a communication task that
requires framing — the agent must suggest how Sarah communicates the hold without
creating a confrontation with a potentially legitimate contractor.

The communicator profile ensures the escalation context is written as an action guide
for Sarah, not a data dump.

**What breaks without these profiles:**
- Without Domain Expert: escalation context is incomplete — Sarah receives a flag
  but not the information she needs (vendor list status, protocol requirements).
- Without Ethics & Safety: the confidence threshold for access automation is set
  too low — the agent auto-approves based on superficial pattern matching.
- Without Decision-Making Under Uncertainty: the agent escalates everything in this
  category (over-cautious) or automates based on available context (over-confident).
- Without Communicator: escalation context is technical and dense — Sarah has to
  interpret before she can act, adding latency in time-critical scenarios.

---

## Component 5 — Maintenance & Scheduling Logic

**Events:** EVT-008 (scheduled maintenance), EVT-009 (recurring fault as maintenance signal)

### What it does

Maintenance events split into two types: **scheduled** (pre-approved, low risk,
automate) and **unscheduled-but-predictive** (emerging fault signal requiring
preventive action). The agent must handle both, and distinguish them from one
another and from genuine faults.

### Step-by-step logic

**Scenario A — Scheduled maintenance (EVT-008, confidence: 96)**

1. AHU filter replacement on Levels 5–8, 2-hour window, Perth HVAC Co.
2. Context: contractor = "Perth HVAC Co (verified)", scheduled = confirmed.
3. All parameters match the approved work order.
4. Automate: confirm access, issue work order confirmation, notify tenants.
5. Confidence: 96%. No human involvement required.

**Scenario B — Fault as maintenance signal (EVT-009, confidence: 58)**

1. Lift 1 DS-047 fault code, 3 occurrences, irregular pattern.
2. Not yet a service-stop trigger, but trending.
3. Auto-monitor, schedule preventive inspection, set 5-occurrence alert threshold.
4. Confidence: 58%. Automate with logging. Flag for end-of-day maintenance review.

### Skills required

**Domain Expert — critical**
The 96% confidence on EVT-008 depends entirely on knowing what "verified contractor
doing scheduled work" means operationally. It is not just a checkbox — it means:
- Work order exists and is signed off
- Contractor has completed site induction
- Insurance certificate is current
- Work scope is limited to what's in the order
- A 2-hour window for 4 AHU units is within normal range (not suspiciously fast
  or slow)

Without domain expertise, the confidence score has no basis. The engineer builds
the automation logic; the domain expert validates that 96% is the right threshold
for this specific contractor + scope combination.

For EVT-009: knowing that DS-047 at frequency 3 is a monitoring signal, not yet
an action signal, is lift-specific operational knowledge. The fault code meaning,
the threshold for action, and the appropriate response (preventive inspection vs
immediate shutdown) are not in any codebase — they come from the maintenance manual
and the facilities manager's experience.

**Data Literacy — important**
Maintenance scheduling depends on data quality in two areas:
- Work order data: is the scheduled maintenance confirmed in the CMMS (Computerised
  Maintenance Management System), or just in an email? The confidence for EVT-008
  should be lower if the confirmation is verbal vs system-recorded.
- Fault history: the DS-047 count of "3 today" is only meaningful if the fault
  logging is reliable. If the sensor logs intermittently, 3 occurrences may
  represent 6 actual events — crossing the action threshold without the agent knowing.

**What breaks without these profiles:**
- Without Domain Expert: DS-047 at count 3 gets either ignored (no pattern
  recognition) or over-reacted to (maintenance stop on a nuisance fault).
- Without Data Literacy: scheduled maintenance confidence is based on calendar
  records, not CMMS confirmation — the agent auto-approves a contractor whose
  work order was verbally cancelled.

---

## Component 6 — Emergency Response Logic

**Events:** EVT-003 (pipe burst)

### What it does

Emergency events are the highest-consequence, lowest-confidence category by design.
The agent's role in an emergency is not to make decisions — it is to detect, escalate
immediately with full context, and recommend an initial response plan for the human
to act on.

### Step-by-step logic

1. Pipe burst detected in B2. Water rising near HVAC pumps and electrical boards.
2. Context: affected systems = "HVAC pumps, electrical boards", water level = "rising rapidly".
3. Multi-system impact, life-safety risk, time-critical.
4. Confidence: 8%. Immediate escalation to Sarah with maximum urgency.
5. Recommended action: isolate water supply, notify emergency services, evacuate B1–B3,
   alert electrical team.
6. Sarah decides: manage internally, call emergency services, or both.

### Why the confidence is 8%, not 0%

The agent assigns 8% rather than 0% because it *can* provide actionable information —
it knows what systems are affected, has a recommended initial response, and can pre-stage
the escalation context. A score of 0% would suggest the agent has nothing useful to
offer. The 8% represents: *"I know this is serious, I know the immediate response steps,
but the decision authority belongs to Sarah."*

### Skills required

**Domain Expert — indispensable**
Emergency response protocols for a Perth CBD office building are defined by the
building's emergency response plan, which is a legal document. The domain expert
knows:
- At what point a pipe burst triggers a mandatory call to emergency services (varies
  by jurisdiction and water volume)
- That electrical boards + water = arc flash risk, requiring qualified electrician
  response, not just facilities management
- That B1–B3 sealing must follow a specific sequence in the building's emergency
  evacuation plan
- That "water rising rapidly" in a basement mechanical room has a specific escalation
  path distinct from a slow leak

**Ethics & Safety — critical**
The most important design decision in this component: **no automated action is
appropriate for a life-safety emergency.** This is not derived from the confidence
score — it is a design principle established before the system is built.

An engineer might reason: "We can automate the water supply isolation — it's a
relay switch, no humans needed." This is technically correct. An ethicist identifies
that automatically isolating a water supply in a building with active fire suppression
systems may disable the sprinklers. Automated relay switches in emergency scenarios
require sign-off from the building's fire safety engineer, the insurer, and in some
cases the local fire authority. None of this is obvious from the code.

**Decision-Making Under Uncertainty — important**
The escalation context for EVT-003 includes: *"You need to decide: manage internally,
call emergency services, or both. Time is a factor."*

This framing — that not deciding is itself a decision, and that speed matters — is a
communication design choice. It is written by someone who understands decision-making
under time pressure. The alternative framing ("please advise on next steps") is vague
and introduces latency at the worst possible moment.

**What breaks without these profiles:**
- Without Domain Expert: the recommended action is generic ("address the pipe burst")
  rather than protocol-specific. Sarah receives a flag, not a response guide.
- Without Ethics & Safety: automated water supply isolation disables fire suppression
  — a safety intervention creates a safety hazard.
- Without Decision-Making Under Uncertainty: the escalation context is passive —
  Sarah receives information but not a decision framework appropriate to time pressure.

---

## Component 7 — Security & Anomaly Detection Logic

**Events:** EVT-010 (cascading multi-system anomaly)

### What it does

The security component handles the most cognitively demanding scenario in the system:
events that are not individually alarming, but whose correlation across systems and
time indicates a situation that no single subsystem would flag on its own.

### Step-by-step logic

1. Seven access denials across floors 8–12 in 45 minutes.
2. Two lift faults (DS-047 recurrence) in the same zone.
3. +3.2°C climate deviation across the same floor range.
4. No single event crosses its individual threshold. Together: pattern anomaly.
5. Confidence: 5%. Escalate immediately with maximum urgency.
6. Recommended action: CCTV review, access denial identity cross-reference,
   physical inspection, possible partial evacuation.

### Why this is the hardest component to design

EVT-010 is the component that most clearly demonstrates why diverse teams are a
technical requirement, not a soft preference.

- The **engineer** sees three separate, sub-threshold events.
- The **systems thinker** sees one correlated pattern across systems.
- The **domain expert** knows that this specific floor range (8–12) houses the
  building's largest tenant and has had prior tailgating incidents.
- The **ethicist** asks: if we automate a partial evacuation on a pattern anomaly
  with no confirmed threat, what is the legal and reputational exposure?
- The **communicator** asks: how do we frame an uncertain escalation to Sarah without
  causing panic or premature action?

All five profiles are needed simultaneously to design this component correctly.

### Skills required

**Systems Thinker — indispensable**
This component does not exist without a systems thinker at the design table. The
correlation rule — that access + lift + climate anomalies on the same floor range
within 45 minutes constitute a security signal — is not a sensor reading. It is a
cross-silo pattern. It requires someone whose mental model spans the full building
infrastructure, not individual systems.

The systems thinker's contribution is encoded in two places:
1. The system prompt: *"Multi-system anomalies with unclear root cause → ESCALATE"*
2. The event schema: EVT-010's `context` field captures the cross-system data that
   makes the correlation visible to the agent.

**Domain Expert — important**
Knowing that this pattern *matters* requires operational experience:
- 7 access denials in 45 minutes on a Tuesday morning could be a badge reader
  malfunction (common in Perth heat), a security incident, or tenants forgetting
  their badges after a long weekend.
- The lift fault recurrence combined with the climate deviation narrows it: badge
  malfunctions don't cause lift faults or climate spikes.
- A domain expert who has managed this building for 3 years has seen the badge
  malfunction pattern — and knows it doesn't look like this.

**Ethics & Safety — important**
EVT-010 is the scenario where automated responses are most tempting (it looks serious)
and most dangerous (it might be nothing, or it might be something that requires a
specific response the agent can't predict). The ethicist establishes the principle:
uncertainty at this level of consequence requires human authority, full stop.

The agent's recommendation to consider *partial* floor evacuation rather than full
building evacuation is also an ethics call: a false alarm full-building evacuation
on a working Tuesday has significant tenant and reputational cost. The agent
recommends the least disruptive response that addresses the risk — but Sarah decides.

**What breaks without these profiles:**
- Without Systems Thinker: EVT-010 is never generated — the three sub-threshold
  events are processed individually as routine (access), monitoring (lift), routine
  (climate). The anomaly is invisible.
- Without Domain Expert: the confidence score is not calibrated to this building's
  history — the agent may score the same pattern at 40% (monitor) rather than 5% (escalate).
- Without Ethics & Safety: the agent recommends automated evacuation — creating legal
  exposure, tenant disruption, and possible "cry wolf" erosion of trust in the system.

---

## Component 8 — Confidence Scoring Engine

**File:** `agent/building_agent.py` → `SYSTEM_PROMPT` + `AgentDecision.confidence`

### What it does

The confidence scoring engine is the core mechanism of the entire system. It is not a
classifier, not a rules engine, and not a lookup table. It is a reasoning process
encoded in natural language that instructs the LLM to evaluate each event against a
scoring contract and produce a calibrated confidence score.

### Step-by-step logic

1. The system prompt defines the scoring contract:
   - 80–100: routine, well-defined, clear precedent → automate
   - 50–79: standard but worth logging → automate + log
   - 0–49: novel, high-stakes, ambiguous, cascading → escalate

2. The LLM receives the full `BuildingEvent` (all fields) and reasons about:
   - Is this event well-understood? (precedent)
   - What is the consequence of a wrong decision? (stakes)
   - Is the available information complete? (certainty)
   - Are there correlated signals across other systems? (complexity)

3. The LLM produces `confidence: int` — a single number that encodes all of the above.

4. The routing logic applies the threshold: `≥75 → automate`, `<50 → escalate`.

### Why LLM-generated, not rule-computed

| Approach | Advantage | Limitation |
|---|---|---|
| Rules engine | Deterministic, auditable, fast | Brittle — requires explicit enumeration of every case; breaks on novel inputs |
| Classifier | Consistent, fast, trainable | Requires labelled training data; retrains when domain changes |
| LLM-generated | Generalises to novel inputs; reasons from description | Non-deterministic; prompt-sensitive; slower |

For a building management system where novel events (pipe bursts, cascading anomalies,
unverified contractors) are precisely the events that matter most, a rules engine
or classifier would fail exactly where failure is most costly. The LLM's ability to
reason about novelty is the design choice.

### Skills required

**Domain Expert — defines the scoring contract**
The thresholds (80/50) and the criteria for each band were not chosen mathematically —
they were chosen by asking an experienced facilities manager: *"At what point do you
want to be notified vs trust automation?"* The answer calibrated the thresholds.

The system prompt's ESCALATE criteria — emergencies, unverified parties, multi-system
anomalies, high-consequence wrong decisions — were defined by asking: *"What are the
failure modes you've seen in buildings where automation went wrong?"*

**Ethics & Safety — defines the asymmetry**
The principle encoded in the system prompt — *"An unnecessary escalation is better
than a wrong auto-decision"* — is an ethical stance, not a technical one. It encodes
an asymmetry: the cost of over-escalation (human attention) is explicitly valued
less than the cost of over-automation (potential harm).

This is a design choice that must be made explicitly by someone trained in
consequentialist reasoning about AI systems. Without it, the engineer defaults
to optimising for efficiency (fewer escalations) rather than safety.

**Decision-Making Under Uncertainty — calibrates the grey zone**
The 50–79 band (automate + log) exists because some events are routine but unusual
enough to want a human-readable record. This is the zone where the agent acts but
also says: *"I did this, and I want you to know."*

Without explicit reasoning about uncertainty, this zone collapses into binary
(automate or escalate) — losing the nuance that makes the system useful at scale.

**What breaks without these profiles:**
- Without Domain Expert: thresholds are set by intuition or trial and error —
  either too many escalations (operator fatigue) or too few (missed edge cases).
- Without Ethics & Safety: the scoring contract is efficiency-optimised — automate
  more, escalate less — until a wrong automation causes harm.
- Without Decision-Making Under Uncertainty: the 50–79 zone is eliminated —
  the system becomes binary and loses the ability to signal "I'm not sure, but I acted."

---

## Component 9 — Sarah's Decision Console

**File:** `pages/2_AI_In_The_Loop.py`

### What it does

The decision console is the human interface. It presents escalated events to Sarah
with everything she needs to make a good decision: the event details, the agent's
reasoning, the recommended action, and a clear call to act. It captures her decision
and feeds it back to the system.

### Design principles

1. **Context before recommendation.** Sarah sees the full event context before the
   agent's recommendation — to prevent anchoring to the AI's framing before she has
   formed her own view.

2. **Recommendation is a suggestion, not a default.** The "Accept Recommendation"
   button exists alongside a free-text field. Sarah can override. Her override is
   logged.

3. **Escalation context is written for action, not explanation.** The `escalation_context`
   field is short, plain-language, and ends with a clear question or decision point.
   It is not a data report — it is a briefing.

### Skills required

**Communicator — critical**
The escalation context that appears in Sarah's console was designed by someone who
understands how humans make decisions under time pressure:
- The context starts with the most critical fact, not the most recent
- It ends with a specific decision question: *"Your call on whether to contact emergency services"*
- It uses plain language, not sensor readings or fault codes

Without a communicator, the console displays raw agent output — technically accurate,
cognitively taxing. Sarah must interpret before she can act, adding latency in
scenarios where speed matters.

**Domain Expert — important**
The recommended actions that appear in the console were written by someone who knows
the building's protocols:
- "Dispatch certified lift technician" — not "call maintenance"
- "Cross-reference against approved contractor list" — not "verify identity"
- "Consider partial floor evacuation" — not "evacuate if necessary"

The specificity of the recommended actions is what makes them useful to Sarah.
Generic recommendations require her to translate before acting — defeating the purpose.

**Ethics & Safety — important**
The console design includes a deliberate friction point: Sarah cannot accept a
recommendation without reading the escalation context (the form requires scrolling).
This is an anti-anchoring design decision — it slows the rubber-stamp failure mode.

An engineer's first instinct is to put the "Accept" button at the top. An ethicist's
response: a fast accept before reading context is the exact behaviour we are designing
against.

**What breaks without these profiles:**
- Without Communicator: the console is a data display, not a decision interface.
  Sarah reads, interprets, decides — slower, more error-prone.
- Without Domain Expert: recommended actions are generic and require Sarah to
  translate into protocol-specific steps — adding cognitive load at high-stress moments.
- Without Ethics & Safety: "Accept" is the default and prominent — Sarah becomes
  a rubber stamp. The exact failure mode the system was designed to prevent.

---

## Component 10 — Feedback Loop

**File:** `agent/feedback.py`

### What it does

Every decision Sarah makes on an escalated event is logged: the event, the agent's
recommendation, Sarah's decision, and whether she accepted the recommendation. This
data is the system's learning signal — it is the mechanism by which human judgment
is preserved and transferred back into the agent over time.

### Step-by-step logic

1. Sarah responds to an escalated event via the decision console.
2. `log_decision()` is called with the event, the agent's decision, Sarah's response,
   and a boolean indicating whether she accepted the recommendation.
3. A `FeedbackEntry` is appended to `feedback_log.json`.
4. Over time, the log accumulates the acceptance rate — the proportion of cases where
   Sarah's judgment aligned with the agent's recommendation.

### What the acceptance rate reveals

| Acceptance rate | Interpretation |
|---|---|
| >95% | Agent may be over-escalating routine cases — thresholds too conservative |
| 70–95% | Healthy — agent escalates genuine edge cases, recommendation is usually right |
| 50–70% | Agent recommendation quality is low — system prompt needs refinement |
| <50% | Systematic misalignment — domain knowledge in the prompt is wrong or outdated |

### Production use of this data

In this demo, `feedback_log.json` is a local file. In a production system, this
data drives three distinct improvement pipelines:

1. **Prompt refinement**: Cases where Sarah overrides the recommendation reveal
   system prompt gaps. Regular review sessions with the domain expert update the
   prompt based on real decisions.

2. **Fine-tuning dataset**: Each `(event, agent_recommendation, sarah_decision)` triple
   is a labelled example. At sufficient volume (typically 500–1,000 examples), this
   data can fine-tune the base model to align with this building's operational norms.

3. **RAG retrieval context**: Past similar events can be retrieved at inference time
   — *"Here are 3 cases where Sarah decided on similar events"* — improving
   recommendation quality without fine-tuning.

### Skills required

**Domain Expert — defines what "accepted" means**
The `sarah_accepted_recommendation` boolean is only meaningful if Sarah's acceptance
is an informed endorsement, not a convenience click. The feedback loop's value as a
training signal depends on Sarah engaging genuinely with each escalation — reading the
context, forming a view, then deciding. The domain expert trains Sarah on how to use
the console, not just the engineer who builds it.

**Data Literacy — interprets the signal**
An acceptance rate of 80% is meaningless without knowing the distribution:
- If the 20% overrides all cluster on ACCESS CONTROL events on Friday afternoons,
  that is a specific domain gap, not a general model quality issue.
- If the 20% overrides all involve the same contractor category, that is a prompt
  gap, not a data quality issue.

A data-literate person analyses the feedback log as a distribution, not just a summary statistic.

**Engineer — closes the loop**
The feedback data is only valuable if it is acted on. The engineer builds the pipeline
that takes `feedback_log.json` and produces: updated prompt versions, fine-tuning
jobs, RAG retrieval configurations. Without this, the feedback log is a record with
no downstream effect — and the system stops improving.

**What breaks without these profiles:**
- Without Domain Expert: Sarah treats "Accept" as the default — the feedback data
  reflects convenience, not judgment. It degrades the model.
- Without Data Literacy: the acceptance rate is read as a single number, not a
  distribution — domain-specific gaps go undetected.
- Without Engineer: the feedback loop is one-way — Sarah's decisions are logged
  but never acted on. The system doesn't improve.

---

## Component 11 — Multi-Backend Model Abstraction

**File:** `agent/building_agent.py` → `get_mode()`, `_build_llm()`

### What it does

The agent is backend-agnostic. The same chain runs on Azure OpenAI (cloud) or Ollama
(local) without any change to the calling code. The active backend is selected by
environment variable at startup.

### Step-by-step logic

```python
def get_mode() -> str:
    if os.getenv("LOCAL_MODEL"):   return "ollama"   # local first
    if os.getenv("AZURE_OPENAI_ENDPOINT"): return "azure"
    return "demo"                                    # pre-computed fallback

def _build_llm() -> BaseChatModel:
    if get_mode() == "ollama":
        return ChatOllama(model=os.getenv("LOCAL_MODEL"), temperature=0.1)
    return AzureChatOpenAI(...)
```

`BaseChatModel` is the type contract. Both backends satisfy it.
The chain (`prompt | structured_llm`) is composed at call time, not at startup.

### Why this matters operationally

In a live demo at a venue with unreliable WiFi, the ability to switch from Azure
to a local Ollama model — by changing one environment variable — is the difference
between a working demo and a dead one.

In a production system, this abstraction enables:
- **Cost management**: route high-volume routine events to a smaller local model;
  reserve the cloud model for complex escalation assessments
- **Data residency**: for buildings in regulated industries, run the model on-premises
- **Redundancy**: fall back to local if the cloud endpoint is unavailable

### Skills required

**Engineer — implements the abstraction**
The `BaseChatModel` interface, LCEL chain composition, and environment-driven backend
selection are engineering decisions. The domain expert and ethicist do not design this
component — but they inform it.

**Domain Expert + Ethics & Safety — constrain it**
The choice of model affects the quality of confidence scoring. A smaller local model
(llama3.2 3B) may produce less calibrated confidence scores than GPT-4o. The domain
expert and ethicist must establish a minimum quality bar: what is the acceptable
rate of miscalibrated escalations before the model is considered unfit for this use case?

This is not a number the engineer can derive. It requires domain judgment about the
consequence of miscalibration in a building management context.

**Decision-Making Under Uncertainty — selects the deployment mode**
The decision to use local vs cloud in a given deployment is itself an uncertainty
decision: local is reliable but less capable; cloud is more capable but dependent on
connectivity. Someone with explicit training in trade-off reasoning under uncertainty
should own this deployment decision.

---

## Cross-Cutting Skills Summary

| Component | Engineer | Domain Expert | Ethicist | Systems Thinker | Communicator |
|---|---|---|---|---|---|
| Event Data Model | design | schema content | — | cross-silo context | — |
| Lift Systems | automation | fault codes, protocols | welfare decisions | cascade effects | PA framing |
| Climate & Environment | automation | HVAC norms, sensor limits | — | system correlation | — |
| Access Control | automation | contractor protocols | access asymmetry | — | denial framing |
| Maintenance & Scheduling | automation | fault thresholds, work orders | — | maintenance windows | — |
| Emergency Response | escalation routing | emergency protocols | no-automation principle | multi-system impact | decision framing |
| Security & Anomaly Detection | correlation logic | floor history | evacuation exposure | cross-silo signal | uncertain-escalation framing |
| Confidence Scoring Engine | scoring logic | threshold calibration | asymmetry principle | — | — |
| Sarah's Decision Console | UI | protocol specificity | anti-anchoring design | — | escalation context |
| Feedback Loop | pipeline | what "accepted" means | data integrity | — | — |
| Multi-Backend Abstraction | interface design | quality bar | model fitness | — | — |

---

## The Final Argument

The table above is not a RACI matrix. It is a failure mode map.

Every cell that has an entry is a component that will be designed incorrectly if
that profile is not at the table. The failures are not abstract — they are:

- Confidence scores that are inverted (EVT-001 automated, EVT-005 escalated)
- Legal exposure from automated emergency responses
- Training data that degrades the model instead of improving it
- An interface that turns Sarah into a rubber stamp
- A cascading anomaly that is never detected because no one modelled cross-silo correlation

The talk's conclusion — *"if any of these voices is missing, the system breaks in
ways you won't see until it's in production"* — is not a cultural statement about
team diversity. It is a technical statement about failure modes.

Each voice in the team is a load-bearing element of the system.
