from datetime import datetime
from copy import deepcopy
import json
from json import JSONDecodeError

from validation import validate_import_data


def build_export_snapshot(transactions, config):
    return {
        "version": "1.0",
        "exported_at": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        "transactions": deepcopy(transactions),
        "config": deepcopy(config),
    }


def serialize_export_payload(export_snapshot) -> str:
    return json.dumps(export_snapshot, indent=2)


def build_export_filename() -> str:
    return f"credit_tracker_session_{datetime.today().strftime('%Y%m%d_%H%M%S')}.json"


def load_import_payload(uploaded_snapshot):
    try:
        imported_data = json.load(uploaded_snapshot)
        valid, error = validate_import_data(imported_data)

        if not valid:
            return {
                "success": False,
                "error": error,
            }

        return {
            "success": True,
            "imported_data": imported_data,
        }

    except JSONDecodeError:
        return {
            "success": False,
            "error": "The uploaded file is not valid JSON. Please upload a valid exported debt-plan file.",
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "The uploaded file could not be decoded. Please upload a UTF-8 encoded JSON file.",
        }

    except Exception:
        return {
            "success": False,
            "error": "An unexpected error occurred while importing the debt plan.",
        }


def restore_imported_session(imported_data, session_state) -> None:
    imported_config = deepcopy(imported_data.get("config", {}))

    imported_transactions = deepcopy(
        imported_data.get("transactions", [])
    )

    # Restore isolated session config
    session_state.config = imported_config

    # Restore isolated transaction history
    session_state.transactions = imported_transactions

    # Restore recurring editor state
    session_state.recurring_edit = deepcopy(
        imported_config.get("recurring", [])
    )
