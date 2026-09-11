"""Prepare config/ and start Home Assistant for F5 debugging."""

from __future__ import annotations

import os
import runpy
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
SRC_YAML = ROOT / ".devcontainer" / "configuration.yaml"


def main() -> None:
    CONFIG.mkdir(parents=True, exist_ok=True)
    if SRC_YAML.exists():
        shutil.copy(SRC_YAML, CONFIG / "configuration.yaml")

    custom_components = str(ROOT / "custom_components")
    pythonpath = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    if custom_components not in pythonpath:
        pythonpath.insert(0, custom_components)
    os.environ["PYTHONPATH"] = os.pathsep.join(pythonpath)
    if custom_components not in sys.path:
        sys.path.insert(0, custom_components)

    os.chdir(ROOT)
    sys.argv = ["homeassistant", "--debug", "-c", str(CONFIG)]
    runpy.run_module("homeassistant", run_name="__main__")


if __name__ == "__main__":
    main()
