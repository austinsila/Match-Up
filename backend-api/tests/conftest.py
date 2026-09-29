import os
import sys
from pathlib import Path

# Must be set before settings/security are imported. Does not override a real env.
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.pop("CLOCK_OFFSET", None)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
