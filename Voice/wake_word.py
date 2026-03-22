"""
Voice/wake_word.py — Wake phrase detection via word matching.

Strips all punctuation from the transcript first, then checks whether the
first two words are "hey" and "node" (including common misrecognitions).

This handles everything ElevenLabs realistically produces for "Hey Node":
    "Hey Node ..."        → matched
    "Hey, Node, ..."      → matched  (comma stripped)
    "Hey Nod ..."         → matched  (short form)
    "Hey Note ..."        → matched  (common mishearing)
    "Hay Node ..."        → matched  (accent variant)
    "random sentence"     → None
"""

import re

_HEY_WORDS  = {"hey", "hay", "he", "hei", "hi"}
_NODE_WORDS = {"node", "nod", "nods", "note", "noted", "notes", "nodes"}


def extract_command(transcript: str) -> str | None:
    """
    Returns the command text after the wake phrase, or None if not detected.
    Returns an empty string if the user said just "Hey Node" with nothing after.
    """
    # Strip punctuation only for the wake-word check, keep original for command
    clean = re.sub(r"[^\w\s]", " ", transcript)
    words = clean.split()

    if len(words) < 2:
        return None

    # Scan for "hey node" anywhere in the utterance (handles pre-speech before the wake phrase)
    for i in range(len(words) - 1):
        if words[i].lower() in _HEY_WORDS and words[i + 1].lower() in _NODE_WORDS:
            # Find where the word after "node" starts in the ORIGINAL transcript
            # This preserves dots, commas etc. in the command (e.g. "google.com")
            original_words = transcript.split()
            return " ".join(original_words[i + 2:]).strip()

    return None
