"""
GrabIt — Universal Media Downloader
====================================

A modular, plugin-style desktop application that detects the platform behind
a pasted URL and hands it to the most appropriate download engine (yt-dlp,
gallery-dl, Instaloader, direct HTTP, and a dozen more specialized backends).

Package layout
--------------
grabit/
    config.py             Paths, portable-mode detection, persisted user settings
    logging_setup.py      Central logging configuration
    app.py                Application bootstrap / entry point used by main.py
    core/                 Pure logic with no GUI or third-party engine imports
        models.py           Dataclasses shared across the app (options, results, routing)
        exceptions.py       Cooperative pause/cancel control-flow exceptions
        url_utils.py        URL validation & extraction helpers
        router.py           SmartRouter: URL -> engine decision
        retry.py            Exponential-backoff retry decorator
    dependencies/         Dependency detection & (explicit, opt-in) installation
    engines/              One module (or small family) per download backend,
                           each registering itself with @register_engine
    workers/              QThread workers that drive engines from the GUI
    gui/                  PySide6 widgets; the only layer that imports Qt
"""

__version__ = "1.0.4"
__app_name__ = "GrabIt"
