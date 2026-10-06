"""Static "About" tab."""
from __future__ import annotations

from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

from grabit import __version__


class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml(f"""
        <div style='font-family: "Segoe UI"; color: #E8E8E8;'>
          <h1 style='color: #FF6B35; margin-bottom: 2px;'>GrabIt <span style='font-size: 18px; color: #A0A0A0;'>v{__version__}</span></h1>
          <p style='color: #B8B8B8;'>Universal media downloader with a layered, plugin-style engine architecture for video, audio, images, files, live streams and cloud remotes.</p>
          <hr style='border: 0; border-top: 1px solid #333333;'>
          <h3>Core Engine Stack</h3>
          <p style='color: #B8B8B8; line-height: 1.6;'>
            yt-dlp · gallery-dl · instaloader · pinterest-dl · gdown · bilix · twitch-archiver ·
            soundcloud-lib · RedDownloader · tiktok-downloader-py · instacapture · civitai-downloader ·
            aria2 · Streamlink · rclone · Playwright fallback · FFmpeg
          </p>
          <h3>Input Coverage</h3>
          <p style='color: #B8B8B8; line-height: 1.6;'>
            Major video and social platforms, image galleries and communities, direct file URLs,
            Google Drive, Dropbox, Mega, live-stream URLs, HLS/DASH manifests,
            BitTorrent / Magnet / Metalink sources, and compatible cloud remotes.
          </p>
          <h3>Download Workflow</h3>
          <p style='color: #B8B8B8; line-height: 1.6;'>
            Smart routing selects the most specific available engine. Generic web URLs can fall back
            to yt-dlp, while JavaScript-heavy pages can use Playwright as a secondary resolver.
            Direct files use HTTP or aria2 when available; live sources use Streamlink when available.
            Batch downloads can optionally run several URLs concurrently.
          </p>
          <h3>Batch &amp; Automation</h3>
          <p style='color: #B8B8B8; line-height: 1.6;'>
            Batch URL import supports TXT, CSV, TSV, JSON, XML, YAML, Markdown and HTML, with
            recursive URL extraction and clipboard support.
          </p>
          <h3>Privacy &amp; Dependencies</h3>
          <p style='color: #B8B8B8; line-height: 1.6;'>
            GrabIt never installs or updates a package without your explicit action, and only
            uses the official PyPI index unless you opt into mirror fallback in Settings.
          </p>
          <div style='margin-top: 14px; padding: 10px 12px; background: #171717; border: 1px solid #303030; border-radius: 6px;'>
            <span style='color: #9A9A9A; font-size: 11px;'>Open-source software · Released under the MIT License</span>
          </div>
        </div>
        """)
        layout.addWidget(about_text)
