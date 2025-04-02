from datetime import datetime
import json
from pathlib import Path
from typing import Optional
from webui_api import add_to_knowledge, get_chat_info, upload_file
from config import ARCHIVE_CACHE_FILE, DEFAULT_KNOWLEDGE_ID, FILENAME_TEMPLATE, MEMORY_DIR
from file_utils import (
    ModelCollection,
    generate_filename,
    get_archive_path,
    load_model_collections,
)
from logger import log
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

model_collections = load_model_collections()

log(
    f"[Notify] Loading model collections...{json.dumps(model_collections)}",
)


class NotifyRequest(BaseModel):
    chat_id: str
    user_id: str
    username: Optional[str] = "User"
    model: str


class NotifyResponse(BaseModel):
    status: str
    detail: Optional[dict[str, str]] = None


def load_archived_ids():
    try:
        if ARCHIVE_CACHE_FILE.exists():
            return json.loads(ARCHIVE_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Failed to load archived_ids cache: {e}")
    return {}


def save_archived_ids(cache):
    try:
        ARCHIVE_CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    except Exception as e:
        log(f"Failed to save archived_ids cache: {e}")


archived_ids = load_archived_ids()


@app.post("/notify", response_model=NotifyResponse)
async def notify_conversation(data: NotifyRequest):
    """
    Notify Archivist of a new conversation to archive.

    Example:
    ```json
    {
      "chat_id": "89ecea6c-accc-4979-ac62-4c42a280073a",
      "user_id": "12345",
      "username": "Lili",
      "model": "llama3.1:latest",
    }
    ```
    """
    chat_id = data.chat_id
    extention = Path(FILENAME_TEMPLATE).suffix[1:]
    user_id = data.user_id
    username = data.username or "User"
    model = data.model
    filepath = Path(MEMORY_DIR) / f"{chat_id}.{extention}"
    if not filepath.exists():
        log(f"[Notify] No memory file found for {chat_id} at {filepath}")
        return NotifyResponse(status="no file", detail={"chat_id": chat_id})
    log(f"[Notify] Processing archive for {chat_id}")
    try:
        chat_info = get_chat_info(chat_id)
        if not chat_info:
            log(f"[Notify] Failed to get chat info for {chat_id}")
            return NotifyResponse(status="no title", detail={"chat_id": chat_id})
        title = chat_info.get("title")
        if not title:
            log(f"[Notify] No title found for {chat_id}")
            return NotifyResponse(status="no title", detail={"chat_id": chat_id})
        collection_id = model_collections.get(model) or model_collections.get("default")
        if collection_id and collection_id.id == "0":
            log(f"[Notify] Excluded model {model}.")
            return NotifyResponse(status="excluded", detail={"chat_id": chat_id})
        elif not collection_id:
            collection_id = ModelCollection(id=DEFAULT_KNOWLEDGE_ID, name="default")
            log(f"[Notify] Model collection not found for {model}. Using default.")
        file_name = generate_filename(FILENAME_TEMPLATE, model, username, chat_id)
        file_id = upload_file(filepath, file_name)
        if not file_id:
            log("[Notify] Upload failed or no file ID returned")
            return NotifyResponse(status="upload failed", detail={"chat_id": chat_id})

        success = add_to_knowledge(file_id, collection_id.id, file_name, filepath)
        if success:
            log(f"[Notify] Added {chat_id} to knowledge {collection_id.name}")
            archived_ids[chat_id] = collection_id.id
            save_archived_ids(archived_ids)
            archived_path = get_archive_path(filepath.name, collection_id.name)
            filepath.rename(archived_path)
            log(f"[Notify] Moved {filepath} to {archived_path}")
            archived_ids[chat_id] = {
                "user_id": user_id,
                "username": username,
                "model": model,
                "archived_at": datetime.now().isoformat(),
            }
            save_archived_ids(archived_ids)
            return NotifyResponse(
                status="archived",
                detail={"chat_id": chat_id, "user_id": user_id, "username": username, "model": model, "title": title},
            )
        else:
            log(f"[Notify] Failed to add {file_name} to knowledge")
            return NotifyResponse(status="failed to add", detail={"chat_id": chat_id})
    except Exception as e:
        log(f"[Notify] Error processing archive: {e}")
        return NotifyResponse(status="error", detail={"chat_id": chat_id, "error": str(e)})
