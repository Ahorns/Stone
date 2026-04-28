"""Single source of truth for filesystem paths used by Waymo scripts.

Importing scripts should always use these constants instead of hardcoding
absolute paths. Layout matches `waymo/` workspace.
"""

from pathlib import Path

# Repo root: parent of darwin_waymo/
REPO_ROOT = Path(__file__).resolve().parent.parent

# Top-level workspace
WAYMO_DIR = REPO_ROOT / "waymo"

# Subfolders
DATA_DIR = WAYMO_DIR / "data"
SCRIPTS_DIR = WAYMO_DIR / "scripts"
OUTPUTS_DIR = WAYMO_DIR / "outputs"
VIZ_DIR = OUTPUTS_DIR / "viz"
SUBMISSIONS_DIR = OUTPUTS_DIR / "submissions"
RESULTS_DIR = WAYMO_DIR / "results"
BASELINES_RESULTS_DIR = RESULTS_DIR / "baselines"
DOCS_DIR = WAYMO_DIR / "docs"

# Default validation shard (the only one downloaded so far)
DEFAULT_VALIDATION_SHARD = DATA_DIR / "validation.tfrecord-00000-of-00150"


def ensure_dirs():
    """Create all output dirs if missing. Idempotent."""
    for d in (VIZ_DIR, SUBMISSIONS_DIR, BASELINES_RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
