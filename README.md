# Agent State IO

A small, standard-library-only Python utility for publishing local text/JSON state and coordinating cooperating writers with a reentrant file lock. Extracted from an existing local research application's state-publication utility; this is its first standalone public release.

## Install

Clone this repository, then run `python -m pip install .` from its directory. This package is not currently published on PyPI.

## Use

```python
import json
from pathlib import Path
from agent_state_io import atomic_json, atomic_text, workspace_lock

path = Path("state/progress.json")
with workspace_lock("state/progress.lock", timeout=5):
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"completed": 0}
    state["completed"] += 1
    atomic_json(path, state)

atomic_text("state/status.txt", "Ready\n")
```

`atomic_text(path, text)` and `atomic_json(path, value)` write a temporary file in the destination directory, flush and fsync it, then replace the destination. A serialization or replacement failure leaves the previous destination intact and cleans up the temporary file. JSON rejects NaN and infinity.

`workspace_lock(path, timeout=30)` serializes cooperating threads/processes using the same lock path. Same-thread nested acquisition is supported. It uses Windows byte-range locks or POSIX flock. Lock files intentionally remain on disk; do not delete or replace them during use. The OS releases a process's lock when it exits.

## Boundaries

- Intended for trusted paths on local filesystems. Network filesystems and hostile shared directories are not supported guarantees.
- A single file replacement is atomic where the underlying filesystem supports it; multiple files are not a transaction.
- Writers must use the same separate lock file for read-modify-write operations. Atomic writes alone do not prevent lost updates.
- File contents are fsynced, but the parent directory is not: this is not a power-loss durability guarantee.
- Replacement creates a new file; existing permissions/ownership metadata are not preserved deliberately.
- Timeout applies separately to the thread-lock wait and subsequent OS-lock wait; total elapsed time can exceed the supplied timeout. Use finite nonnegative values.
- Lock objects are retained per distinct resolved path for the process lifetime. Use a bounded set of lock paths in long-running services. Do not fork while locks are held.
- This package does not encrypt state, validate application schemas, contact an AI provider, or execute trades.

## Development

```sh
python -m unittest discover -s tests -v
python examples/counter.py
```

Tests use synthetic temporary data only. Windows verification is recorded in RELEASE_NOTES.md; POSIX behavior needs independent validation. Contributions should include a minimal reproduction and focused regression tests. Do not put credentials, personal data, or production state in issues or fixtures.

## License

MIT. See LICENSE.
