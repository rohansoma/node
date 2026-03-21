import requests

def transcribe(wav_bytes: bytes, api_key: str) -> str:
    resp = requests.post(
        "https://api.elevenlabs.io/v1/speech-to-text",
        headers={"xi-api-key": api_key},
        files={"file": ("audio.wav", wav_bytes, "audio/wav"),
               "model_id": (None, "scribe_v2")},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("text", "").strip()
