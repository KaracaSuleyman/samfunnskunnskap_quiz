#!/usr/bin/env python3
"""
Samfunnskunnskap Quiz – desktop application.

Opens the self-contained samfunnskunnskap_quiz.html file in a window.
Packaged with PyInstaller as an .exe (Windows) / .app (macOS).
"""

import os
import sys

import webview

WINDOW_TITLE = "Samfunnskunnskap Prøve"
HTML_FILE = "samfunnskunnskap_quiz.html"


def resource_path(relative: str) -> str:
    """Return the correct path whether bundled by PyInstaller or run from source."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def main() -> None:
    html_path = resource_path(HTML_FILE)
    webview.create_window(
        WINDOW_TITLE,
        url=html_path,
        width=920,
        height=860,
        min_size=(700, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
