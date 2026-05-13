import matplotlib.pyplot as plt

# ==================================================
# GRAPH SAFETY HELPERS
# ==================================================


def clamp_balances(values):
    """
    Prevent graph values from dropping below zero.
    """

    return [max(0, float(v)) for v in values]


# ==================================================
# BALANCE OVER TIME
# ==================================================


def create_balance_over_time_chart(
    baseline_balances,
    comparison_balances=None,
    baseline_label="Current Plan",
    comparison_label="Adjusted Plan",
):
    """
    Creates balance-over-time comparison chart.
    """

    baseline_balances = clamp_balances(baseline_balances)

    if comparison_balances is not None:
        comparison_balances = clamp_balances(comparison_balances)

    fig, ax = plt.subplots()

    baseline_months = list(range(1, len(baseline_balances) + 1))

    ax.plot(
        baseline_months,
        baseline_balances,
        marker="o",
        label=baseline_label,
    )

    ax.fill_between(
        baseline_months,
        baseline_balances,
        alpha=0.2,
    )

    if comparison_balances:
        comparison_months = list(range(1, len(comparison_balances) + 1))

        ax.plot(
            comparison_months,
            comparison_balances,
            linestyle="--",
            label=comparison_label,
        )

    ax.axhline(0, linestyle="--")

    ax.set_xlabel("Month")
    ax.set_ylabel("Balance ($)")
    ax.set_title("Balance Over Time")

    ax.legend()
    ax.grid(True)

    return fig


# ==================================================
# PAYOFF COMPARISON
# ==================================================


def create_payoff_comparison_chart(
    baseline_months,
    comparison_months,
    baseline_label="Current Plan",
    comparison_label="Adjusted Plan",
):
    """
    Creates payoff duration comparison bar chart.
    """

    fig, ax = plt.subplots()

    labels = [baseline_label, comparison_label]

    values = [
        max(0, baseline_months),
        max(0, comparison_months),
    ]

    ax.bar(labels, values)

    ax.set_ylabel("Months")
    ax.set_title("Payoff Duration Comparison")

    ax.grid(True, axis="y")

    return fig