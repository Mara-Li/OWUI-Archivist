import os

MEMORY_DIR = "/app/memories"
ARCHIVE_DIR = os.path.join(MEMORY_DIR, "archived")
LOG_DIR = os.path.join(MEMORY_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "archivist.log")
COLLECTIONS_FILE = "/app/model_collections.json"
DEFAULT_KNOWLEDGE_ID = "64eda376-4f8d-43df-9585-2e0f93d5ebde"
WEBUI_API = os.getenv("WEBUI_API", "http://aria-open-webui:3000")
TOKEN = os.getenv("WEBUI_TOKEN")
FILENAME_TEMPLATE = os.getenv("FILENAME_TEMPLATE", "conversation_{datetime}.txt")
TIMELOOP = int(os.getenv("TIMELOOP", 10))
MAX_RETRY = int(os.getenv("ARCHIVIST_MAX_RETRY", 2))

HEADERS: dict[str, str] = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

LAST_ARCHIVED = os.path.join(MEMORY_DIR, "ongoing_conversation_id.txt")

os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

HISTORY_LOG = os.path.join(LOG_DIR, "archivist_history.log")
