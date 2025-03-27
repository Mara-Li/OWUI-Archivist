from file_utils import get_uid, load_user_api, read_file_content
from logger import log, log_history
import requests

from config import HEADERS, WEBUI_API


def is_webui_reachable():
    try:
        res = requests.get(f"{WEBUI_API}/api/v1/health", timeout=5)
        return res.status_code == 200
    except Exception as e:
        log(f"[Delete archive] 🚫 WebUI not reachable: {e}")
        return False


def get_chat_info(chat_id: str):
    # 1. Essaie avec la clé par défaut
    try:
        res = requests.get(f"{WEBUI_API}/api/v1/chats/{chat_id}", headers=HEADERS)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        log(f"Error fetching chat with default key: {e}")

    # 2. Fallback avec les autres clés utilisateur
    all_user_tokens = load_user_api()
    print(all_user_tokens)
    for token in all_user_tokens:
        try:
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            res = requests.get(f"{WEBUI_API}/api/v1/chats/{chat_id}", headers=headers)
            if res.status_code == 200:
                log(f"✅ Chat {chat_id} found using fallback API key")
                return res.json()
        except Exception as e:
            log(f"Error fetching chat {chat_id} with fallback key: {e}")

    log(f"❌ Chat {chat_id} not found with any available key")
    return None


def get_existing_file(knowledge_id, filename):
    try:
        res = requests.get(f"{WEBUI_API}/api/v1/knowledge/{knowledge_id}", headers=HEADERS)
        if res.status_code == 200:
            files = res.json().get("files", [])
            for f in files:
                if f.get("filename") == get_uid(filename):
                    return f
        else:
            log(f"Failed to fetch knowledge details: {res.status_code}")
    except Exception as e:
        log(f"Error checking existing file: {e}")
    return None


def update_file_content(file_id, content):
    try:
        res = requests.post(
            f"{WEBUI_API}/api/v1/files/{file_id}/data/content/update",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"content": content},
        )
        if res.status_code != 200:
            log(f"Failed to update file content: {res.status_code} - {res.text}")
        return res.status_code == 200
    except Exception as e:
        log(f"Error updating file content: {e}")
    return False


def update_file_in_knowledge(knowledge_id, file_id):
    try:
        res = requests.post(
            f"{WEBUI_API}/api/v1/knowledge/{knowledge_id}/file/update",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"file_id": file_id},
        )
        if res.status_code != 200:
            log(f"Failed to reindex file {file_id}: {res.status_code} - {res.text}")
        return res.status_code == 200
    except Exception as e:
        log(f"Error reindexing file in knowledge: {e}")
    return False


def delete_file(file_id):
    try:
        res = requests.delete(f"{WEBUI_API}/api/v1/files/{file_id}", headers=HEADERS)
        if res.status_code != 200:
            log(f"Failed to delete file {file_id}: {res.status_code} - {res.text}")
        return res.status_code == 200
    except Exception as e:
        log(f"Error deleting file: {e}")
    return False


def add_to_knowledge(file_id, knowledge_id, filename, source_path):
    existing_file = get_existing_file(knowledge_id, filename)
    if existing_file:
        log(f"File already in knowledge, updating content: {filename}")
        existing_file_id = existing_file.get("id")
        if existing_file_id:
            content = read_file_content(source_path)
            if update_file_content(existing_file_id, content):
                if update_file_in_knowledge(knowledge_id, existing_file_id):
                    log_history("updated", filename, knowledge_id)
                    return True
                else:
                    log(f"⚠️ Failed to reindex file {filename} in knowledge {knowledge_id}")
                    if not remove_from_knowledge({"file_id": file_id}, knowledge_id, filename):
                        return False
            else:
                log(f"⚠️ Failed to update content for file {filename}")
        else:
            log(f"⚠️ No file ID found for existing file: {filename} in knowledge {knowledge_id}")

    # fallback to upload + add
    data = {"file_id": file_id}
    res = requests.post(
        f"{WEBUI_API}/api/v1/knowledge/{knowledge_id}/file/add",
        headers={**HEADERS, "Content-Type": "application/json"},
        json=data,
    )
    if res.status_code != 200:
        log(f"Add failed: {res.status_code} - {res.text}")
    else:
        log_history("added", filename, knowledge_id)
    return res.status_code == 200


def remove_from_knowledge(data, knowledge_id, filename):
    res = requests.post(
        f"{WEBUI_API}/api/v1/knowledge/{knowledge_id}/file/remove",
        headers={**HEADERS, "Content-Type": "application/json"},
        json=data,
    )
    if res.status_code != 200:
        log(f"Remove failed: {res.status_code} - {res.text}")
    else:
        log_history("removed", filename, knowledge_id)
    return res.status_code == 200


def upload_file(file_path: str, model: str, user: str, filename: str):
    with open(file_path, "rb") as f:
        files = {"file": (filename, f, "text/plain; charset=utf-8")}
        res = requests.post(f"{WEBUI_API}/api/v1/files/", headers=HEADERS, files=files)
    if res.status_code == 200:
        try:
            return res.json().get("id")
        except Exception as e:
            log(f"JSON decode error: {e}")
    else:
        log(f"Upload failed: {res.status_code} - {res.text}")
    return None
