"""Association d'un appel transcrit a un contact du CRM Notion existant.

Recherche le contact par nom (propriete "Nom", titre de la database). Cree le
contact si aucune correspondance, puis ajoute l'appel comme sous-page du
contact (resume / points cles / prochaines etapes).
"""

from notion_client import Client

import config

_client = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(auth=config.NOTION_API_KEY)
    return _client


def find_contact_page_id(name: str) -> str | None:
    client = get_client()
    response = client.data_sources.query(
        data_source_id=config.NOTION_CRM_DATA_SOURCE_ID,
        filter={"property": "Nom", "title": {"equals": name}},
    )
    results = response.get("results", [])
    return results[0]["id"] if results else None


def create_contact_page(name: str) -> str:
    client = get_client()
    page = client.pages.create(
        parent={"type": "data_source_id", "data_source_id": config.NOTION_CRM_DATA_SOURCE_ID},
        properties={"Nom": {"title": [{"text": {"content": name}}]}},
    )
    return page["id"]


def get_or_create_contact_page_id(name: str) -> str:
    page_id = find_contact_page_id(name)
    if page_id:
        return page_id
    return create_contact_page(name)


def _bulleted_list(items: list[str]) -> list[dict]:
    return [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": item}}]},
        }
        for item in items
    ]


def _heading(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


_NOTION_TEXT_LIMIT = 2000
_NOTION_CHILDREN_LIMIT = 100
# Garde-fou : au-delà de ça, la transcription est presque certainement une
# hallucination de faster-whisper (boucle de répétition), pas un vrai appel.
_MAX_TRANSCRIPT_CHARS = 50_000


def _chunk_text(text: str, size: int = _NOTION_TEXT_LIMIT) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def _batched(items: list, size: int = _NOTION_CHILDREN_LIMIT):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def create_call_page(
    contact_page_id: str,
    title: str,
    summary: str,
    key_points: list[str],
    next_steps: list[str],
    transcript: str,
) -> str:
    client = get_client()
    children = [
        _heading("Résumé"),
        _paragraph(summary),
        _heading("Points clés"),
        *_bulleted_list(key_points),
        _heading("Prochaines étapes"),
        *_bulleted_list(next_steps),
    ]
    page = client.pages.create(
        parent={"type": "page_id", "page_id": contact_page_id},
        properties={"title": [{"text": {"content": title}}]},
        icon={"type": "emoji", "emoji": "📞"},
        children=children,
    )
    page_id = page["id"]

    if len(transcript) > _MAX_TRANSCRIPT_CHARS:
        transcript = (
            transcript[:_MAX_TRANSCRIPT_CHARS]
            + "\n\n[Transcription tronquée : anormalement longue, probable erreur de transcription]"
        )

    toggle = client.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "toggle",
                "toggle": {"rich_text": [{"type": "text", "text": {"content": "Transcription complète"}}]},
            }
        ],
    )
    toggle_id = toggle["results"][0]["id"]

    transcript_blocks = [_paragraph(chunk) for chunk in _chunk_text(transcript)]
    for batch in _batched(transcript_blocks):
        client.blocks.children.append(block_id=toggle_id, children=batch)

    return page_id
