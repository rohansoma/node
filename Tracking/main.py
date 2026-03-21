"""
main.py — MouseTracker (head tracking edition)
-----------------------------------------------
Controls the mouse cursor by mapping head rotation to an absolute screen
position — the same model used by professional assistive tools like
Enable Viacam and Camera Mouse.

  Neutral head position  →  cursor at screen centre
  Head turned right      →  cursor moves right
  Head tilted up         →  cursor moves up
  Double blink           →  left click

Controls (debug window must be focused):
    R        — re-calibrate neutral position (look straight at camera first)
    S        — toggle debug window on/off
    Q / ESC  — quit
"""

from __future__ import annotations

import pathlib
import sys
import time
import tkinter as tk

import cv2
import numpy as np

from config           import Config
from cursor_magnet    import CursorMagnet, _AX_AVAILABLE
from head_tracker     import HeadTracker, OneEuroFilter
from mouse_controller import MouseController, MOUSE_AVAILABLE

# Make the project root importable so Voice/ can be found regardless of the
# working directory the user launches the tracker from.
_PROJECT_ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _start_voice() -> None:
    """Try to start the voice command thread. Silently skips if not configured."""
    try:
        from Voice.main   import start_background_thread
        from Voice.config import VoiceConfig
        start_background_thread(VoiceConfig())
    except ImportError:
        pass   # google-genai / requests not installed — voice simply won't run
    except Exception as exc:
        print(f"[Voice] Could not start: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Blink detector
# ─────────────────────────────────────────────────────────────────────────────

class BlinkDetector:
    """
    Detects double blinks from the Eye Aspect Ratio (EAR).

    A blink is registered when EAR drops below the threshold for at least
    BLINK_MIN_FRAMES consecutive frames, then rises again.
    Two blinks within DOUBLE_BLINK_WINDOW seconds trigger a left click.
    Single blinks are intentionally ignored (people blink ~15×/min naturally).
    """

    def __init__(self, cfg) -> None:
        self._threshold  = cfg.BLINK_EAR_THRESHOLD
        self._min_frames = cfg.BLINK_MIN_FRAMES
        self._window     = cfg.DOUBLE_BLINK_WINDOW
        self._consec     = 0     # consecutive frames eye has been closed
        self._blink_times: list[float] = []

    def update(self, ear: float) -> bool:
        """Feed current EAR. Returns True the moment a double-blink is confirmed."""
        if ear < self._threshold:
            self._consec += 1
            return False

        # Eye just reopened — did a blink complete?
        if self._consec >= self._min_frames:
            now = time.monotonic()
            # Discard blinks outside the rolling window
            self._blink_times = [t for t in self._blink_times
                                  if now - t < self._window]
            self._blink_times.append(now)
            if len(self._blink_times) >= 2:
                self._blink_times.clear()
                self._consec = 0
                return True   # double blink confirmed

        self._consec = 0
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_screen_size() -> tuple[int, int]:
    root = tk.Tk()
    root.withdraw()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h


# ─────────────────────────────────────────────────────────────────────────────
# Debug overlay
# ─────────────────────────────────────────────────────────────────────────────

def _draw_overlay(frame: np.ndarray,
                  yaw: float, pitch: float,
                  ear: float,
                  cursor_x: int, cursor_y: int,
                  screen_w: int, screen_h: int,
                  face_found: bool,
                  blink_flash: bool,
                  magnet_target: dict | None = None) -> np.ndarray:
    h, w = frame.shape[:2]

    # ── top bar ───────────────────────────────────────────────────────────────
    cv2.rectangle(frame, (0, 0), (w, 90), (20, 20, 20), -1)

    dot_col = (0, 220, 0) if face_found else (0, 0, 220)
    cv2.circle(frame, (18, 18), 7, dot_col, -1)
    cv2.putText(frame, "Face detected" if face_found else "No face — look at camera",
                (32, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1, cv2.LINE_AA)

    cv2.putText(frame, f"Yaw {yaw:+5.1f}°  Pitch {pitch:+5.1f}°  EAR {ear:.2f}",
                (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 180, 180), 1, cv2.LINE_AA)

    if blink_flash:
        cv2.putText(frame, "CLICK", (10, 76),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2, cv2.LINE_AA)
    elif magnet_target is not None:
        cv2.putText(frame, "MAGNET", (10, 76),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 120), 2, cv2.LINE_AA)
    elif not MOUSE_AVAILABLE:
        cv2.putText(frame, "Mouse OFF — grant Accessibility permission to Terminal",
                    (10, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (0, 100, 255), 1, cv2.LINE_AA)

    # ── mini screen map (bottom-right) ────────────────────────────────────────
    map_w, map_h = 120, 80
    map_x0 = w - map_w - 8
    map_y0 = h - map_h - 28
    cv2.rectangle(frame, (map_x0, map_y0), (map_x0 + map_w, map_y0 + map_h), (40, 40, 40), -1)
    cv2.rectangle(frame, (map_x0, map_y0), (map_x0 + map_w, map_y0 + map_h), (90, 90, 90), 1)
    mx, my = map_x0 + map_w // 2, map_y0 + map_h // 2
    cv2.line(frame, (map_x0, my), (map_x0 + map_w, my), (60, 60, 60), 1)
    cv2.line(frame, (mx, map_y0), (mx, map_y0 + map_h), (60, 60, 60), 1)

    # Draw magnet target on the mini-map (diamond marker)
    if magnet_target is not None:
        tgt_mx = max(map_x0 + 3, min(map_x0 + map_w - 3,
                     map_x0 + int(magnet_target["cx"] / screen_w * map_w)))
        tgt_my = max(map_y0 + 3, min(map_y0 + map_h - 3,
                     map_y0 + int(magnet_target["cy"] / screen_h * map_h)))
        pts = np.array([[tgt_mx, tgt_my - 4], [tgt_mx + 4, tgt_my],
                         [tgt_mx, tgt_my + 4], [tgt_mx - 4, tgt_my]], np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 200, 120), thickness=1)

    dot_mx = max(map_x0 + 3, min(map_x0 + map_w - 3, map_x0 + int(cursor_x / screen_w * map_w)))
    dot_my = max(map_y0 + 3, min(map_y0 + map_h - 3, map_y0 + int(cursor_y / screen_h * map_h)))
    cv2.circle(frame, (dot_mx, dot_my), 5, (0, 200, 255), -1)

    # ── bottom hint ───────────────────────────────────────────────────────────
    cv2.rectangle(frame, (0, h - 22), (w, h), (20, 20, 20), -1)
    cv2.putText(frame, "R: recalibrate   S: toggle debug   Q / ESC: quit   double-blink: click",
                (8, h - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (130, 130, 130), 1, cv2.LINE_AA)

    return frame


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    cfg = Config()

    screen_w, screen_h = _get_screen_size()
    print(f"Screen: {screen_w}×{screen_h} logical px")

    # ── Camera ────────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(cfg.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  cfg.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.FRAME_HEIGHT)
    if not cap.isOpened():
        print("Error: cannot open camera — check CAMERA_INDEX in config.py")
        sys.exit(1)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera: {actual_w}×{actual_h}")

    # ── Components ────────────────────────────────────────────────────────────
    tracker      = HeadTracker(actual_w, actual_h)
    magnet       = CursorMagnet(cfg) if (cfg.MAGNET_ENABLED and _AX_AVAILABLE) else None
    mouse        = MouseController(screen_w, screen_h, cfg, magnet=magnet)
    blinker      = BlinkDetector(cfg)

    filter_yaw   = OneEuroFilter(min_cutoff=cfg.FILTER_MIN_CUTOFF, beta=cfg.FILTER_BETA)
    filter_pitch = OneEuroFilter(min_cutoff=cfg.FILTER_MIN_CUTOFF, beta=cfg.FILTER_BETA)

    # ── Voice commands ────────────────────────────────────────────────────────
    _start_voice()

    print()
    print("MouseTracker running.  Hold your head in your NEUTRAL position —")
    print("the first detected frame sets the centre point.")
    print()
    print("  R              — recalibrate neutral")
    print("  S              — toggle debug window")
    print("  Q / ESC        — quit")
    print("  Double blink   — left click")
    print()
    if magnet is not None:
        print("  Cursor magnetism ON — cursor drifts toward nearby buttons.")
    elif cfg.MAGNET_ENABLED and not _AX_AVAILABLE:
        print("  Cursor magnetism OFF — grant Accessibility permission to enable.")
    print()
    print("Tip: if cursor goes the wrong direction, flip INVERT_YAW / INVERT_PITCH in config.py")

    # ── Tracking loop ─────────────────────────────────────────────────────────
    show_debug    = cfg.SHOW_DEBUG
    yaw = pitch   = 0.0
    ear           = 0.3
    cursor_x      = screen_w // 2
    cursor_y      = screen_h // 2
    face_found    = False
    blink_flash   = False          # brief visual indicator on click
    flash_until   = 0.0
    magnet_target = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: failed to read camera frame")
            break

        result = tracker.process(frame)

        if result is not None:
            raw_yaw, raw_pitch, ear = result
            face_found = True

            yaw   = filter_yaw(raw_yaw)
            pitch = filter_pitch(raw_pitch)
            cursor_x, cursor_y = mouse.update(yaw, pitch)
            magnet_target = magnet.current_target() if magnet is not None else None

            # Blink → click
            if blinker.update(ear):
                mouse.click()
                flash_until = time.monotonic() + 0.4
        else:
            face_found = False

        blink_flash = time.monotonic() < flash_until

        # ── Display ───────────────────────────────────────────────────────────
        if show_debug:
            display = cv2.flip(frame, 1)
            display = _draw_overlay(display, yaw, pitch, ear,
                                    cursor_x, cursor_y,
                                    screen_w, screen_h,
                                    face_found, blink_flash,
                                    magnet_target)
            cv2.imshow("MouseTracker", display)

        # ── Keys ──────────────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break
        elif key == ord('r'):
            tracker.reset_neutral()
            filter_yaw.reset()
            filter_pitch.reset()
            print("Neutral recalibrated — hold still for a moment.")
        elif key == ord('s'):
            show_debug = not show_debug
            if not show_debug:
                cv2.destroyAllWindows()
            print(f"Debug window {'on' if show_debug else 'off'}.")

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if magnet is not None:
        magnet.stop()
    tracker.close()
    cap.release()
    cv2.destroyAllWindows()
    print("MouseTracker stopped.")


if __name__ == "__main__":
    main()
