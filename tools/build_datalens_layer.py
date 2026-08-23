"""Run the existing Expedia CORE and analytics builders, then validate the seven DataLens marts."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    [sys.executable, str(ROOT / "tools" / "build_core.py")],
    [sys.executable, str(ROOT / "tools" / "build_analytics.py")],
    [sys.executable, str(ROOT / "tools" / "validate_datalens_marts.py")],
]

def main() -> int:
    for step in STEPS:
        print("\n>>>", " ".join(step))
        completed = subprocess.run(step, cwd=ROOT)
        if completed.returncode != 0:
            return completed.returncode
    print("\nDONE: CORE + analytics + 7 DataLens marts validation.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
