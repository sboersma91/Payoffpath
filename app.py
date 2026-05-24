from datetime import datetime
from copy import deepcopy

import streamlit as st

from account import (
    get_engine_snapshot,
    DEFAULT_CONFIG,
)

from graphing import (
    create_balance_over_time_chart,
    create_payoff_comparison_chart,
)
from logic.metrics import (
    build_snapshot_from_latest_transaction,
    calculate_initial_balance,
    calculate_recurring_total,
    calculate_cycle_metrics,
    get_current_month,
    calculate_forecast_readiness,
)
from ui.help_sections import (
    render_app_header,
    render_onboarding,
    render_forecast_guidance,
)
from ui.transactions import (
    render_starting_balance_gate,
    render_transaction_form,
)
from state.session_init import (
    initialize_session_state,
    initialize_developer_seed,
    initialize_recurring_editor,
    load_example_scenario,
)
from persistence.session_io import (
    build_export_snapshot,
    serialize_export_payload,
    load_import_payload,
    restore_imported_session,
    build_export_filename,
)
from orchestration.simulation_flow import (
    prepare_simulation_inputs,
    run_forecast_pipeline,
    build_cycle_summary,
    derive_payoff_summary,
    derive_comparison_summary,
)


st.set_page_config(page_title="Credit Card Payoff Simulator", layout="wide")

DEVELOPER_SEED_MODE = False

# ==================================================
# DEVELOPER SEED MODE
# ==================================================
#
# Enables automatic local debug/test state.
#
# When enabled:
# - preloads transactions
# - preloads config
# - auto-runs simulation
# - skips repetitive manual setup
#
# IMPORTANT:
# Seed data only initializes when session state is empty.
# Existing user session work is preserved across reruns.
# ==================================================


render_app_header(DEVELOPER_SEED_MODE)

st.markdown("## Plan Your Credit Card Payoff Path")
st.caption(
    "Estimate how spending, payments, and interest may affect your monthly payoff timeline."
)
st.caption(
    "Forecasts are estimates only and not financial advice."
)

st.info(
    "**Start here:** Enter your current balance, add expected monthly payment and card spending, run the forecast, then review your estimated payoff path."
)

# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

initialize_session_state(DEFAULT_CONFIG)

# ==================================================
# DEVELOPER SEED INITIALIZATION
# ==================================================

initialize_developer_seed(
    DEVELOPER_SEED_MODE,
    DEFAULT_CONFIG,
)

initialize_recurring_editor()

data = st.session_state.transactions

# ==================================================
# SESSION EXPORT
# ==================================================

export_snapshot = build_export_snapshot(
    st.session_state.transactions,
    st.session_state.config,
)

export_json = serialize_export_payload(export_snapshot)

load_col, example_col = st.columns([2, 1])

with load_col:
    st.markdown("### Continue a saved forecast")
    uploaded_snapshot = st.file_uploader(
        "Upload a saved forecast",
        type=["json"],
        help="Upload a saved forecast file to continue where you left off.",
    )

    if uploaded_snapshot is not None:
        import_result = load_import_payload(uploaded_snapshot)

        if not import_result["success"]:
            st.error(import_result["error"])
        else:
            if st.button("Restore Previous Forecast"):
                restore_imported_session(
                    import_result["imported_data"],
                    st.session_state,
                )
                st.success("Saved forecast restored successfully.")
                st.rerun()

with example_col:
    st.markdown("### New here?")
    if st.button("Load Example Scenario", use_container_width=True):
        load_example_scenario(DEFAULT_CONFIG)
        st.success("Example scenario loaded.")
        st.rerun()

render_onboarding()

render_starting_balance_gate(data)

snapshot = get_engine_snapshot()

if data:
    snapshot = build_snapshot_from_latest_transaction(
        data,
        deepcopy(st.session_state.config),
    )

balance = snapshot["total_balance"]

# Initialize initial_balance for current cycle summary
initial_balance = calculate_initial_balance(data)

recurring_total = calculate_recurring_total(
    st.session_state.config.get("recurring", []),
)

st.header("Current Account Status")

# Automatically use current month
current_month = get_current_month()

st.write(f"Showing data for: {current_month}")
st.caption("Current-cycle transaction summary.")

cycle_metrics = calculate_cycle_metrics(data, current_month)
cycle_data = cycle_metrics["cycle_data"]

if not cycle_data:
    st.info("No transactions yet this month.")

total_spend = cycle_metrics["total_spend"]
total_pay = cycle_metrics["total_pay"]
total_interest_paid = cycle_metrics["total_interest_paid"]

# Split into two rows to prevent truncation
col1, col2, col3 = st.columns(3)
col1.metric("Balance", f"${round(balance,2):,}")
col2.metric("Spent", f"${round(total_spend,2):,}")
col3.metric("Paid", f"${round(total_pay,2):,}")

col4, col5 = st.columns(2)
col4.metric("Net", f"${round(total_pay - total_spend,2):,}")
col5.metric("Fixed Monthly", f"${round(recurring_total,2):,}")

render_transaction_form()
st.divider()
st.header("Forecast Setup")
st.caption("Enter your current card situation to prepare a payoff forecast.")

apr = st.number_input(
    "Annual percentage rate (APR %)",
    value=st.session_state.config["apr"] * 100,
) / 100
st.caption("Use the purchase APR shown on your latest statement.")

payment = st.number_input(
    "Planned monthly payment",
    value=st.session_state.config["projected_monthly_payment"],
)
st.caption("Enter what you realistically plan to pay each month.")

variable_spend = st.number_input(
    "Expected extra monthly spending",
    value=st.session_state.config["default_variable_spend"],
)
st.caption("Estimate monthly purchases beyond your fixed recurring charges.")

readiness_metrics = calculate_forecast_readiness(
    balance=balance,
    recurring_total=recurring_total,
    apr=apr,
    safety_payment_buffer=st.session_state.config["safety_payment_buffer"],
)
minimum_viable_payment = readiness_metrics["minimum_viable_payment"]
monthly_interest_estimate = readiness_metrics["monthly_interest_estimate"]

st.subheader("Forecast Readiness")

col_f1, col_f2 = st.columns(2)

with col_f1:
    st.metric(
        "Estimated Monthly Interest",
        f"${monthly_interest_estimate:,.2f}"
    )

with col_f2:
    st.metric(
        "Minimum Viable Payment",
        f"${minimum_viable_payment:,.2f}"
    )

if payment < minimum_viable_payment:
    st.warning(
        "Projected payment may be too low to safely reduce the balance."
    )
else:
    st.success(
        "Projected payment appears strong enough to reduce the balance."
    )

with st.expander("Advanced Forecast Settings", expanded=False):
    st.caption("Optional controls for deeper planning and comparison.")

    compare_delta = st.number_input(
        "Payment change for comparison (+/-)",
        value=st.session_state.config.get("compare_delta", 0.0),
    )
    st.caption("Try a higher or lower payment amount to compare payoff timelines.")

    st.caption(
        "Add or update fixed monthly charges like subscriptions, insurance, and utility bills."
    )
    st.metric("Total Recurring Monthly Charges", f"${recurring_total:,.2f}")

    rows = st.session_state.recurring_edit

    col_h1, col_h2, col_h3 = st.columns([2, 1, 0.5])
    col_h1.markdown("**Charge**")
    col_h2.markdown("**Amount**")
    col_h3.markdown("**Action**")

    for i, r in enumerate(rows):
        col_r1, col_r2, col_r3 = st.columns([2, 1, 0.5])

        name = col_r1.text_input(
            f"name_{i}",
            value=r.get("name", ""),
            label_visibility="collapsed",
        )
        amount = col_r2.number_input(
            f"amount_{i}",
            value=float(r.get("amount", 0.0)),
            label_visibility="collapsed",
        )

        if col_r3.button("❌", key=f"del_{i}"):
            rows.pop(i)
            st.session_state.recurring_edit = rows
            st.rerun()

        r["name"] = name
        r["amount"] = amount

    col_a1, col_a2 = st.columns([1, 3])
    if col_a1.button("+ Add Recurring"):
        rows.append({"name": "", "amount": 0.0})
        st.session_state.recurring_edit = rows
        st.rerun()

    if st.button("Save Recurring Charges"):
        updated_config = deepcopy(st.session_state.config)
        updated_config["recurring"] = deepcopy(
            st.session_state.recurring_edit
        )

        st.session_state.config = updated_config
        st.session_state.recurring_edit = deepcopy(
            updated_config["recurring"]
        )

        st.success("Recurring charges updated")
        st.rerun()

    st.divider()
    st.write("### Reset Tracker")
    st.warning("This clears all balance, spending, and payment history. Settings will stay saved.")

    confirm_reset = st.checkbox("I understand this will delete my tracking history")

    if st.button("Reset Tracker"):
        if not confirm_reset:
            st.warning("Check the confirmation box before resetting.")
        else:
            st.session_state.transactions = []
            st.session_state.recurring_edit = deepcopy(
                st.session_state.config.get("recurring", [])
            )
            st.success("Tracker reset successfully.")
            st.rerun()

# ==================================================
# FORECAST GUIDANCE
# ==================================================

render_forecast_guidance()

run_simulation_clicked = st.button(
    "Run Forecast",
    type="primary",
    use_container_width=True,
)

updated_config = deepcopy(st.session_state.config)
updated_config["apr"] = apr
updated_config["projected_monthly_payment"] = payment
updated_config["default_variable_spend"] = variable_spend
updated_config["compare_delta"] = compare_delta
st.session_state.config = updated_config

# ==================================================
# DEVELOPER AUTO-SIMULATION
# ==================================================
#
# Automatically runs the simulation once after
# developer seed data initializes.
#
# Prevents repetitive manual clicking during
# local development/testing.
#
# Protected against infinite rerun loops via
# developer_simulation_ran session flag.
# ==================================================

if (
    DEVELOPER_SEED_MODE
    and st.session_state.get("developer_seed_loaded", False)
    and not st.session_state.get("developer_simulation_ran", False)
):
    run_simulation_clicked = True
    st.session_state.developer_simulation_ran = True

if run_simulation_clicked:
    simulation_inputs = prepare_simulation_inputs(
        balance=balance,
        payment=payment,
        recurring_total=recurring_total,
        variable_spend=variable_spend,
        apr=st.session_state.config["apr"],
        max_months=st.session_state.config["max_simulation_months"],
        compare_delta=compare_delta,
    )

    current_cycle_summary = build_cycle_summary(
        initial_balance=initial_balance,
        total_spend=total_spend,
        total_pay=total_pay,
        total_interest_paid=total_interest_paid,
        balance=balance,
    )

    forecast_result = run_forecast_pipeline(
        baseline_inputs=simulation_inputs["baseline_inputs"],
        comparison_inputs=simulation_inputs["comparison_inputs"],
        current_cycle_summary=current_cycle_summary,
    )

    if not forecast_result["success"]:
        st.error("Payment too low to overcome spending + interest.")
        st.stop()

    baseline_result = forecast_result["baseline_result"]
    comparison_result = forecast_result["comparison_result"]
    comparison_breakdown = forecast_result["comparison_breakdown"]

    st.divider()
    st.header("Forecast Results")

    months = baseline_result["months"]
    total_interest = baseline_result["total_interest"]

    payoff_summary = derive_payoff_summary(
        months=months,
        total_interest=total_interest,
        ending_balance=baseline_result["ending_balance"],
    )

    average_monthly_interest = payoff_summary["average_monthly_interest"]
    estimated_payoff_date = payoff_summary["estimated_payoff_date"]

    comparison_summary = derive_comparison_summary(months, comparison_result)
    diff = comparison_summary.get("diff", 0)

    st.subheader("Forecast Interpretation")

    if payoff_summary["payoff_exceeds_window"]:
        st.warning(
            "At the current settings, the balance is not projected to fully pay off within the selected forecast window."
        )
    else:
        st.info(
            f"At your current payment and spending levels, this balance is projected to be paid off in about {months} months (around {estimated_payoff_date.strftime('%B %Y')})."
        )

    interpretation_points = []

    if payment <= monthly_interest_estimate:
        interpretation_points.append(
            "Your planned payment is close to the monthly interest level, so payoff progress may feel very slow month to month."
        )
    elif payment < (monthly_interest_estimate * 2):
        interpretation_points.append(
            "Your planned payment is above interest, so the balance is moving in the right direction, but gradually."
        )
    else:
        interpretation_points.append(
            "Your planned payment is meaningfully above estimated monthly interest, which supports steadier payoff progress."
        )

    if total_interest > balance:
        interpretation_points.append(
            "Projected total interest is high relative to the current balance, so small payment or spending changes can have a noticeable long-term impact."
        )
    else:
        interpretation_points.append(
            "Projected interest stays below the current balance, which suggests the plan is reasonably efficient if spending assumptions hold."
        )

    if comparison_summary["success"]:
        if diff < 0:
            interpretation_points.append(
                f"The comparison scenario improves payoff timing by {-diff} months."
            )
        elif diff > 0:
            interpretation_points.append(
                f"The comparison scenario extends payoff timing by {diff} months."
            )
        else:
            interpretation_points.append(
                "The comparison scenario produces about the same payoff timeline."
            )

    st.markdown("#### What this means")
    for point in interpretation_points[:3]:
        st.markdown(f"- {point}")

    st.divider()
    st.subheader("Balance Over Time")

    baseline_balances = baseline_result["balances"]
    comparison_balances = comparison_result["balances"]

    balance_chart = create_balance_over_time_chart(
        baseline_balances=baseline_balances,
        comparison_balances=comparison_balances,
    )

    st.pyplot(balance_chart)

    st.divider()
    st.subheader("Key Forecast Metrics")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    summary_col1.metric(
        "Starting Balance",
        f"${round(balance,2):,}"
    )

    summary_col2.metric(
        "Recurring Monthly",
        f"${round(recurring_total,2):,}"
    )

    summary_col3.metric(
        "Projected Interest",
        f"${round(total_interest,2):,}"
    )

    st.metric(
        "Average Monthly Interest",
        f"${average_monthly_interest:,.2f}"
    )

    st.subheader("Comparison Insight")
    if payoff_summary["payoff_exceeds_window"]:
        st.error("Payoff exceeds configured simulation window.")
    else:
        st.success(f"Estimated payoff timeline: {months} months")
        st.caption(
            f"Estimated payoff date: {estimated_payoff_date.strftime('%B %Y')}"
        )

    if comparison_summary["success"]:
        compare_months = comparison_summary["compare_months"]
        st.caption(f"Adjusted scenario payoff: {compare_months} months")

        if diff > 0:
            st.warning(f"Adjusted scenario is {diff} months longer.")
        elif diff < 0:
            st.success(f"Adjusted scenario is {-diff} months faster.")
        else:
            st.info("Adjusted scenario has about the same payoff timeline.")
    else:
        st.warning("Adjusted plan will not pay off the balance.")

    payoff_chart = create_payoff_comparison_chart(
        baseline_months=months,
        comparison_months=comparison_result["months"] or st.session_state.config["max_simulation_months"],
    )

    st.subheader("Payoff Duration Comparison")
    st.pyplot(payoff_chart)

    st.divider()
    st.subheader("Monthly Breakdown")

    st.caption(
        "Month 0 represents your real current balance activity before projected future months begin."
    )

    st.dataframe(
        comparison_breakdown,
        width="stretch",
        column_config={
            "month": "Month",
            "starting_balance": "Starting Balance",
            "spending": "Spending",
            "interest": "Interest",
            "payment": "Payment",
            "net_reduction": "Net Reduction",
            "ending_balance": "Ending Balance",
            "adjusted_ending_balance": "Adjusted Ending Balance",
            "difference": "Difference",
        },
    )

    st.divider()
    st.subheader("Save This Forecast")
    st.caption("Save this forecast to continue or compare scenarios later.")
    st.download_button(
        label="⬇️ Save Forecast File",
        data=export_json,
        file_name=build_export_filename(),
        mime="application/json",
        help="Save a copy of your forecast so you can restore it later.",
    )
