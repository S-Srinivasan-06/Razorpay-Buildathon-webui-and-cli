#!/usr/bin/env python3
"""Compatibility wrapper forwarding execution to src.cli.

Allows running both:
  python src/main.py ...
  python src/cli.py ...
"""

import sys
from pathlib import Path

# Ensure src/ is in sys.path
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from cli import main

if __name__ == "__main__":
    main()
