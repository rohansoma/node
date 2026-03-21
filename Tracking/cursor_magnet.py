"""
cursor_magnet.py
----------------
Smooth cursor attraction toward nearby UI buttons.

Algorithm: velocity-gated potential-field attraction, validated by:
  - Bezerianos & Balakrishnan, CHI 2005 "The Vacuum" (gravity cursor)
  - Worden et al., CHI 1997 "Sticky Icons" (sticky-zone damping)

Jitter-free design — three layers of stabilisation:
  1. Target hysteresis  — once locked, the target only releases when the
     cursor moves beyond MAGNET_UNLOCK_RADIUS (> MAGNET_RADIUS).  Prevents
     oscillation between two nearby buttons.
  2. Velocity LPF (τ ≈ 8 frames) — smooths micro-tremor speed spikes so the
     velocity gate doesn't flicker.
  3. Alpha LPF — the attraction strength itself is low-pass filtered, so
     any residual speed fluctuation causes a slow drift in alpha, not a
     sudden jump in the cursor.

Target discovery uses the macOS Accessibility API (AXUIElement) on a
background thread.  Requires Accessibility permission in
System Settings → Privacy & Security.
"""

from __future__ import annotations

import math
import threading
from typing import Optional


# ── macOS Accessibility API ───────────────────────────────────────────────────

_AX_AVAILABLE = False
_system_wide  = None

try:
    from ApplicationServices import (           # type: ignore[import]
        AXUIElementCreateSystemWide,
        AXUIElementCopyElementAtPosition,
        AXUIElementCopyAttributeValue,
        kAXRoleAttribute,
        kAXPositionAttribute,
        kAXSizeAttribute,
        kAXParentAttribute,
        kAXErrorSuccess,
        AXValueGetValue,
        kAXValueCGPointType,
        kAXValueCGSizeType,
        AXIsProcessTrustedWithOptions,
        kAXTrustedCheckOptionPrompt,
    )
    _AX_AVAILABLE = bool(
        AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: False})
    )
    if _AX_AVAILABLE:
        _system_wide = AXUIElementCreateSystemWide()
    else:
        print("[Magnet] Accessibility permission not granted — magnetism disabled.")
        print("         System Settings → Privacy & Security → Accessibility")
except Exception as _e:
    print(f"[Magnet] ApplicationServices unavailable ({_e}) — magnetism disabled.")


_CLICKABLE_ROLES = frozenset({
    "AXButton", "AXCheckBox", "AXRadioButton", "AXMenuItem",
    "AXMenuButton", "AXPopUpButton", "AXComboBox", "AXLink",
    "AXDisclosureTriangle", "AXTextField",
})


# ── AX helpers ────────────────────────────────────────────────────────────────

def _element_rect(el) -> Optional[tuple[float, float, float, float]]:
    """Return (center_x, center_y, width, height) for an AX element, or None."""
    err, pos = AXUIElementCopyAttributeValue(el, kAXPositionAttribute, None)
    if err != kAXErrorSuccess or pos is None:
        return None
    ok, pt = AXValueGetValue(pos, kAXValueCGPointType, None)
    if not ok:
        return None
    err2, sz = AXUIElementCopyAttributeValue(el, kAXSizeAttribute, None)
    if err2 != kAXErrorSuccess or sz is None:
        return None
    ok2, size = AXValueGetValue(sz, kAXValueCGSizeType, None)
    if not ok2:
        return None
    if size.width < 6 or size.height < 6:
        return None
    return (pt.x + size.width / 2.0, pt.y + size.height / 2.0,
            size.width, size.height)


def _walk_to_clickable(el, max_depth: int = 5):
    """Walk AX parent chain until a clickable role is found, or return None."""
    for _ in range(max_depth):
        if el is None:
            return None
        err, role = AXUIElementCopyAttributeValue(el, kAXRoleAttribute, None)
        if err == kAXErrorSuccess and role in _CLICKABLE_ROLES:
            return el
        err2, parent = AXUIElementCopyAttributeValue(el, kAXParentAttribute, None)
        if err2 != kAXErrorSuccess or parent is None:
            return None
        el = parent
    return None


def _probe_targets(
    cursor_x: float, cursor_y: float, radius: float
) -> list[dict]:
    """
    Probe a grid of 25 points around the cursor to discover nearby clickable
    AX elements.  Returns target dicts (cx, cy, w, h, dist) sorted nearest-first.
    Runs on a background thread — ~5–10 ms per call on modern macOS.
    """
    if not _AX_AVAILABLE or _system_wide is None:
        return []

    seen: dict[tuple[int, int], dict] = {}

    probe_pts: list[tuple[float, float]] = [(cursor_x, cursor_y)]
    for deg in range(0, 360, 45):
        rad = math.radians(deg)
        for frac in (0.25, 0.60, 1.00):
            r = radius * frac
            probe_pts.append((cursor_x + r * math.cos(rad),
                               cursor_y + r * math.sin(rad)))

    for px, py in probe_pts:
        try:
            err, el = AXUIElementCopyElementAtPosition(
                _system_wide, float(px), float(py), None
            )
        except Exception:
            continue
        if err != kAXErrorSuccess or el is None:
            continue
        clickable = _walk_to_clickable(el)
        if clickable is None:
            continue
        rect = _element_rect(clickable)
        if rect is None:
            continue
        cx, cy, w, h = rect
        key = (round(cx), round(cy))
        if key not in seen:
            seen[key] = {
                "cx": cx, "cy": cy, "w": w, "h": h,
                "dist": math.hypot(cx - cursor_x, cy - cursor_y),
            }

    return sorted(seen.values(), key=lambda t: t["dist"])


# ── Main class ────────────────────────────────────────────────────────────────

class CursorMagnet:
    """
    Velocity-gated cursor attraction toward nearby UI buttons.

    Call update(raw_x, raw_y) each frame with the head-tracker's desired
    screen position.  Returns the attracted position (or raw if no target
    is in range).

    Thread safety: update() runs on the main thread; the background scanner
    only touches shared state under _lock.
    """

    def __init__(self, cfg) -> None:
        self._cfg = cfg

        # ── Lock state ────────────────────────────────────────────────────────
        # Own copy of the locked target dict — never a reference into the
        # shared scan result list, so mutations here don't corrupt scan data.
        self._locked: Optional[dict] = None

        # ── Smoothed values ───────────────────────────────────────────────────
        self._vel_lpf   = 0.0   # low-pass filtered cursor speed  (px/frame)
        self._alpha_lpf = 0.0   # low-pass filtered attraction alpha (0–ALPHA_MAX)
        self._prev_raw: Optional[tuple[float, float]] = None

        # ── Background AX scanner ─────────────────────────────────────────────
        self._lock          = threading.Lock()
        self._scan_x        = 0.0
        self._scan_y        = 0.0
        self._scan_req      = threading.Event()
        self._scan_results: list[dict] = []
        self._running       = True
        self._frames_since_scan = 0

        self._thread = threading.Thread(
            target=self._scanner_loop, daemon=True, name="ax-scanner"
        )
        self._thread.start()

    # ── Public ────────────────────────────────────────────────────────────────

    def update(self, raw_x: float, raw_y: float) -> tuple[float, float]:
        """
        Apply magnetism.  Returns the (possibly attracted) screen position.
        raw_x / raw_y are the position the head-tracker wants to set.
        """
        cfg = self._cfg

        # ── 1. Cursor speed — slow LPF (τ ≈ 8 frames) ────────────────────────
        # A long time-constant smooths over natural micro-tremors so that the
        # velocity gate doesn't flicker open/closed on every frame.
        if self._prev_raw is not None:
            speed = math.hypot(raw_x - self._prev_raw[0], raw_y - self._prev_raw[1])
        else:
            speed = 0.0
        self._prev_raw = (raw_x, raw_y)
        self._vel_lpf = 0.88 * self._vel_lpf + 0.12 * speed

        # ── 2. Schedule background AX scan (steady cadence only) ──────────────
        # No early rescans on speed — they cause the target list to churn and
        # destabilise the lock.  The hysteresis below keeps the lock stable
        # between scans.
        self._frames_since_scan += 1
        if self._frames_since_scan >= cfg.MAGNET_SCAN_INTERVAL:
            self._frames_since_scan = 0
            with self._lock:
                self._scan_x = raw_x
                self._scan_y = raw_y
            self._scan_req.set()

        # ── 3. Snapshot scan results (never mutate the shared list) ───────────
        with self._lock:
            results = list(self._scan_results)

        # ── 4. Hysteresis-based target locking ────────────────────────────────
        #
        # ACQUIRE: if not locked, take the nearest candidate inside MAGNET_RADIUS.
        # HOLD:    if locked, recompute distance to the fixed target centre.
        #          Only release when the cursor exits MAGNET_UNLOCK_RADIUS
        #          (which is larger than MAGNET_RADIUS), forming a hysteresis band
        #          that prevents oscillation between two nearby buttons.
        if self._locked is None:
            for cand in results:
                d = math.hypot(cand["cx"] - raw_x, cand["cy"] - raw_y)
                if d <= cfg.MAGNET_RADIUS:
                    self._locked = dict(cand)   # own copy — safe to mutate
                    self._locked["dist"] = d
                    break
        else:
            lx, ly = self._locked["cx"], self._locked["cy"]
            lock_dist = math.hypot(raw_x - lx, raw_y - ly)
            self._locked["dist"] = lock_dist

            if lock_dist > cfg.MAGNET_UNLOCK_RADIUS:
                # Cursor left the hysteresis zone — release
                self._locked    = None
                self._alpha_lpf = 0.0

        if self._locked is None or not cfg.MAGNET_ENABLED:
            # Decay alpha to zero cleanly rather than snapping (avoids a pop
            # if the target reappears quickly)
            self._alpha_lpf *= 0.6
            return raw_x, raw_y

        tx   = self._locked["cx"]
        ty   = self._locked["cy"]
        dist = self._locked["dist"]

        if dist < 1.0:
            self._alpha_lpf = cfg.MAGNET_ALPHA_MAX
            return tx, ty

        # ── 5. Compute target alpha ────────────────────────────────────────────
        # Velocity gate: alpha → 0 when moving fast (intentional sweep),
        #                alpha → ALPHA_MAX when head is still (aiming at target).
        speed_factor = 1.0 / (1.0 + self._vel_lpf / cfg.MAGNET_SPEED_SCALE)

        # Distance gate: smooth 1 - (d/R)² profile — zero force at boundary,
        # maximum at centre.  Prevents jarring snap-to-target at range edge.
        dist_factor = max(0.0, 1.0 - (dist / cfg.MAGNET_RADIUS) ** 2)

        target_alpha = cfg.MAGNET_ALPHA_MAX * speed_factor * dist_factor

        # ── 6. Smooth alpha (LPF) ─────────────────────────────────────────────
        # Filtering alpha itself is the key fix for cursor jitter.  Even if
        # vel_lpf still has some ripple, it now produces a slow drift in alpha
        # rather than a frame-to-frame jump in cursor position.
        s = cfg.MAGNET_ALPHA_SMOOTH
        self._alpha_lpf = s * self._alpha_lpf + (1.0 - s) * target_alpha
        alpha = self._alpha_lpf

        # ── 7. Apply attraction ────────────────────────────────────────────────
        out_x = raw_x + alpha * (tx - raw_x)
        out_y = raw_y + alpha * (ty - raw_y)

        # ── 8. Sticky zone ────────────────────────────────────────────────────
        # Inside the target's bounding box, blend further toward centre so the
        # cursor settles without fighting head micro-tremor.
        tw, th = self._locked["w"], self._locked["h"]
        if abs(out_x - tx) < tw / 2.0 and abs(out_y - ty) < th / 2.0:
            d = cfg.MAGNET_STICKY_DAMP
            out_x = out_x * (1.0 - d) + tx * d
            out_y = out_y * (1.0 - d) + ty * d

        return out_x, out_y

    def current_target(self) -> Optional[dict]:
        """The currently locked target dict, or None."""
        return self._locked

    def stop(self) -> None:
        """Shut down the background scanner thread."""
        self._running = False
        self._scan_req.set()

    # ── Background scanner ────────────────────────────────────────────────────

    def _scanner_loop(self) -> None:
        while self._running:
            self._scan_req.wait()
            self._scan_req.clear()
            if not self._running:
                break
            with self._lock:
                cx, cy = self._scan_x, self._scan_y
            results = _probe_targets(cx, cy, self._cfg.MAGNET_RADIUS)
            with self._lock:
                self._scan_results = results
