"""Compatibility wrapper for experiments.low_vram_vibed.finish."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.low_vram_vibed.finish import main

if __name__ == "__main__":
    main()
