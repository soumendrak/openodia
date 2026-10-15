"""``python -m openodia`` — same as the ``openodia`` command."""

import sys

from openodia.cli import main

if __name__ == "__main__":  # pragma: no cover - exercised via subprocess
    sys.exit(main())
