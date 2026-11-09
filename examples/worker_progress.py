"""Three local workers publish progress to one JSON document, without an API.

The computation is illustrative; this demonstrates cooperating writers, not a
durable job queue or exactly-once execution. Run after installing the package.
"""
import json
import multiprocessing as mp
from pathlib import Path
import tempfile

from agent_state_io import atomic_json, workspace_lock


def worker(directory, worker_id):
    root = Path(directory)
    for task_id in range(10):
        # Perform work outside the lock; only state updates are serialized.
        result = task_id * task_id
        with workspace_lock(root / "progress.lock", timeout=10):
            path = root / "progress.json"
            progress = json.loads(path.read_text(encoding="utf-8"))
            progress[str(worker_id)] = {"completed": task_id + 1, "last_result": result}
            atomic_json(path, progress)


def main():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "progress.json"
        atomic_json(path, {})
        ctx = mp.get_context("spawn")
        workers = [ctx.Process(target=worker, args=(directory, i)) for i in range(3)]
        try:
            for process in workers:
                process.start()
            for process in workers:
                process.join(20)
                if process.exitcode != 0:
                    raise RuntimeError("Worker failed or exceeded the time limit")
            progress = json.loads(path.read_text(encoding="utf-8"))
            if len(progress) != 3 or any(row["completed"] != 10 for row in progress.values()):
                raise RuntimeError("Missing progress updates")
            print(json.dumps(progress, indent=2))
        finally:
            for process in workers:
                if process.is_alive():
                    process.terminate()
                    process.join()


if __name__ == "__main__":
    main()
