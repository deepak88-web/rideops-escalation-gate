# Case Study Submission: RideOps Support Triage & Escalation Gate
**Candidate:** Candidate Submission | **Role:** Product / Operations Builder | **Date:** November 2026  
**Format:** 4-Part Executive Decision Brief (4 Pages / 8 Slides Equivalent)

---

## Part 1: Diagnosis — What is Driving the Problem?

### The Core Problem: Triage Failure, Not Staffing Shortage
Leadership’s prompt states: *"Support is drowning. Open tickets are up about 60% since July... bring that number down."*

Analysis of all **1,444 Q3 tickets (July 2 – September 30, 2026)** reveals that the backlog is driven by **an avoidable escalation bottleneck**, not frontline agent under-capacity:

```
[Total Tickets: 1,444]
       │
       ├── Non-Escalated (L1 Resolved): 958 (66.3%) ──> Median Resolution: 12.4 hrs (CSAT: 3.95)
       │
       └── Escalated to Engineering:     486 (33.7%) ──> Consumes 70.54% of ALL Resolution Hours!
                 │
                 ├── Legitimate Real Fixes:  211 (43.4%)
                 │
                 └── AVOIDABLE ESCALATIONS:  275 (56.58%) ──> Median Resolution: 42.8 hrs (CSAT: 2.76)
```

### Resolving the Team's Disagreement with Evidence

#### 1. Meera (Support Lead) vs. Sandeep (Engineering Manager)
* **Meera's View**: *"The real problem is engineering... tickets disappear for days... give us more people and quicker turnaround."*
* **Sandeep's View**: *"A lot of what support escalates shouldn't be coming to engineering... if support did basic checks first, we'd move faster."*
* **The Data Evidence**:
  * **Sandeep is right on root cause**: **56.58% (~57%)** of all engineering escalations are **avoidable** (closed as configuration errors, missing information, user confusion, or duplicates). Furthermore, **26.34%** (128 tickets) are bounced right back to L1 without any code fix.
  * **Meera is right on customer pain**: Escalated tickets suffer an exponential latency penalty. Each engineering handoff drastically inflates customer wait times ($p < 10^{-15}$):
    * **0 handoffs (L1 only)**: Median **12.4h** | P90: **29.5h** | CSAT: **3.95**
    * **1 handoff**: Median **33.8h** | P90: **71.4h** | CSAT: **2.97**
    * **2 handoffs**: Median **54.9h** | P90: **94.6h** | CSAT: **2.43**
    * **3 handoffs**: Median **66.1h** | P90: **104.9h** | CSAT: **1.86**
  * Escalated tickets account for only 33.7% of volume, but eat **70.54% of all customer resolution hours**.

#### 2. Ritika (Head of Ops): *"I have no budget for new hires right now."*
* **The Data Evidence**: Ritika does not need budget. Frontline L1 agents are actually fast (median initial response time is **1.5h** across all priorities).
* By eliminating the 56.6% avoidable escalations, the team reclaims **~10,400+ resolution hours per quarter**, expanding effective capacity by over **35% without adding a single hire**.

#### 3. Agent Disparities: The "Karan Check" and "Rahul Outlier"
Meera noted: *"Some of my agents are closing tickets in a few hours, so I know it can be done fast."*
* **The Karan Trade-Off (Karan B)**: Karan has the fastest median non-escalated close time (**9.62 hours**), but his **reopen rate is 29.49%** (highest on the team; team average: 18.28%; $\chi^2 = 13.34, p = 0.0039$). Karan rushes tickets to close without resolving underlying client issues, triggering reopens.
* **The Rahul Outlier (Rahul T)**: Rahul escalates at **58.62%** vs. his category-expected rate of **32.66%** (**1.79× expected ratio**). 61.8% of Rahul's escalations are avoidable.

#### 4. The "Report Export Failing" Defect & Repeat Contact Surge
* Out of 77 escalations in *Report export failing*, **30 were duplicates of a known defect (38.96%)**.
* Repeat contacts (same client and category within 14 days) surged from **14.87% in July** to **17.97% in August** and **24.83% in September**. 1 in 4 September tickets was a repeat contact, heavily concentrated in report export crashes and billing timeouts.

---

## Part 2: Define Success — What Does "Better" Look Like?

Success means reducing customer-visible open backlog by eliminating avoidable escalations and stopping repeat contacts at L1.

### Week-to-Week Operational Scorecard

| Metric | Business Definition | Current Baseline (Q3) | 30-Day Target | 60-Day Target | Measurement Cadence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Avoidable Escalation Rate** | Share of escalated tickets closed without an engineering fix | **56.58%** | **$< 35.0\%$** | **$< 20.0\%$** | Weekly |
| **Net Weekly Backlog** | Tickets created minus tickets closed per week | **+21.4 / wk** (growing) | **$\le 0$ / wk** | **Negative** (clearing) | Weekly |
| **Open Backlog Count** | Total open tickets at end-of-week | **48 tickets** (as of Sep 30) | **$< 25$ tickets** | **$< 15$ tickets** | Weekly (EOW) |
| **Ticket Reopen Rate** | Share of closed tickets reopened by client | **18.28%** (Karan: 29.5%) | **$< 12.0\%$** | **$< 8.0\%$** | Weekly |
| **14-Day Repeat Contact Rate** | Same client & category contact within 14 days | **24.83%** (September) | **$< 16.0\%$** | **$< 10.0\%$** | Weekly |
| **First-Contact Resolution (FCR)**| Resolved by L1 without escalation or reopen | **51.18%** | **$> 65.0\%$** | **$> 75.0\%$** | Weekly |
| **CSAT Response Rate** | Rated tickets / total closed tickets | **44.88%** (55.1% missing) | **$> 65.0\%$** | **$> 75.0\%$** | Monthly |

---

## Part 3: Build a v0 — User Selection, Tool Design & Why It Works

### Targeted User: **The L1 Support Agent & Meera (Support Lead)**
* **Why this user?** The escalation decision is made exclusively by L1 support. Once a ticket enters the engineering queue, the context-switching penalty and 40+ hour delay have already occurred. Equipping L1 agents with real-time decision support at the point of triage intercepts avoidable handoffs before they enter Tier 3 engineering.

### What We Built: The RideOps Escalation Gate (`app.py`)
A working internal web application (built on Streamlit) powered by our production-trained Machine Learning model (`avoidable_escalation_gate.joblib`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RIDEOPS LIVE ESCALATION GATE (v0)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. TICKET TRIAGE CHECKER (Agent Interface)                                  │
│    • Inputs: Category, Priority, Client Tier, Channel, Agent, Description   │
│    • Model Scoring: Evaluates 10 pre-escalation features in real-time       │
│    • Operating Threshold: Cutoff at 0.55 probability                        │
│                                                                             │
│    [SCENARIO A: P(Avoidable) = 0.74 >= 0.55]                                │
│    🚨 GATE ACTIVATED: HIGH RISK OF AVOIDABLE ESCALATION                     │
│    Dynamic Actionable Checklist:                                            │
│    [!] Known Issue Detected: "Report export timeout" microservice bug.      │
│        Do NOT escalate. Link client to Incident #ENG-402 banner.            │
│    [ ] Verify client has downloaded CSV via Chrome Incognito.               │
│    [ ] Check if client permissions were modified this week.                 │
│                                                                             │
│    [SCENARIO B: P(Avoidable) = 0.22 < 0.55]                                 │
│    ✅ GATE PASSED: LEGITIMATE ENGINEERING DEFECT                           │
│    Route immediately to Tier 3 Engineering Queue.                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. OPS INTELLIGENCE COCKPIT (Meera & Ritika Interface)                      │
│    • Live Open Backlog: Real-time filtering of the 48 open tickets.         │
│    • The "Karan Check": Visual speed vs. reopen rate trade-off tracker.     │
│    • The "Rahul Tracker": Actual vs. Expected escalation ratio monitoring.  │
│    • Repeat Contact Radar: Top 10 repeat clients and category drivers.      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Machine Learning Validation (Zero Data Leakage & Two-Model Strategy)
* **Leakage Guard**: Enforces strict isolation—features post-dating escalation (`eng_outcome`, `eng_handoffs`, `resolution_hrs`, `csat_score`) are strictly forbidden.
* **Model 1 (Historical Escalation Audit, N=182 Sep Holdout)**:
  * **ROC-AUC**: **0.5460** | **PR-AUC**: **0.6376** (vs. 0.5665 baseline)
  * **Recall**: **54.05%** | **Precision**: **64.52%** | **F1**: **0.588**
  * *Purpose:* Enables Meera to conduct retrospective audits of avoidable escalation patterns and agent coaching needs.
* **Model 2 (Live Pre-Escalation Gate, N=503 Sep Holdout)**:
  * **ROC-AUC**: **0.6461** | **PR-AUC**: **0.9278** (vs. 0.9164 baseline)
  * **Precision**: **90.09%** | **Recall**: **72.77%** | **F1**: **0.805**
  * *Purpose:* Operational live triage at incoming ticket evaluation. At operating threshold 0.82, over 90% of flagged tickets are confirmed resolvable at L1, preventing premature engineering context switching.
* **Human-in-the-Loop Governance**: All live gate decisions and manager overrides are permanently logged to SQLite (`data/overrides.db`) for operational tracking.

---

## Part 4: The Four-Week Plan & Deliberate Non-Actions

### The 4-Week Implementation Plan

| Week | Core Focus & Operational Activities | Key Deliverables & Milestones |
| :--- | :--- | :--- |
| **Week 1** | **Backlog Monitoring, Ageing Indicators & KPI Validation** | Deploy weekly intake vs. closure cockpit; establish ticket ageing bands (<24h, 24–48h, 48–72h, >72h); validate SLA definitions and baseline metrics with Meera and Ritika. Deploy hotfix for `#ENG-402` (Report Export) and resolve 30 duplicate escalations. |
| **Week 2** | **Known-Issue Lookup & CSV Data Upload Functionality** | Integrate active known-issue reference registry (`ISS-101` to `ISS-106`) into L1 live triage gate; launch CSV upload and schema validation center to enable testing with ongoing weekly ticket extracts. |
| **Week 3** | **L1 Agent Pilot & Feedback Collection** | Pilot the Live Escalation Gate in advisory mode with selected L1 agents (focusing coaching on Rahul T to calibrate his 1.79× escalation ratio and Karan B to reduce his 29.5% reopen rate); monitor persistent override logging in SQLite. |
| **Week 4** | **Operational Impact Measurement & Release Refinement** | Measure operational metrics (Avoidable Escalation Rate, Net Backlog change, CSAT response rate, agent override rates); refine diagnostic recommendations based on logged agent feedback; transition to standard operational release. |

### What We Deliberately Choose NOT To Do (Trade-Offs & Judgement)

1. **Automatic Escalation Blocking**:
   * *Why:* The gate operates strictly as an **advisory decision-support system**, not an automated blocker. Overly rigid auto-blocks alienate support agents and risk stalling genuine catastrophic outages. Every decision retains human approval with manager override tracking.
2. **Unnecessary Hiring (Support or Engineering)**:
   * *Why:* Ritika has zero budget expansion. More critically, adding headcount treats symptoms rather than root causes. Funneling more volume into an uncalibrated triage pipeline would only amplify the handoff bottleneck.
3. **Complex Microservices Architecture or Heavy External Infra**:
   * *Why:* The tool must be maintainable, self-contained, and lightweight. We chose SQLite for persistence and Streamlit for interface rather than spinning up complex microservices, Redis clusters, or external databases.
4. **Unnecessary Deep Learning or Large Language Model (LLM) Integration**:
   * *Why:* Tabular Logistic Regression and TF-IDF n-grams achieve a robust 0.928 PR-AUC on live triage with zero latency, complete explainability, and determinism. Deep learning would introduce unnecessary operational cost, opacity, and maintenance overhead without measurable accuracy gains.
5. **Claiming Backlog Reduction Without Actual Operational Evidence**:
   * *Why:* Backlog reduction is an operational outcome, not an ML metric. We measure true success through week-on-week closed tickets, median and P90 resolution times, and customer satisfaction (CSAT), rather than assuming model deployment automatically clears tickets.
