from datetime import datetime

SUPPORTED_VERSIONS = {
    "1.0",
}

VALID_TRANSACTION_TYPES = {
    "spend",
    "payment",
    "recurring",
    "interest",
    "statement_close",
}

REQUIRED_CONFIG_FIELDS = {
    "apr",
    "projected_monthly_payment",
    "default_variable_spend",
    "safety_payment_buffer",
    "max_simulation_months",
    "statement_close_day",
    "payment_due_day",
    "recurring",
}


# ==================================================
# IMPORT VALIDATION
# ==================================================


def validate_import_data(data):
    """
    Validates imported debt-plan snapshot structure.
    """

    if not isinstance(data, dict):
        return False, "Imported file must contain a JSON object."

    required_keys = {
        "version",
        "transactions",
        "config",
    }

    missing_keys = required_keys - set(data.keys())

    if missing_keys:
        return (
            False,
            f"Missing required keys: {', '.join(sorted(missing_keys))}",
        )

    version = data.get("version")

    if not isinstance(version, str):
        return False, "Import version must be a string."

    if version not in SUPPORTED_VERSIONS:

        supported_versions_text = ", ".join(
            sorted(SUPPORTED_VERSIONS)
        )

        return (
            False,
            (
                f"Import version '{version}' is not supported. "
                f"Supported versions: {supported_versions_text}"
            ),
        )

    transactions = data.get("transactions")

    if not isinstance(transactions, list):
        return False, "Transactions must be a list."

    for index, transaction in enumerate(transactions):
        valid, error = validate_transaction(transaction)

        if not valid:
            return (
                False,
                f"Transaction #{index + 1}: {error}",
            )

    config = data.get("config")

    valid, error = validate_config(config)

    if not valid:
        return False, error

    return True, None


# ==================================================
# TRANSACTION VALIDATION
# ==================================================


def validate_transaction(transaction):
    """
    Validates transaction structure and values.
    """

    if not isinstance(transaction, dict):
        return False, "Transaction must be a dictionary."

    required_fields = {
        "type",
        "amount",
        "date",
    }

    missing_fields = required_fields - set(transaction.keys())

    if missing_fields:
        return (
            False,
            f"Missing transaction fields: {', '.join(sorted(missing_fields))}",
        )

    transaction_type = transaction.get("type")

    if transaction_type not in VALID_TRANSACTION_TYPES:
        return (
            False,
            "Transaction type must be spend, payment, recurring, interest, or statement_close.",
        )

    amount = transaction.get("amount")

    if not isinstance(amount, (int, float)):
        return False, "Transaction amount must be numeric."

    if transaction_type == "statement_close":
        if amount != 0:
            return False, "Statement close amount must be zero."
    elif amount <= 0:
        return False, "Transaction amount must be greater than zero."

    date_value = transaction.get("date")

    if not isinstance(date_value, str) or not date_value.strip():
        return False, "Transaction date must be a non-empty string."

    try:
        datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError:
        return False, "Transaction date must use YYYY-MM-DD format."

    return True, None


# ==================================================
# CONFIG VALIDATION
# ==================================================


def validate_config(config):
    """
    Validates forecasting/configuration structure.
    """

    if not isinstance(config, dict):
        return False, "Config must be a dictionary."

    missing_fields = REQUIRED_CONFIG_FIELDS - set(config.keys())

    if missing_fields:
        return (
            False,
            f"Missing config fields: {', '.join(sorted(missing_fields))}",
        )

    apr = config.get("apr")

    if not isinstance(apr, (int, float)):
        return False, "APR must be numeric."

    if apr < 0 or apr > 1:
        return False, "APR must be between 0 and 1."

    projected_monthly_payment = config.get(
        "projected_monthly_payment"
    )

    if not isinstance(projected_monthly_payment, (int, float)):
        return (
            False,
            "Projected monthly payment must be numeric.",
        )

    if projected_monthly_payment < 0:
        return (
            False,
            "Projected monthly payment must be greater than or equal to zero.",
        )

    default_variable_spend = config.get(
        "default_variable_spend"
    )

    if not isinstance(default_variable_spend, (int, float)):
        return (
            False,
            "Default variable spend must be numeric.",
        )

    if default_variable_spend < 0:
        return (
            False,
            "Default variable spend must be greater than or equal to zero.",
        )

    safety_payment_buffer = config.get(
        "safety_payment_buffer"
    )

    if not isinstance(safety_payment_buffer, (int, float)):
        return (
            False,
            "Safety payment buffer must be numeric.",
        )

    if safety_payment_buffer < 0:
        return (
            False,
            "Safety payment buffer must be greater than or equal to zero.",
        )

    max_simulation_months = config.get(
        "max_simulation_months"
    )

    if not isinstance(max_simulation_months, int):
        return (
            False,
            "Max simulation months must be an integer.",
        )

    if max_simulation_months <= 0:
        return (
            False,
            "Max simulation months must be greater than zero.",
        )

    statement_close_day = config.get(
        "statement_close_day"
    )

    if not isinstance(statement_close_day, int):
        return (
            False,
            "Statement close day must be an integer.",
        )

    if statement_close_day < 1 or statement_close_day > 31:
        return (
            False,
            "Statement close day must be between 1 and 31.",
        )

    payment_due_day = config.get(
        "payment_due_day"
    )

    if not isinstance(payment_due_day, int):
        return (
            False,
            "Payment due day must be an integer.",
        )

    if payment_due_day < 1 or payment_due_day > 31:
        return (
            False,
            "Payment due day must be between 1 and 31.",
        )

    recurring = config.get("recurring")

    if not isinstance(recurring, list):
        return False, "Recurring charges must be a list."

    for index, charge in enumerate(recurring):
        valid, error = validate_recurring_charge(charge)

        if not valid:
            return (
                False,
                f"Recurring charge #{index + 1}: {error}",
            )

    return True, None


# ==================================================
# RECURRING CHARGE VALIDATION
# ==================================================


def validate_recurring_charge(charge):
    """
    Validates recurring charge structure.
    """

    if not isinstance(charge, dict):
        return False, "Recurring charge must be a dictionary."

    required_fields = {
        "name",
        "amount",
    }

    missing_fields = required_fields - set(charge.keys())

    if missing_fields:
        return (
            False,
            f"Missing recurring charge fields: {', '.join(sorted(missing_fields))}",
        )

    name = charge.get("name")

    if not isinstance(name, str) or not name.strip():
        return False, "Recurring charge name must be a non-empty string."

    amount = charge.get("amount")

    if not isinstance(amount, (int, float)):
        return False, "Recurring charge amount must be numeric."

    if amount <= 0:
        return False, "Recurring charge amount must be greater than zero."

    return True, None
