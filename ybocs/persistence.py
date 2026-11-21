"""Lightweight, file-backed session persistence so an in-progress assessment
survives a browser refresh or a dropped Streamlit Cloud websocket. The
browser URL carries an opaque session token; state is mirrored to a small
JSON file on disk keyed by that token and restored on reconnect."""

import json
import os
import time

SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".sessions")

PERSISTED_KEYS = [
    "stage", "lang", "client_name", "client_notes", "consented", "submitted",
    "checklist_answers", "severity_answers",
]


def _path(token):
    safe = "".join(c for c in token if c.isalnum() or c in "-_")
    return os.path.join(SESSIONS_DIR, f"{safe}.json")


def save_session(token, state):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    data = {k: state[k] for k in PERSISTED_KEYS if k in state}
    data["_saved_at"] = time.time()
    tmp = _path(token) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, _path(token))


def delete_session(token):
    path = _path(token)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def load_session(token):
    path = _path(token)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    if "checklist_answers" in data:
        data["checklist_answers"] = {int(k): v for k, v in data["checklist_answers"].items()}
    if "severity_answers" in data:
        data["severity_answers"] = {int(k): v for k, v in data["severity_answers"].items()}
    return data
