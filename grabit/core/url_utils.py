"""URL validation and extraction helpers.

Used by both the single-URL entry field and the batch importer, which
accepts TXT, CSV/TSV, JSON, YAML, XML/RSS/HTML and Markdown files and needs
to pull URLs out of arbitrarily nested structures.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
from typing import Any, List

URL_REGEX = re.compile(r'https?://[^\s<>"\'\)\(\[\]\{\}]+')

_STRUCTURED_URL_KEYS = ("url", "link", "href", "source", "src", "download")


def is_valid_url(url: str) -> bool:
    """Return True if ``url`` looks like something an engine can act on.

    Accepts standard http(s) links, magnet links (must carry a BitTorrent
    info-hash), and the app's own ``rclone://remote/path`` pseudo-scheme.
    """
    value = (url or "").strip()
    if not value:
        return False
    if value.lower().startswith("magnet:?"):
        return "xt=urn:btih:" in value.lower()
    if value.lower().startswith("rclone://"):
        return len(value) > len("rclone://") + 2
    return bool(re.match(r"https?://[^\s]+(?:\.[^\s]+|/[^\s]*)$", value, re.I))


def sanitize_filename(name: str, fallback: str = "downloaded_file") -> str:
    """Strip path-traversal/unsafe characters from a filename that came
    from untrusted external input (HTTP headers, browser download events,
    remote metadata). Collapses any directory components to a plain name."""
    name = (name or "").strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = os.path.basename(name)
    name = name.strip(" .")
    return name or fallback


def extract_urls_regex(text: str) -> List[str]:
    """Best-effort fallback: pull every http(s) URL out of free-form text."""
    urls = URL_REGEX.findall(text or "")
    cleaned = []
    for u in urls:
        u = u.rstrip(".,;:!?")
        if is_valid_url(u):
            cleaned.append(u)
    return cleaned


def extract_urls_from_structure(data: Any) -> List[str]:
    """Recursively pull URLs out of a parsed JSON/YAML structure.

    Looks first for common "link-shaped" keys (``url``, ``href``, ...) and
    otherwise recurses into every value, so it degrades gracefully on
    structures that don't follow any particular convention.
    """
    urls: List[str] = []
    if isinstance(data, str):
        if is_valid_url(data):
            urls.append(data)
        else:
            urls.extend(extract_urls_regex(data))
    elif isinstance(data, list):
        for item in data:
            urls.extend(extract_urls_from_structure(item))
    elif isinstance(data, dict):
        for key in _STRUCTURED_URL_KEYS:
            v = data.get(key)
            if isinstance(v, str) and is_valid_url(v):
                urls.append(v)
        for k, v in data.items():
            if k in _STRUCTURED_URL_KEYS:
                continue
            urls.extend(extract_urls_from_structure(v))
    return urls


def _dedupe(urls: List[str]) -> List[str]:
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def parse_urls_from_file(filepath: str) -> List[str]:
    """Extract URLs from a file, dispatching on its extension.

    Falls back to a plain regex scan whenever the structured parse fails or
    yields nothing, so a malformed CSV or a plain-text list with a ``.json``
    extension still produces usable results instead of an empty list.
    """
    ext = os.path.splitext(filepath)[1].lower()
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        try:
            with open(filepath, "rb") as f:
                content = f.read().decode("utf-8", errors="ignore")
        except OSError:
            return []

    urls: List[str] = []
    if ext == ".json":
        try:
            data = json.loads(content)
            urls = extract_urls_from_structure(data)
        except (json.JSONDecodeError, ValueError):
            urls = extract_urls_regex(content)
    elif ext in (".csv", ".tsv"):
        delimiter = "," if ext == ".csv" else "\t"
        try:
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            for row in reader:
                for cell in row:
                    cell = cell.strip().strip('"').strip("'")
                    if is_valid_url(cell):
                        urls.append(cell)
                    elif "http" in cell:
                        urls.extend(extract_urls_regex(cell))
        except csv.Error:
            urls = extract_urls_regex(content)
        if not urls:
            urls = extract_urls_regex(content)
    elif ext in (".yaml", ".yml"):
        try:
            import yaml  # local import: optional dependency
            data = yaml.safe_load(content)
            urls = extract_urls_from_structure(data)
        except ImportError:
            urls = extract_urls_regex(content)
        except yaml.YAMLError:
            urls = extract_urls_regex(content)
    elif ext in (".xml", ".html", ".htm", ".xhtml", ".rss", ".atom"):
        urls = extract_urls_regex(content)
    elif ext in (".md", ".markdown"):
        md_links = re.findall(r'\[[^\]]*\]\((https?://[^\)]+)\)', content)
        urls.extend([u for u in md_links if is_valid_url(u)])
        urls.extend(extract_urls_regex(content))
    else:
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#") or line.startswith("//"):
                continue
            if is_valid_url(line):
                urls.append(line)
        if not urls:
            urls = extract_urls_regex(content)

    return _dedupe(urls)
