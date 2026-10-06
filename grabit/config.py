"""Application paths and persisted user settings.

Portable-mode detection is unchanged from the original script: if a
``portable.flag`` file sits next to the launcher, GrabIt keeps all its data
(including these settings) in a ``grab_data`` folder beside the launcher
instead of the user's home directory — handy for a USB-stick install.

Every security-sensitive toggle here defaults to the safe/explicit choice
(no silent mirror fallback, no silent sudo). See
:mod:`grabit.dependencies.manager` for why.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

SETTINGS_FILENAME = "settings.json"
_DEFAULT_CONCURRENT_BATCH_DOWNLOADS = 1  # 1 == old, fully sequential behavior


@dataclass
class AppConfig:
    portable: bool
    data_dir: Path
    default_save_dir: Path

    # User-editable, persisted settings (safe defaults):
    concurrent_batch_downloads: int = _DEFAULT_CONCURRENT_BATCH_DOWNLOADS
    allow_mirror_fallback: bool = False
    allow_sudo_system_install: bool = False
    auto_paste_from_clipboard: bool = True

    @property
    def settings_path(self) -> Path:
        return self.data_dir / SETTINGS_FILENAME

    # -- persistence ----------------------------------------------------
    def _editable_fields(self) -> Dict[str, Any]:
        data = asdict(self)
        for key in ("portable", "data_dir", "default_save_dir"):
            data.pop(key, None)
        return data

    def save(self) -> None:
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self._editable_fields(), f, indent=2, sort_keys=True)
        except OSError:
            logger.exception("Could not save settings to %s", self.settings_path)

    def _load_editable_fields(self) -> None:
        if not self.settings_path.exists():
            return
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, json.JSONDecodeError):
            logger.warning("Ignoring unreadable settings file at %s", self.settings_path)
            return
        for key, value in saved.items():
            if key in self._editable_fields():
                setattr(self, key, value)

    @classmethod
    def load(cls, script_dir: Path) -> "AppConfig":
        """Build the config for this run.

        ``script_dir`` should be the directory containing the top-level
        entry point (``main.py``) — that is where ``portable.flag`` is
        looked for, matching the original script's behavior of checking
        next to itself rather than next to any installed package files.
        """
        portable_flag = script_dir / "portable.flag"
        is_portable = portable_flag.exists()

        if is_portable:
            data_dir = script_dir / "grab_data"
            default_save_dir = data_dir / "Downloads"
        else:
            data_dir = Path.home() / ".grabit"
            default_save_dir = Path.home() / "Downloads" / "GrabIt"

        data_dir.mkdir(parents=True, exist_ok=True)
        os.environ["GRABIT_DATA_DIR"] = str(data_dir)

        config = cls(portable=is_portable, data_dir=data_dir, default_save_dir=default_save_dir)
        config._load_editable_fields()
        return config
