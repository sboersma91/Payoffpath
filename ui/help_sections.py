import streamlit as st


def render_app_header(developer_seed_mode: bool) -> None:
    st.title("Credit Card Payoff Simulator")
    st.caption("Session-based payoff forecasting and balance tracking.")

    if developer_seed_mode:
        st.warning("Developer Seed Mode Active")


def render_onboarding() -> None:
    if st.session_state.show_onboarding:
        st.info(
            "This app helps estimate how long one credit card may take to pay off while accounting for payments, ongoing spending, recurring charges, and interest."
        )
        st.markdown("### Quick Steps")
        st.markdown(
            """
- Set your starting balance (first time only).
- Add recent spending and payment activity.
- Enter your projected monthly payment and variable spend.
- Run the simulation and compare payoff timelines.
- Save your plan so you can reload it later.
        """
        )
        st.markdown("### Example Statement Mapping")
        st.caption(
            "Map statement numbers directly: current balance → Starting Balance, planned monthly payment → Projected Monthly Payment, expected new purchases → Variable Monthly Spend, and APR (%) from your statement terms."
        )
        st.markdown("### Forecast Disclaimer")
        st.caption(
            "This forecast is an estimate, not financial advice. Results depend on the accuracy of the values you enter and can change with future spending and payments."
        )
        if st.button("Got it — hide this guide"):
            st.session_state.show_onboarding = False
            st.rerun()


def render_forecast_guidance() -> None:
    with st.expander("How To Use This Forecast"):

        st.caption(
            "Use real statement estimates to forecast how long payoff may take."
        )

        st.markdown("### Quick Steps")

        st.markdown(
            """
- Enter your current balance
- Enter a realistic monthly payment
- Estimate monthly spending
- Run the simulation
- Adjust values to compare payoff timelines
        """
        )

        st.divider()

        st.markdown("### Example Statement Mapping")

        st.info(
            "Previous Balance: $12,500\n\n"
            "Payments: -$1,200\n\n"
            "Purchases: +$650\n\n"
            "Interest: +$210\n\n"
            "Current Balance: $12,160"
        )

        st.caption(
            "Recurring charges are fixed monthly bills. Variable spending is flexible day-to-day spending. Close estimates are completely okay."
        )

        st.divider()

        st.markdown("### Forecast Disclaimer")

        st.markdown(
            """
- This is a payoff forecast tool
- Future spending and payments affect accuracy
- Results improve when updated regularly
        """
        )
