"""Run after installing the package; uses only disposable temporary state."""
import json
import tempfile
from pathlib import Path
from agent_state_io import atomic_json, workspace_lock

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "counter.json"
    with workspace_lock(Path(directory) / "counter.lock"):
        atomic_json(path, {"completed": 1})
    print(json.loads(path.read_text(encoding="utf-8")))
