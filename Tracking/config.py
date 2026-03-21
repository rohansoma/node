class Config:
    # ── Camera ───────────────────────────────────────────────────────────────
    CAMERA_INDEX = 0
    FRAME_WIDTH  = 640
    FRAME_HEIGHT = 480

    # ── Head angle range ─────────────────────────────────────────────────────
    # Degrees of head rotation that maps to the full screen edge.
    # Smaller = more sensitive (less head movement needed).
    MAX_YAW   = 18.0   # left/right
    MAX_PITCH = 12.0   # up/down

    # ── Dead zone ────────────────────────────────────────────────────────────
    # Degrees of head movement to ignore around neutral.
    # Prevents cursor drift while holding your head still.
    DEAD_ZONE_YAW   = 2.0
    DEAD_ZONE_PITCH = 2.0

    # ── Speed curve ──────────────────────────────────────────────────────────
    # Exponent applied to the normalised head angle before mapping to screen.
    #   1.0 = linear (uniform speed everywhere)
    #   1.5 = mild curve — slower near centre (precision), faster at edges
    #   2.0 = strong curve
    SPEED_EXPONENT = 1

    # ── One Euro Filter ──────────────────────────────────────────────────────
    # Applied to raw head-pose angles before mapping.
    # Lower  MIN_CUTOFF → smoother / less jitter at rest (but slightly more lag).
    # Higher BETA       → more responsive during fast head movement.
    FILTER_MIN_CUTOFF = 0.3
    FILTER_BETA       = 0.005

    # ── Direction ────────────────────────────────────────────────────────────
    # Flip these if the cursor goes the wrong way.
    # INVERT_YAW = True is correct for a standard front-facing camera
    # (when you face the camera, turning your head right should move the cursor right).
    INVERT_YAW   = True
    INVERT_PITCH = False

    # ── Blink detection ───────────────────────────────────────────────────────
    # Double-blink triggers a left click.  Single blinks are ignored.
    # EAR (Eye Aspect Ratio) is ~0.25 when open, drops toward 0 on a blink.
    BLINK_EAR_THRESHOLD  = 0.20  # EAR below this counts as "eye closed"
    BLINK_MIN_FRAMES     = 2     # eye must stay closed this many frames to register
    DOUBLE_BLINK_WINDOW  = 0.6   # max seconds between two blinks for a double-click

    # ── Display ───────────────────────────────────────────────────────────────
    SHOW_DEBUG = True
