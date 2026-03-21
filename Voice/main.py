"""
Voice/main.py — Voice command loop for MouseTracker.

Wake phrase: "Hey Node <command>"
────────────────────────────────
Say "Hey Node" followed immediately by your command in the same breath.
The microphone only triggers on speech (VAD), so background noise / TV /
casual conversation is ignored.  Every captured utterance is transcribed
by ElevenLabs; if it starts with "Hey Node" the rest is sent to Gemini as
a command.  If it doesn't start with "Hey Node" it is silently discarded.

Run standalone:
    python -m Voice.main

Or start automatically with the head tracker:
    python Tracking/main.py   ← voice runs as a background thread

Required environment variables (or paste keys into Voice/config.py):
    export ELEVENLABS_API_KEY="..."
    export GEMINI_API_KEY="..."

Example commands:
    "Hey Node open YouTube"
    "Hey Node search for mechanical keyboards"
    "Hey Node open Spotify"
    "Hey Node switch Chrome to the tab with Google Docs"
    "Hey Node do it again"
    "Hey Node set MAX_YAW to 20"
    "Hey Node what are the current tracker settings?"
"""

from __future__ import annotations

import os
import pathlib
import sys
import threading
import time

# Load .env from project root if present
_env = pathlib.Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

from .config    import VoiceConfig
from .listener  import record_command
from .stt       import transcribe
from .agent     import VoiceAgent
from .wake_word import extract_command


# ── Voice loop ────────────────────────────────────────────────────────────────

def _voice_loop(cfg: VoiceConfig, agent: VoiceAgent) -> None:
    """
    The core voice loop.  Runs forever as a daemon thread (or as the main
    thread in standalone mode).

    Cycle:
      1. VAD waits for speech → records until silence.
      2. ElevenLabs transcribes the audio.
      3. If transcript starts with "Hey Node" → extract command → Gemini.
      4. Otherwise → silent discard.
    """
    print("[voice] ready — say 'Hey Node <command>'")

    while True:
        try:
            # ── 1. Record ─────────────────────────────────────────────────────
            wav = record_command(cfg)
            if wav is None:
                continue

            # ── 2. Transcribe ─────────────────────────────────────────────────
            try:
                transcript = transcribe(wav, cfg.ELEVENLABS_API_KEY)
            except RuntimeError as exc:
                print(f"[voice] STT error: {exc}")
                continue

            if not transcript:
                continue

            # ── 3. Wake phrase check ──────────────────────────────────────────
            command = extract_command(transcript)

            if command is None:
                continue   # casual speech — silently discard

            if not command:
                # Said just "Hey Node" — record the follow-up
                wav2 = record_command(cfg)
                if not wav2:
                    continue
                try:
                    command = transcribe(wav2, cfg.ELEVENLABS_API_KEY).strip()
                except RuntimeError:
                    continue
                if not command:
                    continue

            # ── 4. Process with Gemini ────────────────────────────────────────
            print(f"\n◉  {command}")
            try:
                reply = agent.process(command)
            except Exception as exc:
                print(f"   [error] {exc}")
                continue

            print(f"   {reply}\n")

        except Exception as exc:
            print(f"[voice] error: {exc}")
            time.sleep(1)


# ── Background thread entry point ─────────────────────────────────────────────

def start_background_thread(cfg: VoiceConfig | None = None) -> threading.Thread | None:
    """
    Start the voice command loop as a background daemon thread.

    Called by Tracking/main.py so voice runs automatically alongside the
    head tracker without any extra terminal window.

    Returns the running Thread, or None if voice cannot be started (missing
    API keys, etc.) — the tracker continues normally either way.
    """
    if cfg is None:
        cfg = VoiceConfig()

    missing = [k for k, v in [
        ("ELEVENLABS_API_KEY", cfg.ELEVENLABS_API_KEY),
        ("GEMINI_API_KEY",     cfg.GEMINI_API_KEY),
    ] if not v]

    if missing:
        print(f"[Voice] Disabled — missing key(s): {', '.join(missing)}")
        print(f"[Voice] Set them as env vars or edit Voice/config.py")
        return None

    try:
        agent = VoiceAgent(cfg)
    except RuntimeError as exc:
        print(f"[Voice] Could not initialise agent: {exc}")
        return None

    thread = threading.Thread(
        target=_voice_loop,
        args=(cfg, agent),
        daemon=True,       # dies automatically when the main process exits
        name="voice-commands",
    )
    thread.start()
    return thread


# ── Standalone entry point ────────────────────────────────────────────────────

def main() -> None:
    cfg = VoiceConfig()

    missing = [k for k, v in [
        ("ELEVENLABS_API_KEY", cfg.ELEVENLABS_API_KEY),
        ("GEMINI_API_KEY",     cfg.GEMINI_API_KEY),
    ] if not v]

    if missing:
        print(f"[Error] Missing API key(s): {', '.join(missing)}")
        print("  Set them as environment variables or edit Voice/config.py")
        sys.exit(1)

    print()
    print("MouseTracker — Voice Commands (standalone)")
    print("══════════════════════════════════════════")

    try:
        agent = VoiceAgent(cfg)
    except RuntimeError as exc:
        print(f"[Error] {exc}")
        sys.exit(1)

    try:
        _voice_loop(cfg, agent)
    except KeyboardInterrupt:
        print("\n[Voice] Stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
