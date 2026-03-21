"""Records audio via VAD and returns WAV bytes."""
from __future__ import annotations

import io
import wave
from collections import deque

import numpy as np
import sounddevice as sd


def record_command(cfg) -> bytes | None:
    """Block until speech is detected, record until silence, return WAV bytes."""
    sr             = cfg.SAMPLE_RATE
    chunk          = cfg.CHUNK_FRAMES
    silence_chunks = int(cfg.VAD_SILENCE_DURATION * sr / chunk)
    max_chunks     = int(cfg.MAX_RECORD_SECONDS   * sr / chunk)
    pre_buf        = deque(maxlen=max(1, int(cfg.VAD_PRE_BUFFER_SECS * sr / chunk)))

    captured, in_speech, silence_cnt = [], False, 0

    print("  listening…", end="", flush=True)

    with sd.InputStream(samplerate=sr, channels=1, dtype="float32",
                        blocksize=chunk) as stream:
        while len(captured) < max_chunks:
            data, _ = stream.read(chunk)
            rms = float(np.sqrt(np.mean(data ** 2)))

            if not in_speech:
                pre_buf.append(data.copy())
                if rms >= cfg.VAD_RMS_THRESHOLD:
                    in_speech = True
                    captured.extend(pre_buf)
                    print(" recording…", end="", flush=True)
            else:
                captured.append(data.copy())
                silence_cnt = silence_cnt + 1 if rms < cfg.VAD_RMS_THRESHOLD else 0
                if silence_cnt >= silence_chunks:
                    break

    if not captured:
        print()
        return None

    print(" done.", flush=True)

    audio = np.concatenate(captured)
    i16   = (np.clip(audio, -1.0, 1.0) * 32_767).astype(np.int16)
    buf   = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(i16.tobytes())
    return buf.getvalue()
