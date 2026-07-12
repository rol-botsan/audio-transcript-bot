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
                "description": "Points cles structurants abordes pendant l'appel, sous forme de puces courtes.",
            },
            "next_steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Actions concretes a suivre apres cet appel, sous forme de puces courtes.",
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


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def summarize_call(transcript: str, contact_name: str) -> CallSummary:
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
                    "de facon concise et actionnable.\n\n"
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
                key_points=data["key_points"],
                next_steps=data["next_steps"],
            )

    raise RuntimeError("Claude n'a pas retourné de résumé structuré (log_call_summary)")
