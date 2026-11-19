# RideOps Escalation Gate

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Pipeline](https://img.shields.io/badge/pipeline-passing-brightgreen.svg)](run_pipeline.py)
[![Status](https://img.shields.io/badge/status-production--ready-success.svg)]()

> **Predictive Escalation Gate, Operational Intelligence & Triage Analytics for RideOps Support Tickets**

---

## 1. Executive Summary & Problem Context

RideOps support operations observed substantial latency in resolving high-priority customer tickets despite adding capacity. A comprehensive diagnostic across **1,444 Q3 tickets (July 2 – September 30, 2026)** revealed that:
1. **The Avoidable Escalation Bottleneck**: **33.66%** of all support tickets (486) are escalated to Tier 3 engineering. However, **56.58% (~57%)** of these escalations are **avoidable** (resolved as configuration issues, insufficient information, user errors, or duplicates).
2. **Resolution Time Asymmetry**: Escalated tickets account for only 33.7% of volume but consume **70.54% (~71%)** of all customer-facing resolution hours.
3. **Engineering Handoff Penalty**: Each engineering handoff causes an exponential resolution time explosion:
   * **0 handoffs (L1 only)**: Median **12.4h** (P90: 29.5h)
   * **1 handoff**: Median **33.8h** (P90: 71.4h)
   * **2 handoffs**: Median **54.9h** (P90: 94.6h)
   * **3 handoffs**: Median **66.1h** (P90: 104.9h)
4. **Repeat Contact Surge**: Repeat contacts surged from **14.9% in July** to **24.8% in September**, heavily concentrated in report export failures and payment billing issues.

To resolve this, the **RideOps Escalation Gate** introduces:
- A complete, modular operational intelligence analytics engine.
- A leakage-free Machine Learning triage gate that scores tickets at the moment of proposed escalation, accurately filtering avoidable escalations back to L1 before engineering context-switching occurs.

---

## 2. Repository Layout

```text
rideops-escalation-gate/
├── config/
│   └── config.yaml                     # SLA targets, paths, thresholds, and business rules
├── data/
│   ├── raw/
│   │   ├── rideops_support_tickets.csv # Raw support ticket records (n = 1,444)
│   │   └── rideops_data_dictionary.csv # Metadata schema dictionary
│   └── processed/
│       └── tickets_clean.csv           # 39 engineered features and operational flags
├── models/
│   └── avoidable_escalation_gate.joblib# Serialized champion triage gate model
├── notebooks/                          # Original exploratory research notebooks
│   ├── 01_data_quality_and_feature_engineering.ipynb
│   ├── 02_ops_volume_speed_and_escalations.ipynb
│   ├── 03_csat_agents_and_repeat_contacts.ipynb
│   └── 04_hypothesis_tests_and_escalation_modeling.ipynb
├── reports/
│   ├── figures/                        # High-resolution (150 DPI) diagnostic visualizations
│   │   ├── c_volume_and_backlog.png
│   │   ├── de_speed_and_escalations.png
│   │   ├── fg_agent_benchmarking.png
│   │   └── j_model_calibration_and_features.png
│   ├── tables/                         # 20+ exported analysis tables (CSV)
│   ├── SUBMISSION_WRITEUP.md           # Official 4-part case study submission write-up
│   └── EXECUTIVE_SUMMARY.md            # Comprehensive executive decision brief
├── src/                                # Production Python source package
│   ├── data/                           # Ingestion & data quality suite (Section A)
│   ├── features/                       # Durations, flags, calendar, repeat contacts (Section B)
│   ├── analysis/                       # Volume, speed, escalation, CSAT, agent scorecards (Sections C-H)
│   ├── utils/                          # Statistical hypothesis testing (Section I)
│   ├── models/                         # ML gate models, leakage guard, baseline, NLP (Section J)
│   └── visualization/                  # Headless diagnostic figure generation
├── tests/                              # Automated unit & integration testing suite
│   ├── test_data_quality.py
│   ├── test_features.py
│   ├── test_analysis.py
│   ├── test_models.py
│   ├── test_pipeline_integration.py
│   └── run_tests.py                    # Fast automated test runner
├── app.py                              # Working v0 Streamlit web application
├── requirements.txt                    # Project dependencies
└── run_pipeline.py                     # Master pipeline execution CLI
```

---

## 3. Quickstart & Installation

### Environment Setup

Ensure Python 3.10 or higher is installed:

```bash
# Clone the repository
git clone https://github.com/your-org/rideops-escalation-gate.git
cd rideops-escalation-gate

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 4. Execution & Automated Pipeline

### 1. Launch the Interactive v0 Tool (Streamlit App)
To interact with the live Decision Support Gate and Operations Cockpit:

```bash
streamlit run app.py
```
* **L1 Support Agent View**: Test ticket escalation scenarios live, view avoidable probabilities, and receive dynamic diagnostic checklists.
* **Operations Cockpit**: Filter the 48 open backlog tickets, examine Karan's speed vs. quality trade-off, and track repeat-contact surges.

### 2. Run End-to-End Pipeline
Execute the full analytics, hypothesis testing, model training, and figure generation pipeline in a single command:

```bash
python run_pipeline.py
```

**Pipeline Steps Executed:**
1. **Ingestion & Validation**: Parses raw tickets, standardizes schemas, and audits data quality.
2. **Feature Engineering**: Derives durations, operational flags, calendar variables, and repeat-contact tags.
3. **Analytics Engine**: Generates 20+ CSV analytical tables across speed, backlog, CSAT, and agent benchmarks.
4. **Hypothesis Testing**: Computes 7 statistical tests ($\chi^2$, Mann-Whitney U, Kruskal-Wallis, Spearman, OLS).
5. **Machine Learning Gate**: Trains baseline, Logistic Regression, Random Forest, Gradient Boosting, TF-IDF, and Hybrid models; verifies 0 data leakage; exports champion model to `models/avoidable_escalation_gate.joblib`.
6. **Visualization**: Generates 4 publication-quality figures in `reports/figures/`.

### Run Test Suite
Run the test suite covering data quality, feature engineering, analysis, modeling, and pipeline integration:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 5. Summary of Key Analytical Findings

| Section | Focus Area | Benchmark / Metric | Verified Empirical Result | Key Insight |
| :--- | :--- | :--- | :--- | :--- |
| **A** | **Data Quality** | 0 duplicates, expected nulls | 0 duplicates; 958 non-escalated tickets with null outcome; 0 timestamp anomalies | Data passes all integrity checks. |
| **B** | **Repeat Contacts** | Jul: ~14.9%, Aug: ~18.0%, Sep: ~24.8% | Jul: **14.87%**, Aug: **17.97%**, Sep: **24.83%** | Escalated repeat rate driven by report exports & billing. |
| **C** | **Backlog & Volume** | Intake vs. closure | Intake grew from 85/wk to 157/wk; 48 open tickets as of Sep 30 | Net backlog positive due to intake surge. |
| **D** | **Speed & SLA** | First response target P1 $\le 1$h | Overall median FRT: 1.5h; P1 within SLA: **32.8%** | Critical need for automated triage routing. |
| **E** | **Escalation Load** | Escalated hours share ~71% | **70.54%** of total closed resolution hours; 56.58% avoidable | Avoidable escalations tie up Tier 3 engineering. |
| **E5** | **Duplicate Issues** | Report export failure standout | **30 duplicate escalations** (38.96% of category escalations) | Single known defect responsible for ~11% of avoidable escalations. |
| **F** | **CSAT Response** | ~55% non-response | **55.12% missing scores**; Enterprise clients respond at higher rates | CSAT suffers from non-response bias. |
| **G** | **Agent Benchmarking** | Rahul: 1.8× expected; Karan: 0.5× | Rahul T: **1.79×**; Karan B: **0.48×** (Case-mix adjusted) | Rahul over-escalates; Karan shows speed vs. quality trade-off (29.5% reopen rate). |
| **I** | **Hypothesis Tests** | Claims supported by p-values | All 7 tests significant ($p < 0.05$) | Validates that avoidable rates, handoff penalties, and volume trends are statistically genuine. |
| **J** | **ML Gate** | Temporal Split (Train Jul-Aug, Test Sep) | Model 1: ROC-AUC **0.546**, PR-AUC **0.638**; Model 2 (Live Gate): ROC-AUC **0.646**, PR-AUC **0.928** | Accurate pre-escalation triage and historical quality analysis. |

---

## 6. Machine Learning Architecture: Two-Model Strategy

The project deploys two distinct, complementary models addressing two different operational tasks:

### Model 1: Historical Escalation Review & Audit Model
* **Dataset**: 486 historically escalated tickets (Section J).
* **Target**: Was the historical escalation avoidable? (`is_avoidable_esc = 1` for non-fixed outcomes like config, how-to, duplicate, insufficient info; `0` for code/schema fixes).
* **Operational Purpose**: Enables Meera (Support Lead) to retrospectively audit escalation patterns, evaluate agent decision quality, and identify team coaching opportunities.
* **Temporal Holdout Evaluation (September 2026, N=182)**:
  * **Logistic Regression (Champion)**: ROC-AUC: **0.5460** | PR-AUC: **0.6376** (vs. 0.5665 baseline) | Precision: **64.5%** | Recall: **54.1%** | F1: **0.588**
  * **5-Fold Cross-Validation**: ROC-AUC: **0.5657** | PR-AUC: **0.6163** | Precision: **62.1%** | Recall: **58.9%** | F1: **0.604**
* **Saved Artifact**: `models/avoidable_escalation_gate.joblib`

```text
Model 1 (Temporal Split)     ROC-AUC   PR-AUC   Precision   Recall      F1
Baseline (Category Rate)      0.4285   0.5665      0.5086   0.5315  0.5198
Logistic Regression (Champion)0.5460   0.6376      0.6452   0.5405  0.5882
Random Forest                 0.5152   0.6111      0.6081   0.4054  0.4865
Gradient Boosting             0.5325   0.6113      0.5765   0.4414  0.5000
TF-IDF Text Model             0.4434   0.5501      0.5741   0.5586  0.5662
Hybrid (Tabular + TF-IDF)     0.5351   0.6260      0.6042   0.5225  0.5604
```

### Model 2: Live Escalation Triage Gate
* **Dataset**: Population of all closed tickets (N = 1,304 clean ground truth records; open tickets excluded to prevent censoring bias).
* **Target Definition**: Does the newly received ticket require engineering intervention?
  * `0`: Confirmed code/schema defect requiring engineering fix (`Fixed`).
  * `1`: Avoidable / L1-resolvable (clean FCR non-escalated tickets + avoidable escalations).
* **Pre-Escalation Feature Set**: Evaluated solely on features available at live triage time (category, priority, channel, tier, agent, weekday, response speed, hour, repeat contact, client ticket history, text description). Zero post-escalation leakage.
* **Temporal Holdout Evaluation (September 2026, N=503)**:
  * **Logistic Regression (Champion)**: ROC-AUC: **0.6461** | PR-AUC: **0.9278** | Precision: **90.1%** | Recall: **72.8%** | F1: **0.805**
  * **Operating Cutoff**: Threshold = **0.82** (tuned to achieve >90% precision in flagging avoidable escalations).
* **Saved Artifact**: `models/live_triage_gate.joblib`

```text
Model 2 (Live Triage Holdout)ROC-AUC   PR-AUC   Precision   Recall      F1
Baseline (Category Rate)      0.6351   0.9164      0.9038   0.7094  0.7949
Logistic Regression (Champion)0.6461   0.9278      0.9009   0.7277  0.8051
Random Forest                 0.6324   0.9141      0.8997   0.7391  0.8116
Gradient Boosting             0.6046   0.9163      0.8750   0.7368  0.8000
Hybrid (Tabular + TF-IDF)     0.6337   0.9199      0.8947   0.7391  0.8095
```

---

## 7. Persistent Override Tracking & Known-Issue Management

Rather than acting as a hard automated barrier, the RideOps Escalation Gate operates as an **advisory decision-support system**:
1. **Advisory Gate**: Agents can override recommendations with manager sign-off.
2. **Persistent SQLite Store**: All decisions, probabilities, recommendations, and override justifications are logged permanently to `data/overrides.db`.
3. **Known-Issue Reference Registry**: Matches active platform defects (e.g., `#ENG-402`, `#ENG-318`, `#ENG-245`) to provide immediate workarounds and bypass duplicate engineering tickets.
4. **Cockpit Monitoring**: Meera and Ritika track override rates, agent agreement percentages, and downstream outcomes in real time.

---

## 8. Four-Week Implementation Plan & Deliberate Non-Actions

### 4-Week Roadmap

| Week | Core Focus & Operational Activities | Key Deliverables & Milestones |
| :--- | :--- | :--- |
| **Week 1** | **Backlog Monitoring, Ageing Indicators & KPI Validation** | Deploy weekly intake vs. closure cockpit; establish ticket ageing bands (<24h, 24–48h, 48–72h, >72h); validate SLA definitions and baseline metrics with Meera and Ritika. Deploy hotfix for `#ENG-402` (Report Export) and resolve 30 duplicate escalations. |
| **Week 2** | **Known-Issue Lookup & CSV Data Upload Functionality** | Integrate active known-issue reference registry (`ISS-101` to `ISS-106`) into L1 live triage gate; launch CSV upload and schema validation center to enable testing with ongoing weekly ticket extracts. |
| **Week 3** | **L1 Agent Pilot & Feedback Collection** | Pilot the Live Escalation Gate in advisory mode with selected L1 agents (focusing coaching on Rahul T to calibrate his 1.79× escalation ratio and Karan B to reduce his 29.5% reopen rate); monitor persistent override logging in SQLite. |
| **Week 4** | **Operational Impact Measurement & Release Refinement** | Measure operational metrics (Avoidable Escalation Rate, Net Backlog change, CSAT response rate, agent override rates); refine diagnostic recommendations based on logged agent feedback; transition to standard operational release. |

### What We Deliberately Choose NOT To Do (Trade-Offs & Judgement)

1. **Automatic Escalation Blocking**: Retain human approval with manager override rather than hard blocking.
2. **Unnecessary Hiring (Support or Engineering)**: Headcount expansion treats symptoms and funnels more noise into the engineering queue.
3. **Complex Microservices Architecture or Heavy External Infra**: Maintain a self-contained, lightweight SQLite and Streamlit architecture.
4. **Unnecessary Deep Learning or LLM Integration**: Tabular Logistic Regression and TF-IDF achieve 0.928 PR-AUC with zero latency, full explainability, and no operational inference costs.
5. **Claiming Backlog Reduction Without Actual Operational Evidence**: Measure real success through week-on-week closed tickets, median and P90 resolution times, and customer satisfaction (CSAT).

---

## 9. License & Maintainers
Developed for RideOps Engineering & Support Operations. Distributed under the MIT License.
