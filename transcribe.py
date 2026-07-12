"""Transcription audio -> texte, 100% locale et gratuite via faster-whisper (CPU).

Meme approche que Gmail-Agent/voice.py.
"""

from pathlib import Path

from faster_whisper import WhisperModel

import config

_whisper_model = None


def get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(config.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _whisper_model


def transcribe_audio(audio_path: Path) -> str:
    model = get_whisper_model()
    segments, _info = model.transcribe(str(audio_path), language="fr")
    return " ".join(seg.text.strip() for seg in segments).strip()
