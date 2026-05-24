from datetime import datetime


def build_snapshot_from_latest_transaction(data, config):
    snapshot = {
        "statement_balance": float(data[-1].get("statement_balance", 0)),
        "current_balance": float(data[-1].get("current_balance", 0)),
        "total_balance": float(data[-1].get("total_balance", 0)),
        "config": config,
    }
    return snapshot


def calculate_initial_balance(data) -> float:
    if data:
        return round(
            float(data[0].get("total_balance", 0)),
            2,
        )
    return 0


def calculate_recurring_total(recurring_rows) -> float:
    return round(
        sum(r.get("amount", 0) for r in recurring_rows),
        2,
    )


def calculate_cycle_metrics(data, current_month: str):
    cycle_data = [r for r in data if r["date"].startswith(current_month)]

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

    return {
        "cycle_data": cycle_data,
        "total_spend": total_spend,
        "total_pay": total_pay,
        "total_interest_paid": total_interest_paid,
    }


def get_current_month() -> str:
    return datetime.today().strftime("%Y-%m")


def calculate_forecast_readiness(balance, recurring_total, apr, safety_payment_buffer):
    minimum_viable_payment = round(
        recurring_total +
        (balance * (apr / 12)) +
        safety_payment_buffer,
        2,
    )

    monthly_interest_estimate = round(balance * (apr / 12), 2)

    return {
        "minimum_viable_payment": minimum_viable_payment,
        "monthly_interest_estimate": monthly_interest_estimate,
    }
