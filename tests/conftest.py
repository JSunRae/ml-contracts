import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TOOLS = BASE / 'tools'
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
