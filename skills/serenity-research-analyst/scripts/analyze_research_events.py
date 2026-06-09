#!/usr/bin/env python3
"""Run the repository-level research event analyzer from inside the skill."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "analyze_research_events.py"

if not SCRIPT.exists():
    raise SystemExit(f"Could not find repository analyzer: {SCRIPT}")

sys.path.insert(0, str(ROOT))
runpy.run_path(str(SCRIPT), run_name="__main__")
