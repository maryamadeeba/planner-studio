"""Point the app at a throw-away data folder before anything imports app.models (never touch the real studio.db)."""
import os
import tempfile

os.environ["PLANNER_STUDIO_ROOT"] = tempfile.mkdtemp(prefix="planner_tests_")
