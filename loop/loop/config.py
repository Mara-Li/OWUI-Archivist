from pathlib import Path
import os

# - Environment variables
DEFAULT_KNOWLEDGE_ID = os.getenv("DEFAULT_KNOWLEDGE_ID")
WEBUI_API = os.getenv("WEBUI_API", "http://open-webui:8080")
TOKEN = os.getenv("WEBUI_TOKEN")
FILENAME_TEMPLATE = os.getenv("FILENAME_TEMPLATE", "conversation_{datetime}.txt")
TIMELOOP = int(os.getenv("TIMELOOP", 10))
ARCHIVE_PER_KNOWLEDGE = os.getenv("ARCHIVE_PER_KNOWLEDGE", "false").lower() == "true"

# -- Dirs
MEMORY_DIR = Path(os.getenv("MEMORY_DIR", "/app/memory"))
COLLECTIONS_FILE = Path(os.getenv("COLLECTIONS_FILE", "/app/model_collections.json"))
USERS_API = Path(os.getenv("USERS_API", "/app/user_api.json"))

# --- Path
ONGOING_ID = Path(MEMORY_DIR, "ongoing_conversation_id.txt")
ONGOING_DIR = Path(MEMORY_DIR, "ongoing_conversations")
ARCHIVE_DIR = Path(MEMORY_DIR, "archived")
LOG_DIR = Path(MEMORY_DIR, "logs")
LOG_FILE = Path(LOG_DIR, "archivist.log")
HISTORY_LOG = Path(LOG_DIR, "archivist_history.log")

# ---- Create dirs
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# - Headers
HEADERS: dict[str, str] = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
