"""Resume structure d'une transcription d'appel via l'API Claude (Anthropic).

Utilise le tool use pour forcer une sortie structuree (resume, points cles,
prochaines etapes) plutot que de parser du texte libre.
"""

import json
import logging
from dataclasses import dataclass

import anthropic

import config

logger = logging.getLogger(__name__)

_client = None

_TOOL = {
    "name": "log_call_summary",
    "description": "Enregistre le resume structure d'un appel telephonique transcrit.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Resume synthetique de l'appel en 2-4 phrases, en francais.",
            },
            "key_points": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 8,
                "description": "Points cles structurants abordes pendant l'appel, sous forme de puces courtes. Maximum 8, moins si l'appel est court.",
            },
            "next_steps": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 8,
                "description": "Actions concretes a suivre apres cet appel, sous forme de puces courtes. Maximum 8, moins si l'appel est court.",
            },
        },
        "required": ["summary", "key_points", "next_steps"],
    },
}


@dataclass
class CallSummary:
    summary: str
    key_points: list[str]
    next_steps: list[str]


_MAX_INPUT_TRANSCRIPT_CHARS = 20_000
_MAX_ITEMS = 8


def _ensure_list(value) -> list[str]:
    """Claude renvoie parfois un tableau sous forme de chaîne JSON au lieu
    d'un vrai tableau ; on le reparse plutôt que de l'itérer caractère par
    caractère."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return [value] if value.strip() else []
    return []


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def summarize_call(transcript: str, contact_name: str) -> CallSummary:
    if len(transcript) > _MAX_INPUT_TRANSCRIPT_CHARS:
        transcript = transcript[:_MAX_INPUT_TRANSCRIPT_CHARS] + "\n\n[transcription tronquée]"

    client = get_client()
    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "log_call_summary"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Voici la transcription brute d'un appel avec {contact_name}. "
                    "Structure-la en resume, points cles et prochaines etapes, "
                    "de facon concise et actionnable. Maximum 8 points cles et "
                    "8 prochaines etapes, moins si l'appel est court ou repetitif.\n\n"
                    f"Transcription :\n{transcript}"
                ),
            }
        ],
    )

    for block in message.content:
        if block.type == "tool_use" and block.name == "log_call_summary":
            data = block.input
            if message.stop_reason == "max_tokens":
                logger.warning("Réponse Claude tronquée (max_tokens atteint) pour l'appel avec %s", contact_name)
            return CallSummary(
                summary=data.get("summary", "(résumé indisponible, réponse tronquée)"),
                key_points=_ensure_list(data.get("key_points", []))[:_MAX_ITEMS],
                next_steps=_ensure_list(data.get("next_steps", []))[:_MAX_ITEMS],
            )

    raise RuntimeError("Claude n'a pas retourné de résumé structuré (log_call_summary)")
