import os
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent


class VoiceConfig:

    # API keys — set as environment variables or paste here directly.
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")

    # Microphone / VAD
    SAMPLE_RATE          = 48_000   # Hz  (MacBook Air native rate)
    CHUNK_FRAMES         = 2_048
    VAD_RMS_THRESHOLD    = 0.015    # silence below this level
    VAD_SILENCE_DURATION = 1.5      # seconds of silence before stopping
    VAD_PRE_BUFFER_SECS  = 0.3      # seconds captured before speech starts
    MAX_RECORD_SECONDS   = 15

    # Gemini
    GEMINI_MODEL      = "gemini-2.5-flash-lite"
    MAX_HISTORY_TURNS = 12

    # Paths
    TRACKER_CONFIG_PATH = str(_HERE.parent / "Tracking" / "config.py")
