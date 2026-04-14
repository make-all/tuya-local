"""
Functions for logging
"""

import json


def non_json(data):
    """Handler for json_dumps when used for debugging."""
    return f"Non-JSON: ({data})"


def log_json(data):
    """Function for logging data as json."""
    return json.dumps(data, default=non_json)
