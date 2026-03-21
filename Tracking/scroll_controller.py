"""
scroll_controller.py — Head-pitch-driven page scrolling.

When enabled, head pitch is mapped to scroll speed instead of cursor movement.
  Tilt up   → scroll up
  Tilt down → scroll down
  Hold still (within dead zone) → no scroll

Voice commands toggle the mode:
  "Hey Node scroll"  → enable
  "Hey Node unlock"  → disable
"""

from __future__ import annotations

import threading


try:
    from pynput.mouse import Controller as _Controller
    _mouse = _Controller()
    _SCROLL_AVAILABLE = True
except Exception:
    _mouse = None
    _SCROLL_AVAILABLE = False


class ScrollController:
    """Converts head pitch to mouse scroll events when enabled."""

    def __init__(self, cfg) -> None:
        self._cfg     = cfg
        self._enabled = False
        self._accum   = 0.0
        self._lock    = threading.Lock()

    # ── Public ────────────────────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def enable(self) -> None:
        with self._lock:
            self._enabled = True
            self._accum   = 0.0
        print("[Scroll] Scroll mode ON")

    def disable(self) -> None:
        with self._lock:
            self._enabled = False
            self._accum   = 0.0
        print("[Scroll] Scroll mode OFF")

    def update(self, pitch_offset: float) -> None:
        """
        Call every frame with the current pitch angle.
        Does nothing when scroll mode is off.

        pitch_offset > 0 → head tilted up → scroll up (positive dy).
        """
        with self._lock:
            if not self._enabled:
                return
            accum = self._accum

        cfg  = self._cfg
        dead = cfg.DEAD_ZONE_PITCH
        maxp = cfg.MAX_PITCH

        if abs(pitch_offset) < dead:
            return

        norm  = min(1.0, (abs(pitch_offset) - dead) / max(maxp - dead, 1e-6))
        delta = norm * cfg.SCROLL_SPEED_SCALE / 30.0   # ticks/frame at ~30 fps
        accum += delta if pitch_offset > 0 else -delta

        ticks = int(accum)
        accum -= ticks

        with self._lock:
            self._accum = accum

        if ticks and _SCROLL_AVAILABLE:
            _mouse.scroll(0, ticks)
