"""
head_tracker.py
---------------
Estimates head yaw, pitch, and eye aspect ratio (EAR) from a camera frame
using the MediaPipe Tasks FaceLandmarker API (mediapipe >= 0.10.14).

The FaceLandmarker provides a 4×4 facial transformation matrix directly,
so solvePnP is no longer needed — we extract Euler angles straight from
the built-in rotation matrix.

Also provides OneEuroFilter used in main.py.
"""

from __future__ import annotations

import math
import os
import subprocess
import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


# ─────────────────────────────────────────────────────────────────────────────
# Model download helper
# ─────────────────────────────────────────────────────────────────────────────

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
_MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
)


def _ensure_model() -> str:
    if not os.path.exists(_MODEL_PATH):
        print("Downloading face landmarker model (~29 MB) — first-run only…")
        subprocess.run(
            ["curl", "-L", "--progress-bar", "-o", _MODEL_PATH, _MODEL_URL],
            check=True,
        )
        print("Download complete.")
    return _MODEL_PATH


# ─────────────────────────────────────────────────────────────────────────────
# One Euro Filter
# ─────────────────────────────────────────────────────────────────────────────

class OneEuroFilter:
    """
    Adaptive low-pass filter — quiet at rest, fast to react when moving.
    Reference: Casiez et al., CHI 2012.
    """

    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.007,
                 d_cutoff: float = 1.0) -> None:
        self.min_cutoff = min_cutoff
        self.beta       = beta
        self.d_cutoff   = d_cutoff
        self._x:  float | None = None
        self._dx: float        = 0.0
        self._t:  float | None = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x: float) -> float:
        now = time.monotonic()
        if self._x is None:
            self._x, self._t = x, now
            return x

        dt = now - self._t
        if dt < 1e-8:
            return self._x

        dx     = (x - self._x) / dt
        a_d    = self._alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1.0 - a_d) * self._dx

        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a      = self._alpha(cutoff, dt)
        x_hat  = a * x + (1.0 - a) * self._x

        self._x, self._dx, self._t = x_hat, dx_hat, now
        return x_hat

    def reset(self) -> None:
        self._x = self._t = None
        self._dx = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Head Tracker
# ─────────────────────────────────────────────────────────────────────────────

class HeadTracker:
    """
    Estimates head yaw, pitch, and eye aspect ratio (EAR) using MediaPipe
    Tasks FaceLandmarker.

    process() returns (yaw_offset, pitch_offset, ear):
        yaw_offset   > 0  →  head turned to subject's RIGHT
        pitch_offset > 0  →  head tilted UP
        ear               →  ~0.25 open, drops toward 0 on a blink
    """

    # Eye Aspect Ratio landmark indices (Soukupova & Cech, 2016)
    # Each eye: (outer, upper1, upper2, inner, lower1, lower2)
    _RIGHT_EYE = (33,  160, 158, 133, 153, 144)
    _LEFT_EYE  = (263, 387, 385, 362, 380, 373)

    def __init__(self, frame_w: int, frame_h: int) -> None:
        self._fw = frame_w
        self._fh = frame_h
        model_path = _ensure_model()

        base_opts = mp_python.BaseOptions(model_asset_path=model_path)
        opts = mp_vision.FaceLandmarkerOptions(
            base_options=base_opts,
            running_mode=mp_vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_facial_transformation_matrixes=True,
        )
        self._detector = mp_vision.FaceLandmarker.create_from_options(opts)

        self._neutral_yaw:   float | None = None
        self._neutral_pitch: float | None = None

    # ──────────────────────────────────────────────────────────────────────────

    def process(self, frame: np.ndarray):
        """
        Process one BGR camera frame (unflipped).

        Returns (yaw_offset, pitch_offset, landmarks) or None if no face found.
        """
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._detector.detect(mp_img)

        if not result.face_landmarks or not result.facial_transformation_matrixes:
            return None

        lms   = result.face_landmarks[0]
        xform = np.array(result.facial_transformation_matrixes[0]).reshape(4, 4)

        # Extract rotation sub-matrix and decompose to Euler angles (degrees)
        rmat          = xform[:3, :3]
        angles, *_    = cv2.RQDecomp3x3(rmat)
        raw_pitch     = angles[0]   # X-axis: + = head down
        raw_yaw       = angles[1]   # Y-axis: + = head right

        # Invert pitch so + means head UP
        corrected_pitch = -raw_pitch

        # Capture neutral on first detection
        if self._neutral_yaw is None:
            self._neutral_yaw   = raw_yaw
            self._neutral_pitch = corrected_pitch

        return (
            raw_yaw         - self._neutral_yaw,
            corrected_pitch - self._neutral_pitch,
            self._ear(lms),
        )

    def _ear(self, lms) -> float:
        """Average Eye Aspect Ratio of both eyes, in pixel coordinates."""
        def eye_ear(p1, p2, p3, p4, p5, p6):
            def px(i):
                return np.array([lms[i].x * self._fw, lms[i].y * self._fh])
            v1 = np.linalg.norm(px(p2) - px(p6))
            v2 = np.linalg.norm(px(p3) - px(p5))
            h  = np.linalg.norm(px(p1) - px(p4))
            return (v1 + v2) / (2.0 * h + 1e-6)

        return (eye_ear(*self._RIGHT_EYE) + eye_ear(*self._LEFT_EYE)) / 2.0

    def reset_neutral(self) -> None:
        """Re-capture neutral position on the next detected frame."""
        self._neutral_yaw   = None
        self._neutral_pitch = None

    def close(self) -> None:
        self._detector.close()
