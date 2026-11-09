import json
import multiprocessing as mp
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from agent_state_io import atomic_json, atomic_text, workspace_lock


def increment(directory):
    root = Path(directory)
    for _ in range(20):
        with workspace_lock(root / "counter.lock", timeout=10):
            path = root / "counter.json"
            count = json.loads(path.read_text())
            atomic_json(path, count + 1)


def attempt_lock(path, result):
    try:
        with workspace_lock(path, timeout=0.1):
            result.put("acquired")
    except TimeoutError:
        result.put("timeout")


def hold_until_terminated(path, ready):
    with workspace_lock(path):
        ready.set()
        import time
        time.sleep(60)


class IOTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_unicode_and_nested_directories(self):
        path = self.root / "nested" / "state.json"
        atomic_json(path, {"text": "hello 🌍"})
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"text": "hello 🌍"})

    def test_text_exact_newlines(self):
        path = self.root / "state.txt"
        atomic_text(path, "a\nb\r\nc")
        self.assertEqual(path.read_bytes(), b"a\nb\r\nc")

    def test_invalid_json_preserves_previous_file(self):
        path = self.root / "state.json"
        atomic_json(path, {"valid": True})
        for invalid in (float("nan"), float("inf"), object()):
            with self.assertRaises((ValueError, TypeError)):
                atomic_json(path, invalid)
            self.assertEqual(json.loads(path.read_text()), {"valid": True})
            self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_failed_replace_cleans_temporary_file(self):
        path = self.root / "state.txt"
        atomic_text(path, "old")
        with patch("agent_state_io.os.replace", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                atomic_text(path, "new")
        self.assertEqual(path.read_text(), "old")
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_nested_lock_and_exception_release(self):
        path = self.root / "state.lock"
        with self.assertRaises(RuntimeError):
            with workspace_lock(path):
                with workspace_lock(path):
                    raise RuntimeError("test")
        with workspace_lock(path, timeout=0):
            pass

    def test_other_process_times_out_then_acquires(self):
        ctx = mp.get_context("spawn")
        result = ctx.Queue()
        path = self.root / "state.lock"
        with workspace_lock(path):
            worker = ctx.Process(target=attempt_lock, args=(path, result))
            worker.start()
            worker.join(10)
            if worker.is_alive():
                worker.terminate()
                worker.join()
                self.fail("worker hung")
            self.assertEqual(worker.exitcode, 0)
            self.assertEqual(result.get(timeout=2), "timeout")
        worker = ctx.Process(target=attempt_lock, args=(path, result))
        worker.start()
        worker.join(10)
        if worker.is_alive():
            worker.terminate()
            worker.join()
            self.fail("worker hung")
        self.assertEqual(worker.exitcode, 0)
        self.assertEqual(result.get(timeout=2), "acquired")
        result.close()

    def test_multiprocess_counter_has_no_lost_updates(self):
        atomic_json(self.root / "counter.json", 0)
        ctx = mp.get_context("spawn")
        workers = [ctx.Process(target=increment, args=(self.directory.name,)) for _ in range(3)]
        try:
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(15)
                self.assertEqual(worker.exitcode, 0)
            self.assertEqual(json.loads((self.root / "counter.json").read_text()), 60)
        finally:
            for worker in workers:
                if worker.is_alive():
                    worker.terminate()
                    worker.join()

    def test_process_death_releases_os_lock(self):
        ctx = mp.get_context("spawn")
        ready = ctx.Event()
        path = self.root / "crash.lock"
        worker = ctx.Process(target=hold_until_terminated, args=(path, ready))
        worker.start()
        try:
            self.assertTrue(ready.wait(10), "worker did not acquire lock")
            worker.terminate()
            worker.join(10)
            self.assertFalse(worker.is_alive())
            with workspace_lock(path, timeout=1):
                atomic_json(self.root / "recovered.json", {"recovered": True})
            self.assertTrue(json.loads((self.root / "recovered.json").read_text())["recovered"])
        finally:
            if worker.is_alive():
                worker.terminate()
                worker.join()


if __name__ == "__main__":
    unittest.main()
