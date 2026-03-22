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

import json
import re
import subprocess
import threading
import time
import urllib.parse
import webbrowser
import pathlib

try:
    from pynput.keyboard import Controller as _KbController, Key as _Key
    from pynput.mouse import Controller as _MouseController, Button as _Button
    _kb = _KbController()
    _mouse = _MouseController()
    _INPUT_AVAILABLE = True
except Exception:
    _kb = None
    _Key = None
    _mouse = None
    _Button = None
    _INPUT_AVAILABLE = False

# Signalled by recalibrate(); checked each frame in Tracking/main.py.
recalibrate_event = threading.Event()

_KB_ERR = "Keyboard control unavailable — grant Accessibility permission to Terminal."
_MOUSE_ERR = "Mouse control unavailable — grant Accessibility permission to Terminal."

# Maps natural-language key names → pynput Key constants.
_KEY_MAP: dict[str, object] = {}
if _Key is not None:
    _KEY_MAP = {
        "cmd": _Key.cmd, "command": _Key.cmd, "meta": _Key.cmd,
        "ctrl": _Key.ctrl, "control": _Key.ctrl,
        "shift": _Key.shift,
        "alt": _Key.alt, "option": _Key.alt,
        "enter": _Key.enter, "return": _Key.enter,
        "esc": _Key.esc, "escape": _Key.esc,
        "tab": _Key.tab,
        "space": _Key.space,
        "backspace": _Key.backspace,
        "delete": _Key.delete,
        "up": _Key.up, "down": _Key.down,
        "left": _Key.left, "right": _Key.right,
        "home": _Key.home, "end": _Key.end,
        "pageup": _Key.page_up, "pagedown": _Key.page_down,
        **{f"f{i}": getattr(_Key, f"f{i}") for i in range(1, 13)},
    }


# ── Search URL templates for popular sites ────────────────────────────────────

_SITE_SEARCH: dict[str, str] = {
    "amazon":       "https://www.amazon.com/s?k={q}",
    "youtube":      "https://www.youtube.com/results?search_query={q}",
    "reddit":       "https://www.reddit.com/search/?q={q}",
    "github":       "https://github.com/search?q={q}",
    "twitter":      "https://twitter.com/search?q={q}",
    "x":            "https://x.com/search?q={q}",
    "netflix":      "https://www.netflix.com/search?q={q}",
    "spotify":      "https://open.spotify.com/search/{q}",
    "wikipedia":    "https://en.wikipedia.org/w/index.php?search={q}",
    "ebay":         "https://www.ebay.com/sch/i.html?_nkw={q}",
    "google":       "https://www.google.com/search?q={q}",
    "bing":         "https://www.bing.com/search?q={q}",
}


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


def navigate_and_search(site: str, query: str) -> str:
    """Go to a website and immediately search for something on it.

    Prefer this over open_website + wait + type_text for any command like
    "go to X and search Y", "search Y on X", "find Y on X", "look up Y on X".

    Handles Amazon, YouTube, Reddit, GitHub, Twitter/X, Netflix, Spotify,
    Wikipedia, eBay, Google, Bing.  For any other site it opens the site's
    homepage and performs a Google "site:" search as a fallback.

    Args:
        site:  The site name or domain, e.g. "amazon", "youtube", "reddit.com".
        query: What to search for.
    """
    key = site.lower().removesuffix(".com").removesuffix(".org").removesuffix(".net").strip()
    encoded = urllib.parse.quote_plus(query)

    if key in _SITE_SEARCH:
        url = _SITE_SEARCH[key].format(q=encoded)
    else:
        # Fallback: Google site-restricted search
        url = f"https://www.google.com/search?q=site:{urllib.parse.quote(site)}+{encoded}"

    webbrowser.open(url)
    return f"Searching {site} for: {query}"


def find_on_page(query: str) -> str:
    """Open the browser's find-in-page bar and search for text on the current page.

    Use this when the user says "find X on this page", "search for X here",
    "look for X on this page", or "where is X".

    Args:
        query: The text to find on the current page.
    """
    if not _INPUT_AVAILABLE:
        return _KB_ERR
    press_keys("cmd+f")
    time.sleep(0.2)   # let the find bar appear
    _kb.type(query)
    return f'Find-in-page: "{query}"'


def wait(seconds: float) -> str:
    """Pause execution for a number of seconds.

    Use this between steps that require a page or app to finish loading —
    e.g. after open_website before typing in a search box.
    Maximum wait is 5 seconds.

    Args:
        seconds: How long to wait, e.g. 1.5, 2, 3.
    """
    duration = min(float(seconds), 5.0)
    time.sleep(duration)
    return f"Waited {duration:.1f}s"


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


# ── Typing & keyboard ─────────────────────────────────────────────────────────

def type_text(text: str) -> str:
    """Type text into the currently focused input field.

    Use this when the user says something like "type hello world" or
    "write my email address" — type the spoken words exactly as given.

    Args:
        text: The exact text to type.
    """
    if not _INPUT_AVAILABLE:
        return _KB_ERR
    _kb.type(text)
    return f'Typed: "{text}"'


def replace_text(text: str) -> str:
    """Replace all text in the currently focused input field with new text.

    Use this when the user says "retype", "replace with", "change it to",
    "write instead", or "replace the text with" — i.e. when they want to
    overwrite what is already in a field rather than append to it.

    Args:
        text: The new text to put in the field, replacing whatever was there.
    """
    if not _INPUT_AVAILABLE:
        return _KB_ERR
    press_keys("cmd+a")
    time.sleep(0.05)  # let the selection settle before typing
    _kb.type(text)
    return f'Replaced field contents with: "{text}"'


def right_click() -> str:
    """Right-click at the current mouse cursor position.

    Use this when the user says "right click", "context menu", or "secondary click".
    """
    if not _INPUT_AVAILABLE:
        return _MOUSE_ERR
    _mouse.click(_Button.right)
    return "Right-clicked."


def press_keys(keys: str) -> str:
    """Press a key or keyboard shortcut.

    Accepts natural-language key descriptions and converts them to actual
    key presses.  Modifier keys are combined with "+".

    Examples the model should produce:
        "cmd+s"           → ⌘S (save)
        "cmd+shift+t"     → reopen closed tab
        "cmd+c"           → copy
        "cmd+v"           → paste
        "cmd+z"           → undo
        "cmd+a"           → select all
        "escape"          → dismiss / cancel
        "enter"           → confirm
        "tab"             → next field
        "backspace"       → delete one character
        "cmd+left"        → beginning of line
        "cmd+shift+left"  → select to beginning of line
        "up" / "down"     → arrow keys

    Args:
        keys: A "+"-separated string of key names, e.g. "cmd+s", "escape",
              "cmd+shift+3".  Single characters are typed as-is (e.g. "a").
              Always use lowercase.
    """
    if not _INPUT_AVAILABLE:
        return _KB_ERR

    parts = [k.strip().lower() for k in keys.split("+")]

    resolved = []
    for part in parts:
        key = _KEY_MAP.get(part) or (part if len(part) == 1 else None)
        if key is None:
            return f"Unknown key: '{part}'"
        resolved.append(key)

    pressed = []
    try:
        for key in resolved:
            _kb.press(key)
            pressed.append(key)
    finally:
        for key in reversed(pressed):
            _kb.release(key)

    return f"Pressed: {keys}"


def recalibrate() -> str:
    """Re-calibrate the head-tracker neutral position.

    Call this when the user says "recalibrate", "reset the tracker",
    "re-centre", or similar.  The user should hold their head in their
    natural forward-facing position before or immediately after saying this.
    """
    recalibrate_event.set()
    return "Recalibrating — hold your head in neutral position."


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
    "DEAD_ZONE_YAW", "DEAD_ZONE_PITCH",
    "SPEED_EXPONENT",
    "FILTER_MIN_CUTOFF", "FILTER_BETA",
    "MAGNET_ENABLED", "MAGNET_RADIUS",
    "MAGNET_ALPHA_MAX", "MAGNET_STICKY_DAMP",
    "SHOW_DEBUG",
    "BLINK_EAR_THRESHOLD",
}

_CONFIG_PATH   = pathlib.Path(__file__).resolve().parent.parent / "Tracking" / "config.py"
_RUNTIME_PATH  = pathlib.Path(__file__).resolve().parent.parent / "Tracking" / "config.runtime.json"


def _read_runtime() -> dict:
    try:
        return json.loads(_RUNTIME_PATH.read_text())
    except Exception:
        return {"mouseSpeed": 3, "scrollSpeed": 3}


def _write_runtime(updates: dict) -> None:
    rt = _read_runtime()
    rt.update(updates)
    _RUNTIME_PATH.write_text(json.dumps(rt, indent=2))
    # Signal Electron to restart the tracker with the new config.
    print(f"__HANDSFREE__{json.dumps({'type': 'restart_requested'})}", flush=True)


def _set_speed(key: str, noun: str, level: int) -> str:
    level = max(1, min(5, int(level)))
    _write_runtime({key: level})
    return f"{noun} speed set to {level}. Restarting tracker."


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


def set_mouse_speed(level: int) -> str:
    """Set the mouse movement speed on a scale of 1 to 5.

    1 = slowest (requires large head movements to reach screen edges).
    5 = fastest (small head movements move the cursor far).
    3 is the default.  Changes take effect after the tracker restarts.

    Use this when the user says "mouse speed 4", "make the mouse faster",
    "slow down the cursor", "set mouse to level 2", etc.

    Args:
        level: Speed level, 1 (slowest) to 5 (fastest).
    """
    return _set_speed("mouseSpeed", "Mouse", level)


def set_scroll_speed(level: int) -> str:
    """Set the scroll speed on a scale of 1 to 5.

    1 = slowest scroll, 5 = fastest scroll.  3 is the default.
    Changes take effect after the tracker restarts.

    Use this when the user says "scroll speed 2", "make scrolling faster",
    "slower scroll", "set scroll to 4", etc.

    Args:
        level: Speed level, 1 (slowest) to 5 (fastest).
    """
    return _set_speed("scrollSpeed", "Scroll", level)


def change_tracker_config(setting: str, value: str) -> str:
    """Change a MouseTracker configuration setting.

    Changes are written to Tracking/config.py and take effect after the
    tracker is restarted.

    Args:
        setting: The config key to change, e.g. "DEAD_ZONE_YAW", "MAGNET_ENABLED".
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
    return f"Set {key} = {value} (restart the tracker to apply)"
