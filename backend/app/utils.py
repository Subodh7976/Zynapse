from fastapi import UploadFile, status, HTTPException
from typing import Tuple
from uuid import UUID, uuid4
from pathlib import Path
import aiofiles
import re

from .core.constants import SourceTypeEnum, UPLOADS_DIR


async def parse_url_content(link: str, source_type: SourceTypeEnum) -> Tuple[str, str]:
    """
    Simulates fetching content and extracting a title from a URL.

    WARNING: Replace with actual web scraping (requests, BeautifulSoup)
             or YouTube API calls in a real application.
    """
    print(f"Simulating parsing for {source_type.value}: {link}")
    # Basic title derivation (replace with actual fetching/parsing)
    derived_title = ""
    parsed_content = ""
    try:
        # Very basic title extraction from URL path as a fallback
        match = re.search(r'/([^/]+)/?$', str(link))
        derived_title = match.group(1).replace(
            '-', ' ').replace('_', ' ') if match else f"{source_type.value} Source"

        if source_type == SourceTypeEnum.WEB:
            # Simulate fetching web page content
            # Real implementation: Use requests.get(link), then BeautifulSoup(response.text, 'html.parser')
            #                   Extract relevant text and potentially the <title> tag.
            parsed_content = f"Simulated web content from {link}. Title part: {derived_title}"
            # Real title extraction: soup.title.string if soup.title else derived_title
        elif source_type == SourceTypeEnum.YOUTUBE:
            # Simulate getting YouTube info (e.g., transcript)
            # Real implementation: Use YouTube Data API v3 or youtube-transcript-api library.
            parsed_content = f"Simulated YouTube transcript/info for {link}. Video ID might be extracted."
            # Extract video ID or use API to get actual title
            yt_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', str(link))
            if yt_match:
                derived_title = f"YouTube Video ({yt_match.group(1)})"

        print(
            f"Derived title: '{derived_title}', Parsed content (simulated): '{parsed_content[:50]}...'")
        return parsed_content, derived_title

    except Exception as e:
        print(f"Error during simulated URL parsing for {link}: {e}")
        return f"Error parsing {source_type.value} link: {link}", f"Error Source: {link}"


async def save_file_to_storage(file: UploadFile, conversation_id: UUID) -> str:
    """
    Saves the uploaded file locally under UPLOADS_DIR/<conversation_id>/<unique_filename>.
    Returns the filename part (relative path within the convo dir).
    """
    try:
        # Create conversation-specific directory
        convo_dir = UPLOADS_DIR / str(conversation_id)
        convo_dir.mkdir(parents=True, exist_ok=True)

        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid4()}{file_extension}"
        file_path = convo_dir / unique_filename

        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)

        # Return just the unique filename, the full path is implicitly known
        return unique_filename  # e.g., "some-uuid.pdf"

    except Exception as e:
        print(
            f"Error saving file {file.filename} for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {file.filename}. Error: {e}"
        )
    finally:
        await file.close()


async def parse_file_content(conversation_id: UUID, filename: str) -> str:
    """
    Simulates parsing text content from a temporary file.
    Needs conversation_id and filename to construct the full path.
    """
    full_path = UPLOADS_DIR / str(conversation_id) / filename
    print(f"Simulating parsing for: {full_path}")
    if not full_path.exists():
        # This shouldn't happen if save succeeded, but good check
        print(f"Warning: File {full_path} not found for parsing.")
        return f"Error: File {filename} not found."
    # Replace with actual parsing logic
    return f"Simulated parsed content for: {filename} in conversation {conversation_id}."
