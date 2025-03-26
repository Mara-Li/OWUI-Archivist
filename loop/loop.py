# archivist_loop.py
import os
import time
import requests
import shutil
import json
from datetime import datetime
print("[Archivist] Booting script...")

MEMORY_DIR = "/app/memories"
ARCHIVE_DIR = os.path.join(MEMORY_DIR, "archived")
LOG_DIR = os.path.join(MEMORY_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "archivist.log")
COLLECTIONS_FILE = "/app/model_collections.json"
DEFAULT_KNOWLEDGE_ID = "64eda376-4f8d-43df-9585-2e0f93d5ebde"
WEBUI_API = os.getenv("WEBUI_API", "http://aria-open-webui:3000")
TOKEN = os.getenv("WEBUI_TOKEN")

if not TOKEN:
    print("[Archivist] ❌ WEBUI_TOKEN is missing. Exiting.")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

HISTORY_LOG = os.path.join(LOG_DIR, "archivist_history.log")

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")

def log_history(action, filename, knowledge_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {action.upper()} → {filename} in knowledge {knowledge_id}"
    with open(HISTORY_LOG, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")

def load_model_collections():
    try:
        with open(COLLECTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"Failed to load model collections: {e}")
        return {}

def upload_file(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'text/plain; charset=utf-8')}
        res = requests.post(f"{WEBUI_API}/api/v1/files/", headers=HEADERS, files=files)
    if res.status_code == 200:
        try:
            return res.json().get("id")
        except Exception as e:
            log(f"JSON decode error: {e}")
    else:
        log(f"Upload failed: {res.status_code} - {res.text}")
    return None

def get_existing_file(knowledge_id, filename):
    try:
        res = requests.get(f"{WEBUI_API}/api/v1/knowledge/{knowledge_id}", headers=HEADERS)
        if res.status_code == 200:
            files = res.json().get("files", [])
            for f in files:
                if f.get("filename") == filename:
                    return f
        else:
            log(f"Failed to fetch knowledge details: {res.status_code}")
    except Exception as e:
        log(f"Error checking existing file: {e}")
    return None

def read_file_content(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        log(f"Error reading file content: {e}")
    return ""

def update_file_content(file_id, content):
    try:
        res = requests.post(
            f"{WEBUI_API}/api/v1/files/{file_id}/data/content/update",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"content": content}
        )
        if res.status_code != 200:
            log(f"Failed to update file content: {res.status_code} - {res.text}")
        return res.status_code == 200
    except Exception as e:
        log(f"Error updating file content: {e}")
    return False

def reindex_file_in_knowledge(knowledge_id, file_id):
    try:
        res = requests.post(
            f"{WEBUI_API}/api/v1/knowledge/{knowledge_id}/file/update",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"file_id": file_id}
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
                if reindex_file_in_knowledge(knowledge_id, existing_file_id):
                    log_history("updated", filename, knowledge_id)
                    return True
                else:
                    log(f"⚠️ Reindex failed for updated file: {filename}")
            else:
                log(f"⚠️ Failed to update content for file {filename}")
        else:
            log(f"⚠️ No file ID found for existing file: {filename} in knowledge {knowledge_id}")

    # fallback to upload + add
    data = {"file_id": file_id}
    res = requests.post(
        f"{WEBUI_API}/api/v1/knowledge/{knowledge_id}/file/add",
        headers={**HEADERS, "Content-Type": "application/json"},
        json=data
    )
    if res.status_code != 200:
        log(f"Add failed: {res.status_code} - {res.text}")
    else:
        log_history("added", filename, knowledge_id)
    return res.status_code == 200

def extract_model_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("**Model utilisé:**"):
                    return line.split("**Model utilisé:**")[-1].strip()
    except Exception as e:
        log(f"Failed to read model from {file_path}: {e}")
    return None

def loop():
    log("[Archivist] ✅ Entered loop()")
    model_collections = load_model_collections()
    while True:
        try:
            files = [f for f in os.listdir(MEMORY_DIR) if f.endswith(".txt") 
                     and os.path.isfile(os.path.join(MEMORY_DIR, f)) 
                     and not f.startswith("last_archived")]
            for fname in files:
                fpath = os.path.join(MEMORY_DIR, fname)
                log(f"Processing {fname}")
                model = extract_model_from_file(fpath) or "default"
                collection_id = model_collections.get(model) or model_collections.get("default")
                if not collection_id:
                    collection_id = DEFAULT_KNOWLEDGE_ID

                file_id = upload_file(fpath)
                if file_id:
                    if add_to_knowledge(file_id, collection_id, fname, fpath):
                        log(f"Archived {fname} to {collection_id}")
                        shutil.move(fpath, os.path.join(ARCHIVE_DIR, fname))
                    else:
                        log(f"Failed to add {fname} to knowledge")
                else:
                    log(f"Failed to upload {fname}")

        except Exception as e:
            log(f"Error: {e}")

        time.sleep(10)

if __name__ == "__main__":
    try:
        log("[Archivist] 🟢 Launching loop from __main__")
        loop()
    except Exception as e:
        log(f"[Archivist] ❌ Fatal error in __main__: {e}")
