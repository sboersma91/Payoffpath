from datetime import datetime

from simulator import (
    run_simulation,
    compare_simulation,
    build_comparison_breakdown,
)


def prepare_simulation_inputs(
    balance,
    payment,
    recurring_total,
    variable_spend,
    apr,
    max_months,
    compare_delta,
):
    baseline_inputs = {
        "balance": balance,
        "payment": payment,
        "recurring_total": recurring_total,
        "variable_spend": variable_spend,
        "apr": apr,
        "max_months": max_months,
    }

    comparison_inputs = {
        "balance": balance,
        "payment": payment,
        "compare_delta": compare_delta,
        "recurring_total": recurring_total,
        "variable_spend": variable_spend,
        "apr": apr,
        "max_months": max_months,
    }

    return {
        "baseline_inputs": baseline_inputs,
        "comparison_inputs": comparison_inputs,
    }


def build_cycle_summary(initial_balance, total_spend, total_pay, total_interest_paid, balance):
    return {
        "starting_balance": initial_balance,
        "spending": total_spend,
        "payment": total_pay,
        "interest": total_interest_paid,
        "net_reduction": round(total_pay - total_spend, 2),
        "ending_balance": round(balance, 2),
        "adjusted_ending_balance": round(balance, 2),
        "difference": 0,
    }


def derive_payoff_summary(months, total_interest, ending_balance):
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

    return {
        "average_monthly_interest": average_monthly_interest,
        "estimated_payoff_date": estimated_payoff_date,
        "payoff_exceeds_window": ending_balance > 0,
    }


def derive_comparison_summary(baseline_months, comparison_result):
    if comparison_result["success"]:
        compare_months = comparison_result["months"]
        diff = compare_months - baseline_months
        return {
            "success": True,
            "compare_months": compare_months,
            "diff": diff,
        }

    return {
        "success": False,
    }


def run_forecast_pipeline(
    baseline_inputs,
    comparison_inputs,
    current_cycle_summary,
):
    baseline_result = run_simulation(**baseline_inputs)

    if not baseline_result["success"]:
        return {
            "success": False,
            "baseline_result": baseline_result,
        }

    comparison_result = compare_simulation(**comparison_inputs)

    comparison_breakdown = build_comparison_breakdown(
        baseline_result,
        comparison_result,
        current_cycle_summary=current_cycle_summary,
    )

    return {
        "success": True,
        "baseline_result": baseline_result,
        "comparison_result": comparison_result,
        "comparison_breakdown": comparison_breakdown,
    }
