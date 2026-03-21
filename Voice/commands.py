"""
Voice/commands.py — All executable command functions exposed as Gemini tools.

Design rules:
  - Each function has a clear, imperative docstring — Gemini uses this to
    decide when and how to call it.
  - Parameters use plain types (str, float, bool) — the SDK auto-generates
    the JSON schema from type annotations + the Args: section in the docstring.
  - Each function returns a plain str describing what happened.  Gemini
    relays this back to the user.

To add a new command: write a function here, then import and register it
in agent.py's TOOLS list.
"""

from __future__ import annotations

import re
import subprocess
import urllib.parse
import webbrowser
import pathlib


# ── Web ───────────────────────────────────────────────────────────────────────

def open_website(url: str) -> str:
    """Open a URL in the default web browser.

    Args:
        url: The URL to open.  If the user only said a domain (e.g. "github.com"),
             prepend "https://" automatically.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def search_web(query: str) -> str:
    """Search Google for a query and open the results page in the browser.

    Args:
        query: The search terms, exactly as the user said them.
    """
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    webbrowser.open(url)
    return f"Searching Google for: {query}"


# ── Applications ──────────────────────────────────────────────────────────────

def open_application(name: str) -> str:
    """Open a macOS application by name.

    Args:
        name: The application name as it appears in /Applications,
              e.g. "Spotify", "Slack", "Terminal", "Visual Studio Code".
    """
    result = subprocess.run(["open", "-a", name], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Could not open '{name}': {result.stderr.strip() or 'app not found'}"
    return f"Opened {name}"


# ── Browser tab management ────────────────────────────────────────────────────

def get_chrome_tabs() -> str:
    """Return a list of every open Chrome tab with its title and URL.

    Call this before switch_chrome_tab to see what is available.
    """
    try:
        from .browser import get_tabs
        tabs = get_tabs()
    except Exception as exc:
        return f"Could not read Chrome tabs: {exc}"
    if not tabs:
        return "No Chrome tabs found — is Chrome open?"
    return "Open tabs:\n" + "\n".join(f"  {t}" for t in tabs)


def switch_chrome_tab(search: str) -> str:
    """Switch Chrome to the tab whose title or URL best matches the search string.

    Args:
        search: A word or phrase in the tab title or URL, e.g. "YouTube", "GitHub".
    """
    try:
        from .browser import get_tabs, switch_tab
        tabs = get_tabs()
    except Exception as exc:
        return f"Could not read Chrome tabs: {exc}"
    if not tabs:
        return "No Chrome tabs found."
    low = search.lower()
    matches = [t for t in tabs if low in t.title.lower() or low in t.url.lower()]
    if not matches:
        return f"No tab matched '{search}'. Available: {', '.join(t.title for t in tabs[:5])}"
    best = matches[0]
    ok = switch_tab(best)
    return f"Switched to: {best.title}" if ok else f"Switch failed for: {best.title}"


# ── MouseTracker config ───────────────────────────────────────────────────────

# Allowlist — only these settings may be changed by voice to prevent accidents.
_ALLOWED = {
    "MAX_YAW", "MAX_PITCH",
    "DEAD_ZONE_YAW", "DEAD_ZONE_PITCH",
    "SPEED_EXPONENT",
    "FILTER_MIN_CUTOFF", "FILTER_BETA",
    "MAGNET_ENABLED", "MAGNET_RADIUS",
    "MAGNET_ALPHA_MAX", "MAGNET_STICKY_DAMP",
    "SHOW_DEBUG",
    "BLINK_EAR_THRESHOLD",
}

_CONFIG_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "Tracking" / "config.py"
)


def get_tracker_config() -> str:
    """Return the current MouseTracker configuration values.

    Use this when the user asks what settings are active or before changing one.
    """
    if not _CONFIG_PATH.exists():
        return "Tracking/config.py not found."

    lines = [
        "  " + line.strip()
        for line in _CONFIG_PATH.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#") and "=" in line
    ]
    return "Current tracker config:\n" + "\n".join(lines)


def change_tracker_config(setting: str, value: str) -> str:
    """Change a MouseTracker configuration setting.

    Changes are written to Tracking/config.py and take effect after the
    tracker is restarted.

    Args:
        setting: The config key to change, e.g. "MAX_YAW", "MAGNET_ENABLED".
                 Case-insensitive — will be uppercased automatically.
        value:   The new value as a string, e.g. "20.0", "True", "False", "130".
    """
    key = setting.strip().upper()

    if key not in _ALLOWED:
        return (
            f"'{key}' is not in the changeable settings list.\n"
            f"Allowed: {', '.join(sorted(_ALLOWED))}"
        )

    if not _CONFIG_PATH.exists():
        return "Tracking/config.py not found."

    text = _CONFIG_PATH.read_text()
    new_text, n = re.subn(
        rf"^(\s*{re.escape(key)}\s*=\s*)(.+)$",
        rf"\g<1>{value}",
        text,
        flags=re.MULTILINE,
    )

    if n == 0:
        return f"Setting '{key}' was not found in config.py."

    _CONFIG_PATH.write_text(new_text)
    return f"Set {key} = {value}  (restart the tracker to apply)"
