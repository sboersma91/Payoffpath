# ==================================================
# CANONICAL FORECASTING ENGINE
# ==================================================
#
# engine.py is the single source of truth for all
# financial state transitions and balance mechanics.
#
# simulator.py must NOT implement independent balance
# math or forecasting behavior.
#
# All payoff forecasting must route through engine.py
# to ensure live tracking and simulation always share
# identical financial logic.
#
# This prevents forecasting drift between:
# - live balance tracking
# - payoff simulations
# - comparison forecasting
#
# simulator.py intentionally acts as a thin orchestration
# wrapper around the canonical engine layer.
# ==================================================

from engine import run_stateful_simulation


def run_simulation(
    balance,
    payment,
    recurring_total,
    variable_spend,
    apr,
    max_months,
):
    """
    Thin orchestration wrapper around engine.py.

    IMPORTANT:
    This function must not contain independent balance
    calculations or forecasting logic.

    All payoff forecasting routes through:
        engine.run_stateful_simulation()

    This guarantees forecasting behavior always matches
    the live financial engine used by tracker.py.

    Returns:
    {
        success,
        months,
        breakdown,
        balances,
        total_interest,
        total_spending,
        ending_balance,
    }
    """

    if apr is None:
        raise ValueError("APR is required for simulation.")

    if max_months is None:
        raise ValueError("max_months is required for simulation.")

    starting_state = {
        "statement_balance": float(balance),
        "current_balance": 0,
    }

    return run_stateful_simulation(
        starting_state=starting_state,
        payment=payment,
        recurring_total=recurring_total,
        variable_spend=variable_spend,
        apr=apr,
        max_months=max_months,
    )



def compare_simulation(
    balance,
    payment,
    compare_delta,
    recurring_total,
    variable_spend,
    apr,
    max_months,
):
    """
    Runs adjusted payment comparison simulation.
    """

    adjusted_payment = payment + compare_delta

    return run_simulation(
        balance=balance,
        payment=adjusted_payment,
        recurring_total=recurring_total,
        variable_spend=variable_spend,
        apr=apr,
        max_months=max_months,
    )





def build_comparison_breakdown(
    baseline_result,
    comparison_result,
    current_cycle_summary=None,
):
    """
    Builds UI-friendly month-by-month comparison table.

    Safely aligns payoff rows even when simulations
    complete at different months.
    """

    baseline_breakdown = baseline_result.get(
        "breakdown",
        [],
    )

    comparison_breakdown = comparison_result.get(
        "breakdown",
        [],
    )

    max_rows = max(
        len(baseline_breakdown),
        len(comparison_breakdown),
    )

    comparison_rows = []

    # ==================================================
    # MONTH 0 (CURRENT REAL ACCOUNT STATE)
    # ==================================================

    current_cycle_summary = current_cycle_summary or {}

    starting_balance = round(
        float(current_cycle_summary.get("starting_balance", 0)),
        2,
    )

    spending = round(
        float(current_cycle_summary.get("spending", 0)),
        2,
    )

    payment = round(
        float(current_cycle_summary.get("payment", 0)),
        2,
    )

    interest = round(
        float(current_cycle_summary.get("interest", 0)),
        2,
    )

    net_reduction = round(
        float(current_cycle_summary.get("net_reduction", 0)),
        2,
    )

    ending_balance = round(
        float(current_cycle_summary.get("ending_balance", starting_balance)),
        2,
    )

    adjusted_ending_balance = round(
        float(
            current_cycle_summary.get(
                "adjusted_ending_balance",
                ending_balance,
            )
        ),
        2,
    )

    difference = round(
        float(current_cycle_summary.get("difference", 0)),
        2,
    )

    comparison_rows.append(
        {
            "month": 0,
            "starting_balance": starting_balance,
            "spending": spending,
            "interest": interest,
            "payment": payment,
            "net_reduction": net_reduction,
            "ending_balance": ending_balance,
            "adjusted_ending_balance": adjusted_ending_balance,
            "difference": difference,
        }
    )

    for index in range(max_rows):

        baseline_row = (
            baseline_breakdown[index]
            if index < len(baseline_breakdown)
            else None
        )

        comparison_row = (
            comparison_breakdown[index]
            if index < len(comparison_breakdown)
            else None
        )

        starting_balance = (
            round(
                float(baseline_row["start_balance"]),
                2,
            )
            if baseline_row
            else None
        )

        ending_balance = (
            round(
                float(baseline_row["ending_balance"]),
                2,
            )
            if baseline_row
            else None
        )

        adjusted_ending_balance = (
            round(
                float(comparison_row["ending_balance"]),
                2,
            )
            if comparison_row
            else None
        )

        if (
            ending_balance is not None
            and adjusted_ending_balance is not None
        ):
            difference = round(
                ending_balance - adjusted_ending_balance,
                2,
            )
        else:
            difference = None

        spending = (
            round(
                float(baseline_row["spending"]),
                2,
            )
            if baseline_row
            else None
        )

        interest = (
            round(
                float(baseline_row["interest"]),
                2,
            )
            if baseline_row
            else None
        )

        payment = (
            round(
                float(baseline_row["payment"]),
                2,
            )
            if baseline_row
            else None
        )

        net_reduction = (
            round(
                float(baseline_row["net_reduction"]),
                2,
            )
            if baseline_row
            else None
        )

        comparison_rows.append(
            {
                "month": index + 1,
                "starting_balance": starting_balance,
                "spending": spending,
                "interest": interest,
                "payment": payment,
                "net_reduction": net_reduction,
                "ending_balance": ending_balance,
                "adjusted_ending_balance": adjusted_ending_balance,
                "difference": difference,
            }
        )

    return comparison_rows