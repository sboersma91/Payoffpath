import streamlit as st

from account import add


def render_starting_balance_gate(data) -> None:
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


def render_transaction_form() -> None:
    # Add Transactions
    st.header("Add Transaction")
    st.caption("Record spending or payments applied to the account.")

    with st.form("add_transaction_form"):
        col_a, col_b, col_c = st.columns([1, 1, 1])

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
