"""Bridges the ``grabit`` logger to Qt signals so GUI widgets can show log
lines live, without any widget touching the logging module directly from a
worker thread (Qt signal/slot delivery across threads is queued and safe;
touching a QPlainTextEdit directly from ``DownloadThread`` would not be).
"""
from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal


class QtLogBridge(QObject):
    line_emitted = Signal(str, str)  # level, formatted message

    _instance: "QtLogBridge | None" = None

    @classmethod
    def instance(cls) -> "QtLogBridge":
        if cls._instance is None:
            cls._instance = QtLogBridge()
        return cls._instance


class _BridgeHandler(logging.Handler):
    def __init__(self, bridge: QtLogBridge):
        super().__init__()
        self._bridge = bridge
        self.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            return
        self._bridge.line_emitted.emit(record.levelname, msg)


def install(logger_name: str = "grabit") -> QtLogBridge:
    bridge = QtLogBridge.instance()
    logger = logging.getLogger(logger_name)
    if not any(isinstance(h, _BridgeHandler) for h in logger.handlers):
        logger.addHandler(_BridgeHandler(bridge))
    return bridge
