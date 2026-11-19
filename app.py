"""
RideOps Support Escalation Gate - Interactive Decision Support System
Addresses the core leadership challenge: "Bring open tickets down this quarter without increasing headcount."

System Architecture:
- Tab 1: 🎯 L1 Agent: Live Triage Gate & Known Issues (Pre-Escalation Decision Support & Defect Linking)
- Tab 2: 🔍 Historical Escalation Quality (Post-Escalation Avoidability Analysis)
- Tab 3: 📊 Operations, Backlog & CX Cockpit (Backlog Dynamics, Ticket Ageing, CX Metrics & Override Audit)
- Tab 4: 🧑‍💻 Agent Quality & The Karan Check (Case-Mix Adjusted Benchmarking)
- Tab 5: 📁 Data Refresh & CSV Upload (Schema Validation, Duplicate Detection & Live Dataset Switch)
"""

from pathlib import Path
import os
import sys
import datetime
import numpy as np
import pandas as pd
import joblib
import streamlit as st

# Setup paths and environment
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    MODEL_PATH,
    LIVE_MODEL_PATH,
    PROCESSED_DATA_PATH,
    DEFAULT_MODEL_THRESHOLD,
    LIVE_OPERATING_THRESHOLD,
    CANONICAL_CATEGORIES,
    CANONICAL_CHANNELS,
    CANONICAL_CLIENT_TIERS,
    CANONICAL_AGENTS,
    CANONICAL_PRIORITIES,
    CAT_FEATURES,
    NUM_FEATURES,
    TEXT_FEATURE,
    TABLES_DIR,
    FIGURES_DIR
)
from src.logging import (
    init_override_db,
    log_escalation_decision,
    get_logged_decisions,
    compute_override_metrics,
    seed_sample_overrides_if_empty
)
from src.data.known_issues import (
    load_known_issues,
    search_known_issues,
    get_known_issue_by_id
)
from src.data.upload_validator import (
    validate_uploaded_tickets_csv
)
from src.analysis import (
    compute_weekly_volume_and_backlog,
    assign_age_band
)

# Page configuration
st.set_page_config(
    page_title="RideOps Escalation Gate v0",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 12px;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_live_gate_model():
    """Load pre-trained Model 2: Live Triage Gate pipeline."""
    if LIVE_MODEL_PATH.exists():
        try:
            return joblib.load(LIVE_MODEL_PATH)
        except Exception:
            return None
    return None


@st.cache_resource
def load_historical_model():
    """Load pre-trained Model 1: Historical Escalation Avoidability pipeline."""
    if MODEL_PATH.exists():
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return None
    return None


@st.cache_data
def load_ticket_data():
    """Load cleaned support ticket dataset."""
    if PROCESSED_DATA_PATH.exists():
        df = pd.read_csv(PROCESSED_DATA_PATH)
        for col in ["created_at", "first_response_at", "first_closed_at", "final_closed_at", "week_start"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    return pd.DataFrame()


# Initialize data & SQLite override tracking
seed_sample_overrides_if_empty()
live_model = load_live_gate_model()
hist_model = load_historical_model()

# Support dynamic uploaded dataset via session state
if "active_df" not in st.session_state:
    st.session_state["active_df"] = load_ticket_data()
df = st.session_state["active_df"]

# Sidebar Navigation & System Status
st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=64)
st.sidebar.title("RideOps Gate v0")
st.sidebar.caption("Predictive Escalation Gate & Operations Cockpit")

view_mode = st.sidebar.radio(
    "Navigation Mode",
    [
        "🎯 L1 Agent: Live Triage Gate",
        "🔍 Historical Escalation Quality",
        "📊 Operations & Backlog Cockpit",
        "🧑‍💻 Agent Quality & The Karan Check",
        "📁 Data Refresh & CSV Upload"
    ]
)

st.sidebar.divider()
st.sidebar.markdown("**System Architecture & Models**")
st.sidebar.markdown(f"• **Live Triage Gate:** `{'Ready' if live_model is not None else 'Unavailable'}`")
st.sidebar.markdown(f"• **Live Cutoff Threshold:** `{LIVE_OPERATING_THRESHOLD}`")
st.sidebar.markdown("• **Live Gate Sep Holdout:** `ROC-AUC: 0.646 | PR-AUC: 0.928`")
st.sidebar.markdown(f"• **Historical Quality Model:** `{'Ready' if hist_model is not None else 'Unavailable'}`")
st.sidebar.markdown("• **Historical Sep Holdout:** `ROC-AUC: 0.546 | PR-AUC: 0.638`")
st.sidebar.markdown(f"• **Active Tickets Loaded:** `{len(df):,}`")


# ==============================================================================
# TAB 1: LIVE TRIAGE GATE & KNOWN ISSUES (FOR L1 SUPPORT AGENTS)
# ==============================================================================
if view_mode == "🎯 L1 Agent: Live Triage Gate":
    st.title("🎯 L1 Support Agent: Live Escalation Gate")
    st.markdown(
        "Evaluate incoming support tickets before escalation to prevent unnecessary engineering handoffs. "
        "The model estimates whether this ticket is an **avoidable escalation / L1-resolvable** or a "
        "**legitimate engineering defect** requiring Tier 3 intervention."
    )

    preset = st.selectbox(
        "📋 Load a Pre-configured Ticket Scenario (or edit fields below):",
        [
            "Custom Input",
            "Scenario A: 'Report export failing' (Active Known Issue ENG-402 - High Avoidable Risk)",
            "Scenario B: 'OTP / boarding issue' (Core Flow Defect - Legitimate Defect Risk)",
            "Scenario C: 'Billing / invoice discrepancy' (Rate Card Config - High Avoidable Risk)",
            "Scenario D: 'Live tracking / GPS incorrect' (Driver Telemetry - L1 Diagnostic Required)"
        ]
    )

    # Pre-populate defaults matching exact canonical taxonomies
    if preset == "Scenario A: 'Report export failing' (Active Known Issue ENG-402 - High Avoidable Risk)":
        d_cat = "Report export failing"
        d_prio = "P2"
        d_chan = "Client portal"
        d_tier = "Mid-market"
        d_agent = "Rahul T"
        d_day = "Tuesday"
        d_frt = 2.5
        d_hour = 14
        d_rep = 1
        d_prior = 6
        d_text = "Transport admin reports monthly MIS CSV export spinning indefinitely and failing with gateway 504 timeout."
    elif preset == "Scenario B: 'OTP / boarding issue' (Core Flow Defect - Legitimate Defect Risk)":
        d_cat = "OTP / boarding issue"
        d_prio = "P1"
        d_chan = "WhatsApp"
        d_tier = "Enterprise"
        d_agent = "Vikram S"
        d_day = "Monday"
        d_frt = 0.5
        d_hour = 9
        d_rep = 0
        d_prior = 12
        d_text = "Fatal null pointer crash during OTP verification screen on Android driver build v2.4.1 affecting airport shifts."
    elif preset == "Scenario C: 'Billing / invoice discrepancy' (Rate Card Config - High Avoidable Risk)":
        d_cat = "Billing / invoice discrepancy"
        d_prio = "P3"
        d_chan = "Email"
        d_tier = "SMB"
        d_agent = "Karan B"
        d_day = "Wednesday"
        d_frt = 1.0
        d_hour = 11
        d_rep = 1
        d_prior = 2
        d_text = "Client disputing extra toll surcharge billed on night shift roster. Needs rate card config reconciliation."
    elif preset == "Scenario D: 'Live tracking / GPS incorrect' (Driver Telemetry - L1 Diagnostic Required)":
        d_cat = "Live tracking / GPS incorrect"
        d_prio = "P2"
        d_chan = "Phone"
        d_tier = "Enterprise"
        d_agent = "Sneha M"
        d_day = "Thursday"
        d_frt = 1.2
        d_hour = 16
        d_rep = 0
        d_prior = 5
        d_text = "Fleet manager observes cab marker lagging by 8 minutes on live dispatch map for shift 3."
    else:
        d_cat = "Billing / invoice discrepancy"
        d_prio = "P2"
        d_chan = "Email"
        d_tier = "Enterprise"
        d_agent = "Rahul T"
        d_day = "Wednesday"
        d_frt = 1.5
        d_hour = 11
        d_rep = 0
        d_prior = 3
        d_text = "Client reports invoice calculation error on weekend roster trip."

    # Input Form
    with st.form("triage_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.selectbox("Ticket Category", CANONICAL_CATEGORIES, index=CANONICAL_CATEGORIES.index(d_cat) if d_cat in CANONICAL_CATEGORIES else 0)
            priority = st.selectbox("Priority", CANONICAL_PRIORITIES, index=CANONICAL_PRIORITIES.index(d_prio))
            channel = st.selectbox("Channel", CANONICAL_CHANNELS, index=CANONICAL_CHANNELS.index(d_chan))

        with col2:
            client_tier = st.selectbox("Client Tier", CANONICAL_CLIENT_TIERS, index=CANONICAL_CLIENT_TIERS.index(d_tier))
            # Include an explicit (Other / New Agent) option for handling unseen agents
            agent_options = CANONICAL_AGENTS + ["(Other / New Agent)"]
            agent_index = agent_options.index(d_agent) if d_agent in agent_options else len(agent_options) - 1
            assigned_agent = st.selectbox("Assigned L1 Agent", agent_options, index=agent_index)
            weekday = st.selectbox("Weekday Raised", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(d_day))

        with col3:
            hrs_to_frt = st.number_input("Hours to First Response", min_value=0.0, max_value=72.0, value=float(d_frt), step=0.5)
            hour_of_day = st.slider("Hour of Day (0-23)", 0, 23, int(d_hour))
            is_repeat = st.checkbox("Repeat Contact within 14 Days?", value=bool(d_rep))
            client_prior = st.number_input("Client Historical Tickets", min_value=0, max_value=200, value=int(d_prior))

        description = st.text_area("Ticket Description / Client Message", value=d_text, height=90)
        submitted = st.form_submit_button("🚀 Assess Escalation Risk with Live Gate", use_container_width=True)

    # Section 5: Known-Issue Search & Quick Association Panel
    st.markdown("---")
    st.subheader("🔍 Active Known Issues & Workaround Lookup")
    with st.expander("Explore Known Issues & Outage Registry (Bypass Duplicate Escalations)", expanded=("report export" in category.lower())):
        k_search = st.text_input("Search Known Issues by keyword, engineering ID, or status:", value="ENG-402" if "report export" in category.lower() else "")
        known_df = search_known_issues(query=k_search, category="" if k_search else category)

        if not known_df.empty:
            for _, krow in known_df.iterrows():
                with st.container():
                    st.markdown(f"**[{krow['issue_id']}] {krow['issue_title']}** (Ref: `{krow['eng_reference']}` | Status: `{krow['status']}`)")
                    st.markdown(f"• **Category:** `{krow['category']}`")
                    st.markdown(f"• **Description:** {krow['description']}")
                    st.info(f"💡 **Recommended Client Workaround:** {krow['workaround']}")
                    if st.button(f"🔗 Associate Ticket with Issue {krow['issue_id']} (Bypass Escalation)", key=f"link_{krow['issue_id']}"):
                        rec_id = log_escalation_decision(
                            ticket_id=f"SUP-{np.random.randint(20000, 29999)}",
                            agent_id=assigned_agent,
                            category=category,
                            priority=priority,
                            client_tier=client_tier,
                            predicted_probability=0.99,
                            model_recommendation="Known Defect Identified: Escalation Bypassed",
                            actual_decision="Resolved at L1 (Linked to Known Issue)",
                            is_override=False,
                            override_reason=f"Linked to active issue {krow['issue_id']} ({krow['eng_reference']})",
                            known_issue_id=krow["issue_id"]
                        )
                        st.success(
                            f"✅ Ticket associated with **{krow['issue_id']} ({krow['eng_reference']})**! "
                            f"Decision logged to SQLite (Record ID #{rec_id}). Send the recommended workaround to client."
                        )
                    st.markdown("---")
        else:
            st.write("No matching known issues found for this query.")

    # Prediction & Gate Verdict
    if submitted or preset != "Custom Input":
        # Handle unknown agent mapping gracefully
        model_agent_val = assigned_agent if assigned_agent in CANONICAL_AGENTS else "Unknown"

        input_record = pd.DataFrame([{
            "category": category,
            "priority": priority,
            "channel": channel,
            "client_tier": client_tier,
            "assigned_agent": model_agent_val,
            "weekday": weekday,
            "hrs_to_first_response": hrs_to_frt,
            "hour_of_day": hour_of_day,
            "is_repeat_contact": int(is_repeat),
            "client_prior_tickets": client_prior,
            "description": description
        }])

        st.subheader("Decision Support Verdict")

        # Model Inference
        if live_model is not None:
            prob_avoidable = float(live_model.predict_proba(input_record)[0, 1])
            is_gate_active = prob_avoidable >= LIVE_OPERATING_THRESHOLD

            col_res1, col_res2 = st.columns([1, 2])
            with col_res1:
                st.metric(
                    label="Estimated Avoidable / L1-Resolvable Probability",
                    value=f"{prob_avoidable*100:.1f}%",
                    delta=f"Live Gate Cutoff: {LIVE_OPERATING_THRESHOLD*100:.0f}%",
                    delta_color="inverse" if is_gate_active else "normal"
                )
                st.progress(prob_avoidable)

            with col_res2:
                if is_gate_active:
                    st.warning("⚠️ **GATE ACTIVATED: L1 TROUBLESHOOTING REQUIRED**")
                    st.markdown(
                        f"This ticket has a **{prob_avoidable*100:.1f}% probability** of being resolvable at Level 1 without engineering code changes. "
                        "Please perform the required diagnostic checks before attempting escalation."
                    )
                else:
                    st.success("✅ **GATE PASSED: LEGITIMATE DEFECT PROFILE**")
                    st.markdown(
                        f"This ticket has an avoidable probability of **{prob_avoidable*100:.1f}%** (below {LIVE_OPERATING_THRESHOLD*100:.0f}% threshold). "
                        "Issue indicates a core code, schema, or infrastructure failure."
                    )
        else:
            prob_avoidable = None
            is_gate_active = True
            st.warning(
                "⚠️ **Live Triage Model Unavailable**: Checkpoint file not found at `models/live_triage_gate.joblib`. "
                "Defaulting to standard manual L1 triage checklist."
            )

        # Category-Specific Troubleshooting Checklist
        st.markdown("---")
        st.subheader("📋 L1 Diagnostic & Troubleshooting Checklist")
        if "billing" in category.lower():
            st.markdown("• [ ] Verify rate card parameters against signed client contract schedule.")
            st.markdown("• [ ] Check if night shift surcharge or toll multiplier was toggled during roster generation.")
            st.markdown("• [ ] Request itemized trip billing CSV from client to verify individual discrepancy lines.")
        elif "roster" in category.lower() or "booking" in category.lower():
            st.markdown("• [ ] Verify client roster upload CSV format against standard UTF-8 template.")
            st.markdown("• [ ] Check for duplicate employee IDs or unmapped pickup geocodes in shift rows.")
            st.markdown("• [ ] Re-trigger roster validation batch before escalating to database administrator.")
        elif "live tracking" in category.lower() or "gps" in category.lower():
            st.markdown("• [ ] Verify driver mobile app background location permissions and battery optimization settings.")
            st.markdown("• [ ] Confirm driver device connectivity with carrier telemetry stream.")
            st.markdown("• [ ] Check if issue is isolated to a single driver or affects fleet-wide dispatch.")
        elif "otp" in category.lower() or "boarding" in category.lower():
            st.markdown("• [ ] Verify if carrier SMS gateway outage is logged with telecom provider.")
            st.markdown("• [ ] Check if driver and passenger app build versions are up-to-date (minimum v2.4.0).")
            st.markdown("• [ ] Test passenger boarding manual override workflow in admin dispatch console.")
        else:
            st.markdown("• [ ] Verify client browser cache, cookies, and app version.")
            st.markdown("• [ ] Attempt to reproduce the issue with identical client user role permissions.")
            st.markdown("• [ ] Attach complete reproduction steps, client screenshots, and error logs.")

        # Persistent Decision & Override Submission Form (SQLite Backed)
        st.markdown("---")
        st.subheader("✍️ Record Agent Triage Decision & Manager Override")
        st.caption("All triage decisions are permanently logged to SQLite for operational monitoring by Meera and Ritika.")

        with st.form("decision_logging_form"):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                ticket_id_input = st.text_input("Ticket ID", value=f"SUP-{np.random.randint(12000, 19999)}")
                actual_decision = st.selectbox(
                    "Agent Final Decision",
                    [
                        "Resolved at L1 (Followed Checklist)",
                        "Escalated to Tier 3 Eng (Gate Passed)",
                        "Escalated to Tier 3 Eng (Manager Override)",
                        "Referred to Operations Lead for Review"
                    ]
                )
            with col_d2:
                is_override = "Override" in actual_decision
                override_reason = st.text_input(
                    "Override Justification (Required if overriding model recommendation)",
                    value="" if not is_override else "Client VP escalated; requested priority engineering investigation."
                )

            submit_decision = st.form_submit_button("💾 Commit Decision to Operations Log", use_container_width=True)

            if submit_decision:
                if is_override and not override_reason.strip():
                    st.error("❌ Justification reason is required when overriding gate recommendations.")
                else:
                    rec_label = "Gate Activated: L1 Guidance Required" if is_gate_active else "Gate Passed: Engineering Escalation Approved"
                    prob_val = prob_avoidable if prob_avoidable is not None else 0.0

                    record_id = log_escalation_decision(
                        ticket_id=ticket_id_input,
                        agent_id=assigned_agent,
                        category=category,
                        priority=priority,
                        client_tier=client_tier,
                        predicted_probability=prob_val,
                        model_recommendation=rec_label,
                        actual_decision=actual_decision,
                        is_override=is_override,
                        override_reason=override_reason
                    )
                    st.success(
                        f"✅ Decision logged permanently to SQLite! (Record ID #{record_id} | Ticket: {ticket_id_input} | "
                        f"Agent: {assigned_agent} | Decision: {actual_decision})"
                    )


# ==============================================================================
# TAB 2: HISTORICAL ESCALATION QUALITY & REVIEW
# ==============================================================================
elif view_mode == "🔍 Historical Escalation Quality":
    st.title("🔍 Historical Escalation Review & Quality Analysis")
    st.markdown(
        "Trained on the **486 historically escalated tickets** to analyze "
        "historical escalation quality, uncover patterns of avoidable escalations, and support Meera's "
        "retrospective audits."
    )

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Historical Escalated Tickets", "486")
    col_m2.metric("True Avoidable Rate", "56.58%", help="275 of 486 escalations had non-code outcomes")
    col_m3.metric("Sep Holdout ROC-AUC", "0.546", help="Evaluated on 182 September escalations")

    st.subheader("Historical Model Reconciled Performance (Empirical Evaluation)")
    j2_path = TABLES_DIR / "j2_temporal_split_comparison.csv"
    if j2_path.exists():
        j2_df = pd.read_csv(j2_path)
        st.dataframe(
            j2_df.style.format({
                "ROC_AUC": "{:.4f}",
                "PR_AUC": "{:.4f}",
                "Precision": "{:.1%}",
                "Recall": "{:.1%}",
                "F1": "{:.3f}"
            }),
            use_container_width=True
        )

    st.subheader("Key Drivers of Avoidable Escalations (Logistic Regression Coefficients)")
    st.image(str(FIGURES_DIR / "j_model_calibration_and_features.png"))

    st.info(
        "💡 **Key Insights from Historical Escalation Analysis:**\n\n"
        "1. **Report Export Failing (+1.82 log-odds)**: Massive concentration of duplicate tickets caused by unlinked #ENG-402 defect.\n"
        "2. **Agent Behavioral Variation**: Rahul T (+0.94 log-odds) has an actual-to-expected escalation ratio of 1.79x, with 61.8% avoidable escalations.\n"
        "3. **First-Response Speed**: High rush-to-escalate within 1 hour often bypasses basic configuration verification."
    )


# ==============================================================================
# TAB 3: OPERATIONS & BACKLOG COCKPIT (MEERA & RITIKA VIEW)
# ==============================================================================
elif view_mode == "📊 Operations & Backlog Cockpit":
    st.title("📊 Operations, Backlog & Customer Experience Cockpit")
    st.markdown(
        "Executive operational dashboard resolving leadership's core mandate: "
        "*'Bring open tickets down this quarter without increasing headcount.'*"
    )

    # 1. High-Level Executive KPI Cards
    closed_df = df[df["is_open"] == 0]
    open_tickets = df[df["is_open"] == 1].copy()

    n_closed = len(closed_df)
    n_csat = closed_df["csat_score"].notna().sum()
    csat_resp_rate = (n_csat / n_closed * 100) if n_closed > 0 else 0.0
    avg_csat = closed_df["csat_score"].mean() if n_csat > 0 else 0.0
    n_reopened = (closed_df["reopen_count"] > 0).sum()
    reopen_rate = (n_reopened / n_closed * 100) if n_closed > 0 else 0.0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Tickets Processed", f"{len(df):,}")
    kpi2.metric("Open Backlog (Sep 30)", f"{len(open_tickets)} tickets", delta="+60% since July", delta_color="inverse")
    kpi3.metric("Historical Avoidable Rate", "56.58%", delta="Target: <25%", delta_color="inverse")
    kpi4.metric("Eng Handoff Load", "70.54%", delta="Target: <40%", delta_color="inverse")
    kpi5.metric("Repeat Contact Rate", "24.83%", delta="+9.9% in Sep", delta_color="inverse")

    st.divider()

    # 2. Section 2: Backlog Management Dashboard (Weekly Dynamics & Queue Distribution)
    st.subheader("📈 Backlog Management Dynamics: Inbound vs. Outbound")
    wb_df = compute_weekly_volume_and_backlog(df)

    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        st.markdown("**Weekly Tickets Created vs. Finally Closed & Net Backlog Change:**")
        chart_data = wb_df.set_index("week_start")[["created", "closed", "net_backlog"]]
        st.bar_chart(chart_data)

    with col_b2:
        st.markdown("**Open Backlog Queue Distribution:**")
        l1_queue = (open_tickets["status"] == "Open - with L1").sum()
        eng_queue = (open_tickets["status"] == "Open - with Engineering").sum()

        st.metric("Open in L1 Queue", f"{l1_queue} tickets", help="Tickets being diagnosed or awaiting client response")
        st.metric("Open in Engineering Queue", f"{eng_queue} tickets", help="Tickets escalated to Tier 3 engineering")

        queue_mix = pd.DataFrame({
            "Queue": ["Open - with L1", "Open - with Engineering"],
            "Count": [l1_queue, eng_queue]
        }).set_index("Queue")
        st.dataframe(queue_mix, use_container_width=True)

    st.divider()

    # 3. Section 3: Ticket Ageing and Prioritization
    st.subheader(f"⏱️ Ticket Ageing & Operational Prioritization ({len(open_tickets)} Open Tickets)")
    st.caption("Operational indicators to prioritize stagnant tickets. (Proposed indicators, not contractual SLAs).")

    open_tickets["age_band"] = open_tickets["open_age_hrs"].apply(assign_age_band)

    # Age band summary metrics
    ab1, ab2, ab3, ab4 = st.columns(4)
    ab1.metric("Under 24 hours", f"{(open_tickets['age_band'] == 'Under 24 hours').sum()} tickets")
    ab2.metric("24–48 hours", f"{(open_tickets['age_band'] == '24–48 hours').sum()} tickets")
    ab3.metric("48–72 hours", f"{(open_tickets['age_band'] == '48–72 hours').sum()} tickets")
    ab4.metric("More than 72 hours", f"{(open_tickets['age_band'] == 'More than 72 hours').sum()} tickets", delta="Critical", delta_color="inverse")

    # Multi-dimensional Filtering
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        prio_filter = st.multiselect("Priority Filter", options=["P1", "P2", "P3", "P4"], default=["P1", "P2", "P3", "P4"])
    with col_f2:
        cat_filter = st.multiselect("Category Filter", options=sorted(df["category"].unique()), default=sorted(df["category"].unique()))
    with col_f3:
        status_filter = st.multiselect("Queue Status", options=["Open - with L1", "Open - with Engineering"], default=["Open - with L1", "Open - with Engineering"])

    filtered_open = open_tickets[
        (open_tickets["priority"].isin(prio_filter)) &
        (open_tickets["category"].isin(cat_filter)) &
        (open_tickets["status"].isin(status_filter))
    ].sort_values(["priority", "open_age_hrs"], ascending=[True, False])

    st.dataframe(
        filtered_open[[
            "ticket_id", "priority", "category", "client_name", "client_tier",
            "assigned_agent", "status", "open_age_hrs", "age_band", "is_repeat_contact"
        ]],
        use_container_width=True
    )

    st.divider()

    # 4. Section 4: Customer Experience Monitoring
    st.subheader("⭐ Customer Experience (CX) & Quality Guardrails")
    st.markdown("Ensure that aggressive backlog reduction does not degrade resolution quality or satisfaction.")

    cx1, cx2, cx3, cx4 = st.columns(4)
    cx1.metric("Average CSAT", f"{avg_csat:.2f} / 5.0", delta="+0.2 Target")
    cx2.metric("CSAT Response Rate", f"{csat_resp_rate:.1f}%", help=f"{n_csat} responses out of {n_closed} closed tickets")
    cx3.metric("Ticket Reopen Rate", f"{reopen_rate:.1f}%", delta="Target: <8%", delta_color="inverse")
    esc_csat = closed_df[closed_df["is_escalated"] == 1]["csat_score"].mean()
    non_esc_csat = closed_df[closed_df["is_escalated"] == 0]["csat_score"].mean()
    cx4.metric("Escalated CSAT Penalty", f"{esc_csat:.2f} vs {non_esc_csat:.2f}", delta=f"{esc_csat - non_esc_csat:.2f}", delta_color="inverse")

    col_cx1, col_cx2 = st.columns(2)
    with col_cx1:
        st.markdown("**Resolution Speed vs. CSAT Rating (Hours to Final Close):**")
        csat_speed = closed_df.groupby("csat_score")["resolution_hrs"].agg(Median_Hours="median", P90_Hours=lambda s: np.percentile(s, 90)).round(1)
        st.dataframe(csat_speed, use_container_width=True)
        st.caption("Lower resolution times directly drive higher CSAT ratings (5★ median resolution is 10.8h vs 115.4h for 1★).")

    with col_cx2:
        st.markdown("**CSAT Score Distribution by Escalation Status:**")
        csat_dist = pd.crosstab(closed_df["csat_score"], closed_df["is_escalated"], normalize="columns") * 100
        csat_dist.columns = ["Non-Escalated (L1 Only)", "Escalated to Engineering"]
        st.bar_chart(csat_dist)

    st.divider()

    # 5. Persistent Override & Decision Monitoring (SQLite)
    st.subheader("🛡️ Persistent Override & Decision Monitoring (Live SQLite DB)")
    override_stats = compute_override_metrics()

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Total Decisions Logged", override_stats["total_decisions"])
    o2.metric("Manager Overrides", override_stats["total_overrides"])
    o3.metric("Override Rate", f"{override_stats['override_rate']*100:.1f}%", delta="Target: <20%", delta_color="inverse")
    o4.metric("Agent-Model Agreement", f"{override_stats['agreement_rate']*100:.1f}%", delta="Target: >80%")

    recent_decisions = get_logged_decisions(limit=15)
    if not recent_decisions.empty:
        st.markdown("**Recent Logged Triage Decisions, Overrides & Known Issue Links:**")
        display_cols = [
            col for col in [
                "id", "ticket_id", "agent_id", "category", "priority",
                "predicted_probability", "model_recommendation",
                "actual_decision", "is_override", "override_reason", "known_issue_id", "final_outcome", "created_at"
            ] if col in recent_decisions.columns
        ]
        st.dataframe(recent_decisions[display_cols], use_container_width=True)


# ==============================================================================
# TAB 4: AGENT QUALITY & THE KARAN CHECK
# ==============================================================================
elif view_mode == "🧑‍💻 Agent Quality & The Karan Check":
    st.title("🧑‍💻 Fair Agent Benchmarking & The Karan Check")
    st.markdown(
        "Resolves Meera's belief that *'some agents close in a few hours, so it can be done fast'*. "
        "Case-mix adjusted analysis exposes the critical trade-off between **speed** and **quality**."
    )

    scorecard_path = TABLES_DIR / "g1_agent_scorecard.csv"
    if scorecard_path.exists():
        scorecard_df = pd.read_csv(scorecard_path)
        st.dataframe(
            scorecard_df.style.format({
                "actual_esc_rate": "{:.2f}%",
                "expected_esc_rate": "{:.2f}%",
                "actual_vs_expected_ratio": "{:.2f}x",
                "avoidable_esc_rate": "{:.2f}%",
                "reopen_rate": "{:.2f}%",
                "non_esc_median_close_hrs": "{:.1f} hrs",
                "fcr_rate": "{:.2f}%",
                "mean_csat": "{:.2f}"
            }),
            use_container_width=True
        )

    st.subheader("Visualizing the Speed vs. Reopen Trade-Off (The Karan Check)")
    st.image(str(FIGURES_DIR / "fg_agent_benchmarking.png"))

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.warning(
            "⚠️ **The Karan B Diagnostic**: Karan appears to be the top performer on raw speed with a **9.62h median resolution** "
            "(fastest on the team). However, his **reopen rate is 29.49%** (highest on team, peer avg is 18%). He is rushing tickets "
            "to closure without resolving client root causes, creating secondary inbound volume."
        )
    with col_k2:
        st.error(
            "🚨 **The Rahul T Diagnostic**: Rahul has an actual escalation rate of **58.62%** against an expected rate of **32.66%** "
            "(**1.79x expected ratio**). 61.8% of his escalations are avoidable. Rahul requires coaching on internal troubleshooting."
        )


# ==============================================================================
# TAB 5: DATA REFRESH & CSV UPLOAD CENTER (SECTION 6)
# ==============================================================================
elif view_mode == "📁 Data Refresh & CSV Upload":
    st.title("📁 Operational Data Upload & Refresh Center")
    st.markdown(
        "Upload newly extracted support ticket datasets to refresh cockpit metrics, backlog inspection, "
        "and agent benchmarks without altering the historical baseline or retraining ML models."
    )

    uploaded_file = st.file_uploader("Upload New Support Tickets CSV File:", type=["csv"])

    if uploaded_file is not None:
        st.info("Validating uploaded CSV against schema dictionaries, data types, and timestamps...")
        is_valid, validation_errors, processed_df = validate_uploaded_tickets_csv(uploaded_file)

        if not is_valid:
            st.error("❌ **Validation Failed**: The uploaded file violates schema or integrity rules:")
            for err in validation_errors:
                st.write(f"• {err}")
        else:
            st.success(f"✅ **Validation Succeeded**: File is valid and clean! ({len(processed_df):,} records parsed)")

            c_u1, c_u2, c_u3 = st.columns(3)
            c_u1.metric("Uploaded Records", f"{len(processed_df):,}")
            c_u2.metric("Open Backlog", f"{(processed_df['is_open'] == 1).sum():,}")
            c_u3.metric("Escalated Tickets", f"{(processed_df['is_escalated'] == 1).sum():,}")

            st.dataframe(processed_df.head(10), use_container_width=True)

            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("🚀 Apply Uploaded Dataset to Cockpit", use_container_width=True):
                    st.session_state["active_df"] = processed_df
                    st.success("Cockpit successfully refreshed with uploaded dataset! Navigate to tabs above to view.")
            with col_act2:
                if st.button("🔄 Reset to Baseline Q3 Dataset", use_container_width=True):
                    st.session_state["active_df"] = load_ticket_data()
                    st.info("Cockpit reset to original Q3 baseline dataset.")
    else:
        st.markdown("---")
        st.subheader("Current Active Dataset Metadata")
        st.markdown(f"• **Dataset Rows:** `{len(df):,}`")
        st.markdown(f"• **Open Backlog Tickets:** `{(df['is_open'] == 1).sum()}`")
        st.markdown(f"• **Date Span:** `{df['created_at'].min().strftime('%Y-%m-%d')} to {df['created_at'].max().strftime('%Y-%m-%d')}`")
        if st.button("🔄 Reset to Historical Baseline", use_container_width=True):
            st.session_state["active_df"] = load_ticket_data()
            st.rerun()
