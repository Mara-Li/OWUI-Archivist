import os

# - Environment variables
DEFAULT_KNOWLEDGE_ID = os.getenv("DEFAULT_KNOWLEDGE_ID")
WEBUI_API = os.getenv("WEBUI_API", "http://open-webui:8080")
TOKEN = os.getenv("WEBUI_TOKEN")
FILENAME_TEMPLATE = os.getenv("FILENAME_TEMPLATE", "conversation_{datetime}.txt")
TIMELOOP = int(os.getenv("TIMELOOP", 10))
ARCHIVE_PER_KNOWLEDGE = os.getenv("ARCHIVE_PER_KNOWLEDGE", "false").lower() == "true"

# -- Dirs
MEMORY_DIR = os.getenv("MEMORY_DIR", "/app/memory")
COLLECTIONS_FILE = os.getenv("COLLECTIONS_FILE", "/app/model_collections.json")
USERS_API = os.getenv("USERS_API", "/app/user_api.json")

# --- Path
ONGOING_ID = os.path.join(MEMORY_DIR, "ongoing_conversation_id.txt")
ONGOING_DIR = os.path.join(MEMORY_DIR, "ongoing_conversations")
ARCHIVE_DIR = os.path.join(MEMORY_DIR, "archived")
LOG_DIR = os.path.join(MEMORY_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "archivist.log")
HISTORY_LOG = os.path.join(LOG_DIR, "archivist_history.log")

# ---- Create dirs
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# - Headers
HEADERS: dict[str, str] = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
