"""
meet_store.py — In-process shared file store for real-time meeting file sharing.

Uses a module-level dict so both doctor and patient Streamlit sessions
(running in the same Python process) share the same data instantly.
Files are keyed by room_name and stored as a list of dicts with base64 data.
"""
import time
import base64
from typing import Dict, List

# Module-level shared store — survives across Streamlit reruns within the process
_STORE: Dict[str, List[dict]] = {}

def add_file(room: str, name: str, mime: str, size: int, data_b64: str, sender: str) -> dict:
    """Add a file to the room's shared store. Returns the file record."""
    record = {
        "id": f"{int(time.time()*1000)}_{name}",
        "name": name,
        "mime": mime,
        "size": size,
        "data_b64": data_b64,
        "sender": sender,
        "ts": time.time(),
    }
    if room not in _STORE:
        _STORE[room] = []
    _STORE[room].append(record)
    return record

def get_files(room: str) -> List[dict]:
    """Return all files shared in a room, oldest first."""
    return list(_STORE.get(room, []))

def clear_room(room: str):
    """Clear all files for a room (call after session ends)."""
    _STORE.pop(room, None)

def file_count(room: str) -> int:
    return len(_STORE.get(room, []))
