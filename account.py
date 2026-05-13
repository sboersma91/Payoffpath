from datetime import datetime
from typing import Dict, List
import json
import streamlit as st
from copy import deepcopy

from engine import (
    apply_transaction_to_state,
    close_statement_cycle_state,
    apply_interest_to_state,
    apply_recurring_to_state,
    normalize_state,
)

CONFIG_FILE = "config.json"

# ==================================================
# CONFIG MANAGEMENT
# ==================================================

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        default = {
            "apr": 0.2099,
            "projected_monthly_payment": 2000,
            "default_variable_spend": 0,
            "safety_payment_buffer": 100,
            "max_simulation_months": 120,
            "statement_close_day": 2,
            "payment_due_day": 28,
            "recurring": [
                {"name": "GPT", "amount": 21.40},
                {"name": "Visible", "amount": 25},
                {"name": "Skool", "amount": 9},
                {"name": "Google", "amount": 79.20},
                {"name": "Wilderness", "amount": 25},
            ]
        }
        save_config(default)
        return default


def save_config(config):
    """
    Persists configuration defaults.

    Session-level overrides remain isolated in Streamlit session state.
    """

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)



DEFAULT_CONFIG = load_config()

# ==================================================
# DEVELOPER SEED DATA
# ==================================================
#
# Reusable local development/testing seed state.
#
# IMPORTANT:
# These constants are intentionally passive.
#
# account.py does NOT activate developer mode.
# app.py may optionally import/use these values
# for local debugging workflows.
# ==================================================

DEFAULT_DEVELOPER_CONFIG = {
    "apr": 0.2499,
    "projected_monthly_payment": 1650,
    "default_variable_spend": 400,
    "safety_payment_buffer": 150,
    "max_simulation_months": 120,
    "statement_close_day": 2,
    "payment_due_day": 28,
    "compare_delta": 250,
    "recurring": [
        {"name": "Phone", "amount": 95},
        {"name": "Insurance", "amount": 210},
        {"name": "Gym", "amount": 49},
        {"name": "Streaming", "amount": 42},
        {"name": "Fuel", "amount": 180},
    ],
}

DEFAULT_DEVELOPER_TRANSACTIONS = [
    {
        "date": "2026-05-01",
        "type": "spend",
        "amount": 12850,
        "statement_balance": 0,
        "current_balance": 12850,
        "total_balance": 12850,
    },
    {
        "date": "2026-05-03",
        "type": "statement_close",
        "amount": 0,
        "statement_balance": 12850,
        "current_balance": 0,
        "total_balance": 12850,
    },
    {
        "date": "2026-05-07",
        "type": "recurring",
        "amount": 576,
        "statement_balance": 12850,
        "current_balance": 576,
        "total_balance": 13426,
    },
    {
        "date": "2026-05-10",
        "type": "payment",
        "amount": 1200,
        "statement_balance": 11650,
        "current_balance": 576,
        "total_balance": 12226,
    },
    {
        "date": "2026-05-14",
        "type": "spend",
        "amount": 420,
        "statement_balance": 11650,
        "current_balance": 996,
        "total_balance": 12646,
    },
]

# ==================================================
# SESSION CONFIG STATE
# ==================================================


def initialize_session_config():
    """
    Initializes isolated per-user config state.
    """

    if "config" not in st.session_state:
        st.session_state.config = deepcopy(DEFAULT_CONFIG)



def get_config():
    """
    Returns isolated per-session config.
    """

    initialize_session_config()

    return st.session_state.config

# ==================================================
# SESSION TRANSACTION STORAGE
# ==================================================


def initialize_session_storage():
    """
    Initializes isolated per-user transaction storage.
    """

    if "transactions" not in st.session_state:
        st.session_state.transactions = []



def read_data():
    """
    Reads transaction data from Streamlit session state.
    """

    initialize_session_storage()

    return st.session_state.transactions



def write_row(row):
    """
    Writes transaction data into isolated session state.
    """

    initialize_session_storage()

    st.session_state.transactions.append(row)

# ==================================================
# BALANCE HELPERS
# ==================================================

def get_total_balance(data: List[Dict]) -> float:
    if not data:
        return 0

    last = data[-1]
    return float(last.get("total_balance", 0) or 0)

def get_statement_balance(data):
    if not data:
        return 0

    last = data[-1]
    return float(last.get("statement_balance", 0) or 0)


def get_current_balance(data):
    if not data:
        return 0

    last = data[-1]
    return float(last.get("current_balance", 0) or 0)

# ==================================================
# DATE HELPERS
# ==================================================

def today():
    return datetime.today()

def get_statement_close_day():
    return get_config()["statement_close_day"]



def get_payment_due_day():
    return get_config()["payment_due_day"]


def get_recurring_charges():
    return get_config().get("recurring", [])


def get_total_recurring_amount():
    recurring = get_recurring_charges()
    return round(sum(item.get("amount", 0) for item in recurring), 2)

# ==================================================
# RECURRING CHARGE ENGINE
# ==================================================


def apply_recurring_charges():
    """
    Applies recurring charges into the NEW current cycle.

    These charges:
    - do NOT immediately accrue interest
    - enter current_balance only
    - naturally roll into the next statement balance
    """

    recurring_total = get_total_recurring_amount()

    if recurring_total <= 0:
        return {
            "recurring_applied": 0,
            "current_balance": 0,
        }

    data = read_data()

    current_state = normalize_state(
        {
            "statement_balance": get_statement_balance(data),
            "current_balance": get_current_balance(data),
        }
    )

    updated_state = apply_recurring_to_state(
        current_state,
        recurring_total,
    )

    write_row({
        "date": today().strftime("%Y-%m-%d"),
        "type": "recurring",
        "amount": round(recurring_total, 2),
        "statement_balance": round(updated_state["statement_balance"], 2),
        "current_balance": round(updated_state["current_balance"], 2),
        "total_balance": round(updated_state["total_balance"], 2)
    })

    return {
        "recurring_applied": round(recurring_total, 2),
        "statement_balance": round(updated_state["statement_balance"], 2),
        "current_balance": round(updated_state["current_balance"], 2),
        "total_balance": round(updated_state["total_balance"], 2),
    }

# ==================================================
# TRANSACTION ENGINE
# ==================================================

def add(txn_type, amount):
    data = read_data()

    if amount <= 0:
        raise ValueError("Amount must be positive")

    current_state = normalize_state(
        {
            "statement_balance": get_statement_balance(data),
            "current_balance": get_current_balance(data),
        }
    )

    updated_state = apply_transaction_to_state(
        current_state,
        txn_type,
        amount,
    )

    write_row({
        "date": today().strftime("%Y-%m-%d"),
        "type": txn_type,
        "amount": amount,
        "statement_balance": round(updated_state["statement_balance"], 2),
        "current_balance": round(updated_state["current_balance"], 2),
        "total_balance": round(updated_state["total_balance"], 2)
    })

    return {
        "transaction_type": txn_type,
        "amount": amount,
        "statement_balance": round(updated_state["statement_balance"], 2),
        "current_balance": round(updated_state["current_balance"], 2),
        "total_balance": round(updated_state["total_balance"], 2),
    }

# ==================================================
# CYCLE MANAGEMENT
# ==================================================

def close_statement_cycle():
    data = read_data()

    current_state = normalize_state(
        {
            "statement_balance": get_statement_balance(data),
            "current_balance": get_current_balance(data),
        }
    )

    updated_state = close_statement_cycle_state(current_state)

    write_row({
        "date": today().strftime("%Y-%m-%d"),
        "type": "statement_close",
        "amount": 0,
        "statement_balance": round(updated_state["statement_balance"], 2),
        "current_balance": round(updated_state["current_balance"], 2),
        "total_balance": round(updated_state["total_balance"], 2)
    })

    recurring_result = apply_recurring_charges()

    return {
        "statement_balance": round(updated_state["statement_balance"], 2),
        "current_balance": recurring_result["current_balance"],
        "total_balance": recurring_result["total_balance"],
        "recurring_applied": recurring_result["recurring_applied"],
    }

# ==================================================
# INTEREST ENGINE
# ==================================================

def apply_interest():
    data = read_data()

    current_state = normalize_state(
        {
            "statement_balance": get_statement_balance(data),
            "current_balance": get_current_balance(data),
        }
    )

    if current_state["statement_balance"] <= 0:
        return {
            "interest_applied": 0,
            "statement_balance": round(current_state["statement_balance"], 2),
            "current_balance": round(current_state["current_balance"], 2),
            "total_balance": round(current_state["total_balance"], 2),
        }

    config = get_config()

    updated_state, monthly_interest = apply_interest_to_state(
        current_state,
        config["apr"],
    )

    write_row({
        "date": today().strftime("%Y-%m-%d"),
        "type": "interest",
        "amount": round(monthly_interest, 2),
        "statement_balance": round(updated_state["statement_balance"], 2),
        "current_balance": round(updated_state["current_balance"], 2),
        "total_balance": round(updated_state["total_balance"], 2)
    })

    return {
        "interest_applied": round(monthly_interest, 2),
        "statement_balance": round(updated_state["statement_balance"], 2),
        "current_balance": round(updated_state["current_balance"], 2),
        "total_balance": round(updated_state["total_balance"], 2),
    }

# ==================================================
# PUBLIC ENGINE STATE HELPERS
# ==================================================


def get_engine_snapshot():
    data = read_data()

    return {
        "statement_balance": get_statement_balance(data),
        "current_balance": get_current_balance(data),
        "total_balance": get_total_balance(data),
        "config": deepcopy(get_config()),
    }
