# Payoffpath

# Credit Card Payoff Simulator

A simple Streamlit app that helps users estimate how long it may take to pay off a credit card while still accounting for ongoing spending, recurring charges, payments, and interest.

## What It Does

- Tracks a single credit card balance
- Separates statement balance from current-cycle balance
- Estimates payoff timeline based on:
  - current balance
  - APR
  - projected monthly payment
  - recurring monthly charges
  - variable monthly spending
- Compares payoff timing with an adjusted payment amount
- Allows users to export and import a session plan as JSON

## Who This Is For

This tool is for people carrying credit card debt who want a clearer forecast of how spending and payments affect their payoff timeline.

## What This Is Not

This is not financial advice, banking software, or an exact credit card statement replica. It is a planning and forecasting tool based on user-provided assumptions.

## Run Locally

```bash`
pip install -r requirements.txt
streamlit run app.py

## Project Structure

app.py          # Streamlit user interface
engine.py       # Core financial state transition logic
simulator.py    # Forecast orchestration wrapper
account.py      # Session-based account state helpers
graphing.py     # Chart generation
validation.py   # Import/session validation
config.json     # Default app configuration

## Disclaimer

This app provides estimates only. Actual credit card payoff timelines may vary based on card issuer rules, payment timing, fees, APR changes, spending behavior, statement cycles, and user-entered assumptions.
