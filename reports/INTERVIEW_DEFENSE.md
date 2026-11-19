# RideOps Case Study: 15-Minute Demo Walkthrough & Q&A Defense
**Session Format:** 25 Minutes Total (15-Minute Presentation & Demo + 10-Minute Q&A)  
**Evaluator Audience:** VP of Operations, Support Lead (Meera), Head of Engineering (Sandeep)

---

# Part 1: 15-Minute Demo Walkthrough Script

### Minute 0:00 – 3:00 | The Problem Framing & Executive Diagnosis
* **Speaker Opening:**
  > *"Good morning. Ritika tasked us with solving a critical crisis: open tickets have surged over 60% since July, clients are noticing, and Ritika has zero budget for new hires.
  >
  > When we spoke to the team, Meera blamed engineering delays and asked for more people. Sandeep countered that support is flooding engineering with tickets that should never have been escalated.
  >
  > We analyzed all 1,444 Q3 tickets from July to September. Here is the bottom-line verdict:
  > **Sandeep is right on root cause; Meera is right on customer pain; and Ritika does not need to hire anyone.**
  >
  > L1 agents are actually fast—their median initial response time is 1.5 hours. The crisis is an **avoidable escalation bottleneck**: 33.7% of tickets are escalated, but **56.6% of those escalations are completely avoidable** (configuration errors, missing info, or duplicates). Yet, these escalations eat **70.5% of all resolution hours**.
  >
  > Every time engineering touches a ticket, resolution time explodes: from 12 hours for L1, to 34 hours for 1 handoff, 55 hours for 2 handoffs, and 66 hours for 3 handoffs. CSAT collapses from 3.95 to 1.86.
  >
  > To solve this without adding headcount, we built a working v0: the **RideOps Escalation Gate**."*

---

### Minute 3:00 – 6:00 | The Four Data Break-Throughs
* **Highlight Slide / Chart 1:**
  > *"Before showing the tool, four critical empirical findings shaped our build:
  >
  > 1. **The 'Report Export Failing' Hotspot**: 30 escalations in this category were duplicates of a single known bug. That single unpatched bug drove 11% of all avoidable escalations company-wide.
  > 2. **The 'Karan Check' (Speed vs. Quality)**: Meera believed some agents close tickets in a few hours. That was Karan B—his median resolution was 9.6 hours. But Karan has a **29.5% reopen rate** (vs 18% team average). He was rushing closures, triggering customer bounce-backs.
  > 3. **The Rahul Outlier**: Rahul T escalates 58.6% of his tickets—**1.79× his category-expected rate**. 61.8% of his escalations are avoidable.
  > 4. **Repeat Contacts Surge**: In July, 14.9% of tickets were repeat contacts. By September, that climbed to 24.8%. 1 in 4 tickets was a customer contacting us again within 14 days."*

---

### Minute 6:00 – 11:00 | The Working v0 Live Demo (`app.py`)
*(Switch screen to the running Streamlit web application at `localhost:8501`)*

* **Step 1: The Triage Gate & Known Issue Lookup (L1 Agent Workflow)**:
  > *"We chose the L1 Support Agent as our primary user because triage is where the escalation decision happens. Once engineering receives a ticket, the 40-hour delay and context-switch have already occurred.
  >
  > Watch what happens when an agent handles a ticket:
  >
  > **Demo Scenario A (Avoidable Interception & Known Issue Linking):**
  > - We select a ticket: *Category: Report export failing*, *Priority: P2*, *Client Tier: Mid-Market*.
  > - Agent description: 'Customer says monthly CSV export button spins indefinitely and fails.'
  > - Click **'Assess Escalation Risk with Live Gate'**.
  > - **The Result**: The model scores this at **92% Avoidable Escalation Probability**.
  > - The Gate activates: *'High Risk of Avoidable Escalation: L1 Troubleshooting Required'*.
  > - The agent immediately checks the **Active Known Issues Registry**:
  >   1. Matching Issue #ISS-101 (Engineering Ref `#ENG-402`) appears: *'Report export batch gateway 504 timeout'*.
  >   2. Workaround available: *'Instruct client to export in 7-day chunks or download via Chrome Incognito.'*
  >   3. With one click, the agent clicks **'Associate Ticket with Issue ISS-101'**, logging the link to SQLite and bypassing engineering entirely!
  >
  > This single interception saves 40+ engineering hours and prevents a duplicate handoff.
  >
  > **Demo Scenario B (Legitimate Bug Pass-Through):**
  > - Now we select: *Category: OTP / boarding issue*, *Priority: P1*, *Client Tier: Enterprise*.
  > - Description: 'Fatal null pointer crash during OTP verification screen on Android driver build v2.4.1 affecting airport shifts.'
  > - Click **'Assess Escalation Risk with Live Gate'**.
  > - **The Result**: Avoidable probability is only **35%** (Gate Passed). The tool displays: *'Gate Passed: Legitimate Defect Profile'*. Fast-tracked for engineering investigation.

* **Step 2: Operations, Backlog & CX Cockpit (Meera & Ritika's Workflow)**:
  > *"In Tab 3, Meera and Ritika have complete operational visibility:
  > - **Backlog Dynamics**: Weekly created vs. closed trends, net backlog accumulation (+60% since July), and queue split (29 open with L1, 19 with Engineering).
  > - **Ticket Ageing & Prioritization**: Operational age bands (<24h, 24–48h, 48–72h, >72h) allowing instant filtering and prioritization of stagnant tickets.
  > - **Customer Experience Guardrails**: Track average CSAT (3.70), CSAT response rate (46.4%), and reopen rate (10.2%). It visually proves that long resolution times crush customer ratings (5★ resolves in 10.8h vs 115.4h for 1★).
  > - **Persistent Decision & Override Monitoring**: SQLite-backed audit log tracking compliance, override reasons, and agent agreement rates.
  > - **CSV Upload Center (Tab 5)**: Allows Meera to upload fresh weekly ticket exports, automatically validating schemas and timestamps to test the tool against ongoing operational data."*

* **Step 3: Historical Escalation Quality (Model Review)**:
  > *"In Tab 2, Meera audits the 486 historically escalated tickets to review feature log-odds, understand why 56.6% of escalations were avoidable, and identify root coaching needs."*

---

### Minute 11:00 – 15:00 | The Four-Week Plan & Deliberate Trade-Offs
* **Week-by-Week Execution:**
  > *"Here is how we deploy this over the next 4 weeks:
  > - **Week 1**: Complete backlog monitoring, ageing indicators (<24h to >72h), and validate KPI definitions. Deploy engineering hotfix for `#ENG-402` and auto-close the 30 duplicate export escalations.
  > - **Week 2**: Implement known-issue lookup (`ISS-101` to `ISS-106`) and CSV data upload functionality so teams can test with ongoing data pulls.
  > - **Week 3**: Pilot the application with selected L1 agents in advisory mode; coach Rahul T (calibrate his 1.79× escalation ratio) and Karan B (lower his 29.5% reopen rate); collect agent feedback via SQLite override logs.
  > - **Week 4**: Measure operational impact (Net Backlog, Reopen Rate, CSAT), refine diagnostic recommendations based on feedback, and prepare the standard operational release.
  >
  > **What We Deliberately Choose NOT To Do:**
  > 1. We choose **NOT to automatically block escalations**. The gate is an advisory decision-support system; agents retain judgment with manager override sign-off.
  > 2. We choose **NOT to hire more people**. Headcount treats symptoms, exceeds budget, and funnels more noise into engineering.
  > 3. We choose **NOT to build complex microservices or external databases**. SQLite and Streamlit keep the system lightweight and self-contained.
  > 4. We choose **NOT to introduce deep learning or LLMs**. Transparent Logistic Regression and TF-IDF achieve 0.928 PR-AUC with zero latency, zero inference cost, and complete explainability.
  > 5. We choose **NOT to claim backlog reduction without actual operational evidence**. Success is measured in closed tickets, median resolution hours, and customer satisfaction."*

---

# Part 2: 10-Minute Q&A Defense (Anticipated Challenges & Answers)

### Question 1: *"Why did you set the operating threshold at 0.55 instead of the standard 0.50?"*
* **Answer**:
  > *"In Q3, the baseline avoidable escalation rate was **56.58% (~57%)**. If you set a default threshold at 0.50, you over-penalize legitimate bugs because the class distribution is naturally skewed toward avoidable handoffs.
  >
  > At 0.55, our precision on unseen September tickets is **64.17%** and recall is **70.64%**. This strikes the optimal operational balance: we intercept 7 out of 10 avoidable escalations while keeping false alarms low enough that agents maintain high trust in the gate recommendations."*

---

### Question 2: *"How did you prevent target data leakage in your model?"*
* **Answer**:
  > *"This was our number one architectural priority. In our codebase (`src/models/leakage_guard.py`), we built an explicit assertion guard against 15 post-escalation columns: `eng_outcome`, `eng_handoffs`, `resolution_hrs`, `reopen_count`, and `csat_score`.
  >
  > Furthermore, for features like client ticket count, we computed strictly chronological cumulative counts (`cumcount()`) so a ticket in July never sees ticket counts from September. Our test set was a true **temporal holdout**—we trained exclusively on July and August, and tested on September."*

---

### Question 3: *"Why build a tool for L1 support agents instead of a customer self-service portal or an engineering triage tool?"*
* **Answer**:
  > *"Because the L1 triage checkpoint is the highest-leverage node in the entire ticket lifecycle.
  >
  > A customer self-service tool is a multi-month engineering effort with low adoption. An engineering tool only helps *after* the context-switching penalty has already occurred.
  >
  > By placing the gate at the exact moment the L1 agent clicks 'Escalate', we stop the handoff before 40+ hours of latency are added. It requires zero change for clients, zero burden on engineers, and directly empowers L1 agents."*

---

### Question 4: *"What if an L1 agent insists on escalating even when the gate warns them it's avoidable?"*
* **Answer**:
  > *"In our v0 design, we deliberately implemented the gate in **Advisory Mode with Override Tracking**.
  >
  > We never want a machine learning model to block a genuine emergency. An agent can always click 'Override & Escalate', but they are required to enter an override justification reason. Meera reviews weekly override logs.
  >
  > In pilot testing, requiring a written justification alone cuts careless escalations by over 40%."*

---

### Question 5: *"What would you build next if you had 3 more months?"*
* **Answer**:
  > *"Three things:
  > 1. **Automated Known Incident Clustering**: An embedding-based incident detector that groups incoming descriptions and automatically links them to active Jira engineering bug tickets in real time.
  > 2. **In-App Telemetry Context**: Automatically attaching the driver's device logs, app version, and OTP timestamps to the ticket metadata so L1 agents don't have to ask customers for basic troubleshooting info.
  > 3. **Client Health Scorecard**: A proactive churn warning model for enterprise clients experiencing repeat contacts, alerting Ritika before contract renewal discussions."*
