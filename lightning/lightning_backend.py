"""Compatibility entry point using shared source; never extracts or patches a ZIP."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "cloud_backend.py"), run_name="__main__")
