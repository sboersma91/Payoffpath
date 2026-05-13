"""
Pure financial state transition engine.

This module contains the shared balance mechanics used by both live tracking
and forecasting. It intentionally does not import Streamlit, read files, or
mutate session state.
"""


VALID_USER_TRANSACTION_TYPES = {"spend", "payment"}


def normalize_state(state=None):
    """Return a clean balance state dictionary."""

    state = state or {}

    statement_balance = round(float(state.get("statement_balance", 0) or 0), 2)
    current_balance = round(float(state.get("current_balance", 0) or 0), 2)

    statement_balance = max(0, statement_balance)
    current_balance = max(0, current_balance)

    return {
        "statement_balance": statement_balance,
        "current_balance": current_balance,
        "total_balance": round(statement_balance + current_balance, 2),
    }



def state_from_transactions(transactions):
    """Build current state from the latest transaction row."""

    if not transactions:
        return normalize_state()

    latest = transactions[-1]

    return normalize_state(
        {
            "statement_balance": latest.get("statement_balance", 0),
            "current_balance": latest.get("current_balance", 0),
        }
    )



def apply_spend_to_state(state, amount):
    """Apply a purchase to current-cycle balance only."""

    if amount <= 0:
        raise ValueError("Spend amount must be greater than zero.")

    state = normalize_state(state)
    state["current_balance"] += float(amount)

    return normalize_state(state)



def apply_payment_to_state(state, amount):
    """
    Apply payment to statement balance first.
    Any excess payment reduces current-cycle balance.
    """

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    state = normalize_state(state)
    remaining_payment = float(amount)

    statement_balance = state["statement_balance"]
    current_balance = state["current_balance"]

    if statement_balance > 0:
        applied_to_statement = min(statement_balance, remaining_payment)
        statement_balance -= applied_to_statement
        remaining_payment -= applied_to_statement

    if remaining_payment > 0:
        current_balance = max(0, current_balance - remaining_payment)

    return normalize_state(
        {
            "statement_balance": statement_balance,
            "current_balance": current_balance,
        }
    )



def close_statement_cycle_state(state):
    """Move current-cycle balance into statement balance."""

    state = normalize_state(state)

    new_statement_balance = state["statement_balance"] + state["current_balance"]

    return normalize_state(
        {
            "statement_balance": new_statement_balance,
            "current_balance": 0,
        }
    )



def apply_recurring_to_state(state, recurring_total):
    """
    Add recurring charges to current-cycle balance.
    These do not immediately accrue interest.
    """

    state = normalize_state(state)
    recurring_total = float(recurring_total or 0)

    if recurring_total < 0:
        raise ValueError("Recurring total cannot be negative.")

    state["current_balance"] += recurring_total

    return normalize_state(state)



def apply_interest_to_state(state, apr):
    """Apply monthly interest to statement balance only."""

    state = normalize_state(state)

    if apr < 0 or apr > 1:
        raise ValueError("APR must be between 0 and 1.")

    statement_balance = state["statement_balance"]

    if statement_balance <= 0:
        return normalize_state(state), 0

    interest = statement_balance * (float(apr) / 12)
    statement_balance += interest

    new_state = normalize_state(
        {
            "statement_balance": statement_balance,
            "current_balance": state["current_balance"],
        }
    )

    return new_state, round(interest, 2)



def apply_transaction_to_state(state, txn_type, amount):
    """Route a user transaction through the shared engine."""

    if txn_type == "spend":
        return apply_spend_to_state(state, amount)

    if txn_type == "payment":
        return apply_payment_to_state(state, amount)

    raise ValueError("Invalid transaction type")



def simulate_monthly_cycle(state, payment, recurring_total, variable_spend, apr):
    """
    Run one simplified monthly forecast cycle using the same balance mechanics.

    Order:
    1. close current cycle into statement balance
    2. add recurring charges to new current cycle
    3. add variable spend to new current cycle
    4. apply payment to statement first, then current
    5. apply interest to unpaid statement balance
    """

    if payment < 0:
        raise ValueError("Payment cannot be negative.")

    if variable_spend < 0:
        raise ValueError("Variable spend cannot be negative.")

    start_state = normalize_state(state)

    working_state = close_statement_cycle_state(start_state)
    working_state = apply_recurring_to_state(working_state, recurring_total)

    if variable_spend > 0:
        working_state = apply_spend_to_state(working_state, variable_spend)

    if payment > 0:
        working_state = apply_payment_to_state(working_state, payment)

    working_state, interest = apply_interest_to_state(working_state, apr)

    spending = round(float(recurring_total or 0) + float(variable_spend or 0), 2)

    return {
        "start_state": start_state,
        "ending_state": working_state,
        "spending": spending,
        "interest": interest,
        "payment": round(float(payment), 2),
    }


# ==================================================
# STATEFUL FORECASTING ENGINE
# ==================================================


def run_stateful_simulation(
    starting_state,
    payment,
    recurring_total,
    variable_spend,
    apr,
    max_months,
):
    """
    Canonical month-by-month forecasting engine.

    Uses the shared balance mechanics from simulate_monthly_cycle()
    so forecasting and live tracking share identical financial behavior.

    Returns structure compatible with existing simulator output.
    """

    if apr is None:
        raise ValueError("APR is required for simulation.")

    if max_months is None:
        raise ValueError("max_months is required for simulation.")

    state = normalize_state(starting_state)

    months = 0

    balances = []
    breakdown = []

    total_interest = 0
    total_spending = 0

    while state["total_balance"] > 0 and months < max_months:

        months += 1

        cycle_result = simulate_monthly_cycle(
            state=state,
            payment=payment,
            recurring_total=recurring_total,
            variable_spend=variable_spend,
            apr=apr,
        )

        start_state = normalize_state(
            cycle_result["start_state"]
        )

        ending_state = normalize_state(
            cycle_result["ending_state"]
        )

        spending = round(float(cycle_result["spending"]), 2)
        interest = round(float(cycle_result["interest"]), 2)
        payment_amount = round(float(cycle_result["payment"]), 2)

        ending_balance = max(
            0,
            round(float(ending_state["total_balance"]), 2),
        )

        start_balance = round(
            float(start_state["total_balance"]),
            2,
        )

        net_reduction = round(
            start_balance - ending_balance,
            2,
        )

        if start_balance > 0:
            balance_change_percent = round(
                (net_reduction / start_balance) * 100,
                2,
            )
        else:
            balance_change_percent = 0

        balances.append(ending_balance)

        total_interest += interest
        total_spending += spending

        breakdown.append(
            {
                "month": months,
                "start_balance": start_balance,
                "spending": spending,
                "interest": interest,
                "payment": payment_amount,
                "ending_balance": ending_balance,
                "net_reduction": net_reduction,
                "balance_change_percent": balance_change_percent,
            }
        )

        # Detect impossible payoff
        if payment_amount <= (spending + interest) and ending_balance > 0:
            return {
                "success": False,
                "months": None,
                "breakdown": breakdown,
                "balances": balances,
                "total_interest": round(total_interest, 2),
                "total_spending": round(total_spending, 2),
                "ending_balance": ending_balance,
            }

        state = normalize_state(ending_state)

        if state["total_balance"] <= 0:
            break

    return {
        "success": state["total_balance"] <= 0,
        "months": months,
        "breakdown": breakdown,
        "balances": balances,
        "total_interest": round(total_interest, 2),
        "total_spending": round(total_spending, 2),
        "ending_balance": max(
            0,
            round(float(state["total_balance"]), 2),
        ),
    }
