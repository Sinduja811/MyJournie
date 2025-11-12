import json
from datetime import datetime
from pathlib import Path

DATA_PATH = Path("data/users/demo_user.json")

def load_entries():
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r") as f:
        return json.load(f)
    
def save_entry(entry):
    entries = load_entries()   
    entry["timestamp"] = datetime.now().isoformat()
    entries.append(entry)

    with open(DATA_PATH, "w") as f:
        json.dump(entries, f, indent=2)

    return entry

def get_history():
    """Return the full journal/history"""

    return load_entries()

