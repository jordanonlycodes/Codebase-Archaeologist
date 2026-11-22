"""The same retrieval/intelligence utilities run in Node and the real workspace."""
import subprocess
from pathlib import Path


def test_jordan_deterministic_frontend():
    run = subprocess.run(['node', '--test', 'tests/frontend/jordan.test.cjs'],
                         cwd=Path(__file__).resolve().parents[1], capture_output=True,
                         text=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr
