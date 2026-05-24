from datetime import datetime
from copy import deepcopy
import json
from json import JSONDecodeError

import streamlit as st

from account import (
    get_engine_snapshot,
    add,
    DEFAULT_CONFIG,
)

from simulator import (
    run_simulation,
    compare_simulation,
    build_comparison_breakdown,
)

from graphing import (
    create_balance_over_time_chart,
    create_payoff_comparison_chart,
)
from ui.help_sections import (
    render_app_header,
    render_onboarding,
    render_forecast_guidance,
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

# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

if "config" not in st.session_state:
    # Deep copy prevents nested shared mutation
    st.session_state.config = deepcopy(DEFAULT_CONFIG)

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "show_onboarding" not in st.session_state:
    st.session_state.show_onboarding = True

# ==================================================
# DEVELOPER SEED INITIALIZATION
# ==================================================

if (
    DEVELOPER_SEED_MODE
    and not st.session_state.transactions
):

    seeded_config = deepcopy(DEFAULT_CONFIG)

    seeded_config["apr"] = 0.2499
    seeded_config["projected_monthly_payment"] = 1400
    seeded_config["default_variable_spend"] = 350
    seeded_config["safety_payment_buffer"] = 150
    seeded_config["max_simulation_months"] = 120
    seeded_config["compare_delta"] = 250
    seeded_config["recurring"] = [
        {"name": "Phone", "amount": 95},
        {"name": "Insurance", "amount": 180},
        {"name": "Gym", "amount": 45},
        {"name": "Streaming", "amount": 38},
    ]

    st.session_state.config = seeded_config

    st.session_state.transactions = [
        {
            "date": "2026-05-01",
            "type": "spend",
            "amount": 9800,
            "statement_balance": 0,
            "current_balance": 9800,
            "total_balance": 9800,
        },
        {
            "date": "2026-05-03",
            "type": "statement_close",
            "amount": 0,
            "statement_balance": 9800,
            "current_balance": 0,
            "total_balance": 9800,
        },
        {
            "date": "2026-05-07",
            "type": "spend",
            "amount": 850,
            "statement_balance": 9800,
            "current_balance": 850,
            "total_balance": 10650,
        },
        {
            "date": "2026-05-10",
            "type": "payment",
            "amount": 400,
            "statement_balance": 9400,
            "current_balance": 850,
            "total_balance": 10250,
        },
    ]

    st.session_state.recurring_edit = deepcopy(
        seeded_config["recurring"]
    )

    st.session_state.developer_seed_loaded = True
    st.session_state.developer_simulation_ran = False

if "recurring_edit" not in st.session_state:
    st.session_state.recurring_edit = deepcopy(
        st.session_state.config.get("recurring", [])
    )

data = st.session_state.transactions

# ==================================================
# SESSION EXPORT
# ==================================================

export_snapshot = {
    "version": "1.0",
    "exported_at": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
    "transactions": deepcopy(st.session_state.transactions),
    "config": deepcopy(st.session_state.config),
}

export_json = json.dumps(export_snapshot, indent=2)

render_onboarding()

with st.expander("Load Saved Plan"):
    uploaded_snapshot = st.file_uploader(
        "⬆️ Upload Saved Plan",
        type=["json"],
        help="Upload a previously exported debt-plan JSON file.",
    )

    if uploaded_snapshot is not None:

        try:
            imported_data = json.load(uploaded_snapshot)

            from validation import validate_import_data

            valid, error = validate_import_data(imported_data)

            if not valid:
                st.error(error)

            else:
                if st.button("Restore Imported Session"):

                    imported_config = deepcopy(imported_data.get("config", {}))

                    imported_transactions = deepcopy(
                        imported_data.get("transactions", [])
                    )

                    # Restore isolated session config
                    st.session_state.config = imported_config

                    # Restore isolated transaction history
                    st.session_state.transactions = imported_transactions

                    # Restore recurring editor state
                    st.session_state.recurring_edit = deepcopy(
                        imported_config.get("recurring", [])
                    )

                    st.success("Debt plan imported successfully.")

                    st.rerun()

        except JSONDecodeError:
            st.error(
                "The uploaded file is not valid JSON. Please upload a valid exported debt-plan file."
            )

        except UnicodeDecodeError:
            st.error(
                "The uploaded file could not be decoded. Please upload a UTF-8 encoded JSON file."
            )

        except Exception:
            st.error(
                "An unexpected error occurred while importing the debt plan."
            )

with st.expander("Forecast Assumptions"):
    st.subheader("Forecast Assumptions")
    st.caption("Update statement-based assumptions used across the forecast.")
    st.info(
        "Session settings are isolated to this browser session unless exported."
    )

    col_s1 = st.columns(1)[0]

    with col_s1:
        new_apr = st.number_input(
            "Annual percentage rate (APR %)",
            value=st.session_state.config["apr"] * 100,
        ) / 100
        st.caption("Use the purchase APR shown on your credit card statement.")

    # Save settings
    if st.button("Save Settings"):

        updated_config = deepcopy(st.session_state.config)

        updated_config["apr"] = new_apr

        # Replace session config atomically
        st.session_state.config = updated_config

        st.success("Session settings updated")
        st.rerun()

    st.divider()
    st.write("### Reset Tracker")
    st.warning("This clears all balance, spending, and payment history. Settings will stay saved.")

    confirm_reset = st.checkbox("I understand this will delete my tracking history")

    if st.button("Reset Tracker"):
        if not confirm_reset:
            st.warning("Check the confirmation box before resetting.")
        else:
            # Clear isolated session transaction state
            st.session_state.transactions = []

            # Reset transient editor state
            st.session_state.recurring_edit = deepcopy(
                st.session_state.config.get("recurring", [])
            )

            st.success("Tracker reset successfully.")

            # Clean rerun with preserved config defaults
            st.rerun()



# If no data, allow user to set starting balance
if not data:
    st.subheader("Set Starting Balance")

    start_balance = st.number_input("Starting Balance", min_value=0.0, step=100.0)

    if st.button("Initialize"):
        if start_balance <= 0:
            st.warning("Enter a valid starting balance")
        else:
            # Store as initial balance (treated as spend to create positive balance)
            add("spend", start_balance)

            st.success("Starting balance set")
            st.rerun()

    st.stop()

snapshot = get_engine_snapshot()

if data:
    latest_transaction = data[-1]

    snapshot = {
        "statement_balance": float(latest_transaction.get("statement_balance", 0)),
        "current_balance": float(latest_transaction.get("current_balance", 0)),
        "total_balance": float(latest_transaction.get("total_balance", 0)),
        "config": deepcopy(st.session_state.config),
    }

balance = snapshot["total_balance"]

# Initialize initial_balance for current cycle summary
initial_balance = 0

if data:
    initial_balance = round(
        float(data[0].get("total_balance", 0)),
        2,
    )

recurring_total = round(
    sum(r.get("amount", 0) for r in st.session_state.config.get("recurring", [])),
    2,
)

st.header("Current Account Status")

# Automatically use current month
current_month = datetime.today().strftime("%Y-%m")

st.write(f"Showing data for: {current_month}")
st.caption("Current-cycle transaction summary.")

cycle_data = [r for r in data if r["date"].startswith(current_month)]

if not cycle_data:
    st.info("No transactions yet this month.")

# Exclude initialization transaction from spend totals
initial_record = data[0] if data else None

spend_transactions = [
    r for r in cycle_data
    if r["type"] == "spend" and r != initial_record
]

payment_transactions = [
    r for r in cycle_data
    if r["type"] == "payment"
]

interest_transactions = [
    r for r in cycle_data
    if r["type"] == "interest"
]

total_spend = round(
    sum(float(r["amount"]) for r in spend_transactions),
    2,
)

total_pay = round(
    sum(float(r["amount"]) for r in payment_transactions),
    2,
)

total_interest_paid = round(
    sum(float(r["amount"]) for r in interest_transactions),
    2,
)

# Split into two rows to prevent truncation
col1, col2, col3 = st.columns(3)
col1.metric("Balance", f"${round(balance,2):,}")
col2.metric("Spent", f"${round(total_spend,2):,}")
col3.metric("Paid", f"${round(total_pay,2):,}")

col4, col5 = st.columns(2)
col4.metric("Net", f"${round(total_pay - total_spend,2):,}")
col5.metric("Fixed Monthly", f"${round(recurring_total,2):,}")

# Add Transactions
st.header("Add Transaction")
st.caption("Record spending or payments applied to the account.")

with st.form("add_transaction_form"):
    col_a, col_b, col_c = st.columns([1,1,1])

    with col_a:
        txn_type = st.selectbox("Type", ["spend", "payment"]) 

    with col_b:
        amount = st.number_input("Amount", min_value=0.0, step=1.0, value=0.0)

    with col_c:
        submit = st.form_submit_button("Add")

    if submit:
        if amount <= 0:
            st.warning("Enter an amount greater than 0")
        else:
            add(txn_type, float(amount))

            st.success(f"Added {txn_type} of ${amount}")
            st.rerun()

# ==================================================
# FORECAST GUIDANCE
# ==================================================

render_forecast_guidance()

# Inputs
st.header("Forecast Simulation")
st.caption("Estimate payoff timing based on projected payments and spending.")

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

compare_delta = st.number_input(
    "Payment change for comparison (+/-)",
    value=st.session_state.config.get("compare_delta", 0.0),
)
st.caption("Try a higher or lower payment amount to compare payoff timelines.")

minimum_viable_payment = round(
    recurring_total +
    (balance * (st.session_state.config["apr"] / 12)) +
    st.session_state.config["safety_payment_buffer"],
    2,
)

monthly_interest_estimate = round(balance * (st.session_state.config["apr"] / 12), 2)

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

run_simulation_clicked = st.button("Run Simulation")

with st.expander("Recurring Monthly Charges"):
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

    baseline_result = run_simulation(
        balance=balance,
        payment=payment,
        recurring_total=recurring_total,
        variable_spend=variable_spend,
        apr=st.session_state.config["apr"],
        max_months=st.session_state.config["max_simulation_months"],
    )

    if not baseline_result["success"]:
        st.error("Payment too low to overcome spending + interest.")
        st.stop()

    comparison_result = compare_simulation(
        balance=balance,
        payment=payment,
        compare_delta=compare_delta,
        recurring_total=recurring_total,
        variable_spend=variable_spend,
        apr=st.session_state.config["apr"],
        max_months=st.session_state.config["max_simulation_months"],
    )

    current_cycle_summary = {
        "starting_balance": initial_balance,
        "spending": total_spend,
        "payment": total_pay,
        "interest": total_interest_paid,
        "net_reduction": round(total_pay - total_spend, 2),
        "ending_balance": round(balance, 2),
        "adjusted_ending_balance": round(balance, 2),
        "difference": 0,
    }

    comparison_breakdown = build_comparison_breakdown(
        baseline_result,
        comparison_result,
        current_cycle_summary=current_cycle_summary,
    )

    st.header("Simulation Results")

    months = baseline_result["months"]
    total_interest = baseline_result["total_interest"]

    average_monthly_interest = round(
        total_interest / months,
        2,
    ) if months else 0

    estimated_payoff_date = datetime.today().replace(day=1)

    if months:
        estimated_payoff_year = estimated_payoff_date.year + ((estimated_payoff_date.month - 1 + months) // 12)
        estimated_payoff_month = ((estimated_payoff_date.month - 1 + months) % 12) + 1

        estimated_payoff_date = estimated_payoff_date.replace(
            year=estimated_payoff_year,
            month=estimated_payoff_month,
        )

    if baseline_result["ending_balance"] > 0:
        st.error("Payoff exceeds configured simulation window.")
    else:
        st.success(f"Estimated payoff timeline: {months} months")

        st.info(
            f"Estimated payoff date: {estimated_payoff_date.strftime('%B %Y')}"
        )

    if comparison_result["success"]:
        compare_months = comparison_result["months"]

        st.info(f"Adjusted plan payoff: {compare_months} months")

        diff = compare_months - months

        if diff > 0:
            st.error(f"+{diff} months longer")
        elif diff < 0:
            st.success(f"{-diff} months faster")
        else:
            st.write("No change in payoff time")
    else:
        st.warning("Adjusted plan will not pay off the balance.")

    st.subheader("Forecast Summary")

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

    st.subheader("Balance Over Time")

    baseline_balances = baseline_result["balances"]
    comparison_balances = comparison_result["balances"]

    balance_chart = create_balance_over_time_chart(
        baseline_balances=baseline_balances,
        comparison_balances=comparison_balances,
    )

    payoff_chart = create_payoff_comparison_chart(
        baseline_months=months,
        comparison_months=comparison_result["months"] or st.session_state.config["max_simulation_months"],
    )


    st.pyplot(balance_chart)

    st.subheader("Payoff Duration Comparison")
    st.pyplot(payoff_chart)

with st.expander("Save Your Plan"):
    st.caption(
        "Sessions are private to your browser and temporary unless exported. "
        "Download your current plan to save progress."
    )
    st.download_button(
        label="⬇️ Download Current Plan",
        data=export_json,
        file_name=f"credit_tracker_session_{datetime.today().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        help="Download a complete debt-plan snapshot including transactions and forecasting configuration.",
    )
