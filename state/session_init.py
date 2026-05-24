from copy import deepcopy

import streamlit as st


def initialize_session_state(default_config: dict) -> None:
    if "config" not in st.session_state:
        # Deep copy prevents nested shared mutation
        st.session_state.config = deepcopy(default_config)

    if "transactions" not in st.session_state:
        st.session_state.transactions = []

    if "show_onboarding" not in st.session_state:
        st.session_state.show_onboarding = True


def initialize_developer_seed(
    developer_seed_mode: bool,
    default_config: dict,
) -> None:
    if (
        developer_seed_mode
        and not st.session_state.transactions
    ):
        load_example_scenario(default_config)

        st.session_state.developer_seed_loaded = True
        st.session_state.developer_simulation_ran = False


def load_example_scenario(default_config: dict) -> None:
    seeded_config = deepcopy(default_config)

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


def initialize_recurring_editor() -> None:
    if "recurring_edit" not in st.session_state:
        st.session_state.recurring_edit = deepcopy(
            st.session_state.config.get("recurring", [])
        )
