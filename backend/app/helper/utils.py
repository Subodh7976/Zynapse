
from app.core.db import get_all_source


def build_sources_description(conversation_id: str) -> str:
    """
    builds a description (for LLMs) describing the sources available with brief description

    Args:
        conversation_id (str): conversation id for retrieving the sources

    Returns:
        str: combined sources in markdown format
    """
    sources = get_all_source(conversation_id)

    sources_description = "**Sources available:**"
    sources_description += "| Source ID | Source Title | Source Description |\n| --- | --- | --- |\n"

    for source in sources:
        source_id = str(source.id)
        source_title = source.title
        source_description = source.brief

        sources_description += f"| {source_id} | {source_title} | {source_description} |\n"

    return sources_description
