from enum import Enum
from pathlib import Path


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOADS_DIR = Path("./uploaded_files_temp")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CONVERSATION_EXPIRY_MINUTES = 30


class SourceTypeEnum(Enum):
    DOCUMENT = "document"
    YOUTUBE = "youtube"
    WEB = "web"
