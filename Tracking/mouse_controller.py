"""
mouse_controller.py
-------------------
Converts head yaw/pitch offsets (degrees) to an absolute screen position
using the same model as professional assistive tools (Enable Viacam, Camera Mouse):

  - Head at neutral (0°, 0°)      → cursor at screen centre
  - Head at ±MAX_YAW / ±MAX_PITCH → cursor at screen edge
  - Dead zone near neutral         → cursor held at centre, no jitter
  - Non-linear speed curve         → slow near centre (precision),
                                     fast at edges (coverage)
"""

from __future__ import annotations


try:
    from pynput.mouse import Button as _Button, Controller as _Controller
    _mouse = _Controller()
    MOUSE_AVAILABLE = True
except Exception as e:
    _mouse = None
    MOUSE_AVAILABLE = False
    print(f"[Warning] Mouse control unavailable: {e}")
    print("  macOS: grant Accessibility access to Terminal in")
    print("         System Settings → Privacy & Security → Accessibility")


class MouseController:

    def __init__(self, screen_w: int, screen_h: int, cfg, magnet=None) -> None:
        self._sw     = screen_w
        self._sh     = screen_h
        self._cfg    = cfg
        self._magnet = magnet   # optional CursorMagnet instance

    def update(self, yaw_offset: float, pitch_offset: float) -> tuple[int, int]:
        """
        Map head angles to a screen position and move the cursor.
        Returns the (x, y) screen position that was set.

        yaw_offset   > 0  →  head turned subject's RIGHT
        pitch_offset > 0  →  head tilted UP
        """
        cfg = self._cfg

        norm_x = self._curve(yaw_offset,   cfg.DEAD_ZONE_YAW,   cfg.MAX_YAW,   cfg.SPEED_EXPONENT)
        norm_y = self._curve(pitch_offset, cfg.DEAD_ZONE_PITCH, cfg.MAX_PITCH, cfg.SPEED_EXPONENT)

        if cfg.INVERT_YAW:
            norm_x = -norm_x
        if cfg.INVERT_PITCH:
            norm_y = -norm_y

        # Screen Y is inverted: pitch up → cursor higher → smaller screen_y
        screen_x = self._sw / 2.0 + norm_x * self._sw / 2.0
        screen_y = self._sh / 2.0 - norm_y * self._sh / 2.0

        # Apply cursor magnetism (potential-field attraction) before clamping
        if self._magnet is not None:
            screen_x, screen_y = self._magnet.update(screen_x, screen_y)

        screen_x = int(max(0, min(self._sw - 1, screen_x)))
        screen_y = int(max(0, min(self._sh - 1, screen_y)))

        if MOUSE_AVAILABLE:
            _mouse.position = (screen_x, screen_y)

        return screen_x, screen_y

    def click(self) -> None:
        if MOUSE_AVAILABLE:
            _mouse.click(_Button.left)

    @staticmethod
    def _curve(angle: float, dead_zone: float,
               max_angle: float, exponent: float) -> float:
        """
        Maps an angle (degrees) to a normalised value in [-1, 1].

        Within the dead zone → 0.0 (cursor at centre).
        Beyond max_angle     → ±1.0 (cursor at screen edge).
        Exponent > 1         → non-linear: slower near centre, faster at edges.
        """
        if abs(angle) < dead_zone:
            return 0.0
        sign      = 1.0 if angle > 0.0 else -1.0
        effective = (abs(angle) - dead_zone) / max(max_angle - dead_zone, 1e-6)
        effective = min(1.0, effective)
        return sign * (effective ** exponent)
