from __future__ import annotations

import pathlib
from typing import Any

import yaml

from .schema import Settings


def load_settings(path: str | pathlib.Path) -> Settings:
    """Load configuration from YAML into a Settings instance."""
    config_path = pathlib.Path(path).expanduser().resolve()
    with config_path.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh) or {}
    return Settings.model_validate(data)
