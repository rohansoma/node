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

    # ── Cursor Magnetism ──────────────────────────────────────────────────────
    # Smooth attraction toward nearby UI buttons (validated CHI 2005 model).
    # Requires Accessibility permission: System Settings → Privacy & Security.
    #
    # MAGNET_RADIUS        — pixel radius to acquire a lock on a button.
    # MAGNET_UNLOCK_RADIUS — pixel radius to release the lock (> RADIUS).
    #                        The gap between the two forms a hysteresis band
    #                        that prevents flickering between nearby buttons.
    # MAGNET_ALPHA_MAX     — max fraction of the gap closed per frame (0–1).
    # MAGNET_ALPHA_SMOOTH  — LPF coefficient on the alpha value (0–1).
    #                        Higher = slower but smoother attraction buildup.
    # MAGNET_SPEED_SCALE   — px/frame at which attraction is halved.
    # MAGNET_STICKY_DAMP   — extra centre-pull inside the target bounding box.
    # MAGNET_SCAN_INTERVAL — frames between Accessibility scans (10 ≈ 33 ms).
    MAGNET_ENABLED        = True
    MAGNET_RADIUS         = 130
    MAGNET_UNLOCK_RADIUS  = 185
    MAGNET_ALPHA_MAX      = 0.30
    MAGNET_ALPHA_SMOOTH   = 0.78
    MAGNET_SPEED_SCALE    = 7.0
    MAGNET_STICKY_DAMP    = 0.20
    MAGNET_SCAN_INTERVAL  = 10

    # ── Scroll mode ───────────────────────────────────────────────────────────
    # Activated by voice: "Hey Node scroll" / deactivated: "Hey Node unlock".
    # Head pitch maps to scroll speed; cursor movement is paused while active.
    # SCROLL_SPEED_SCALE — max scroll ticks per second (at full pitch deflection).
    SCROLL_SPEED_SCALE = 20.0

    # ── Display ───────────────────────────────────────────────────────────────
    SHOW_DEBUG = True
