"""Conftest for hrtool test suite."""
import sys
from pathlib import Path

# Ensure the repository root is findable for imports like `from manager import MainWindow`
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))