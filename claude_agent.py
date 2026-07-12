"""Resume structure d'une transcription d'appel via l'API Claude (Anthropic).

Utilise le tool use pour forcer une sortie structuree (resume, points cles,
prochaines etapes) plutot que de parser du texte libre.
"""

from dataclasses import dataclass

import anthropic

import config

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
        max_tokens=1024,
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
            return CallSummary(
                summary=data["summary"],
                key_points=data["key_points"][:_MAX_ITEMS],
                next_steps=data["next_steps"][:_MAX_ITEMS],
            )

    raise RuntimeError("Claude n'a pas retourné de résumé structuré (log_call_summary)")
