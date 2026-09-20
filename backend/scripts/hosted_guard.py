"""Operational acknowledgement for hosted checks; not cloud identity verification."""
import sys
from pathlib import Path

TARGETS = ("aws", "lightning", "colab")


def add_hosted_argument(parser):
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cloud-target", choices=TARGETS)
    # Retain existing AWS/Colab evaluation commands without source edits.
    for target in TARGETS:
        group.add_argument(f"--{target}-only", dest="cloud_target", action="store_const", const=target)


def require_hosted(target):
    if target not in TARGETS or sys.platform != "linux":
        raise RuntimeError("Run only on the explicitly selected hosted Linux runtime, never the development PC.")
    if target == "lightning" and not Path("/teamspace/studios/this_studio").is_dir():
        raise RuntimeError("Select a hosted Lightning AI Studio terminal.")
    if target == "colab" and not Path("/content").is_dir():
        raise RuntimeError("Select a hosted Colab runtime.")
