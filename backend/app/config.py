from enum import Enum
from pathlib import Path

from app.repository import RedisRepository

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOADS_DIR = Path("./uploaded_files_temp")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CONVERSATION_EXPIRY_MINUTES = 30

SUMMARIZER_MODEL = "gemini-2.0-flash"
CHAT_AGENT_MODEL = "gemini-2.0-flash"
MIND_MAP_MODEL = "gemini-2.0-flash"
FLOW_MODEL = "gemini-2.0-flash"

REDIS_HOST = "redis"
REDIS_PREFIX = "zynapse.service"
MERGE_TYPE = "message"


class SourceTypeEnum(Enum):
    DOCUMENT = "document"
    YOUTUBE = "youtube"
    WEB = "web"


redis_repo = RedisRepository(
    REDIS_PREFIX, REDIS_HOST,
    MERGE_TYPE
)