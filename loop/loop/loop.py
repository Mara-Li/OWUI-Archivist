import os
import shutil
import time
from webui_api import add_to_knowledge, get_chat_info, is_webui_reachable, upload_file
from config import ARCHIVE_DIR, DEFAULT_KNOWLEDGE_ID, FILENAME_TEMPLATE, MEMORY_DIR, TIMELOOP
from file_utils import extract_from_file, generate_filename, load_model_collections, read_last_archived
from logger import log


def run_loop():
    log("[Archivist] ✅ Entered loop()")
    model_collections = load_model_collections()
    last_archived = read_last_archived()
    while True:
        if not is_webui_reachable():
            log("[Archivist] 🚫 WebUI not reachable. Skip updating.")
            time.sleep(TIMELOOP)
            continue
        try:
            files = [
                f
                for f in os.listdir(MEMORY_DIR)
                if os.path.isfile(os.path.join(MEMORY_DIR, f)) and not f.startswith("ongoing_conversation_id")
            ]
            for fname in files:
                fpath = os.path.join(MEMORY_DIR, fname)
                fbasename = fname.split(".")[0]
                if fbasename == last_archived:
                    log(f"No need to archive {fname}: ongoing conversation")
                    continue
                log(f"Processing {fname}")
                info = extract_from_file(fpath)

                collection_id = model_collections.get(info.model) or model_collections.get("default")
                chat_info = get_chat_info(fname.split(".")[0])
                if not chat_info:
                    log(f"Chat info not found for {fname}")
                    continue
                if not collection_id:
                    collection_id = DEFAULT_KNOWLEDGE_ID
                file_name: str = generate_filename(FILENAME_TEMPLATE, info.model, info.user)
                file_id = upload_file(fpath, info.model, info.user, filename=file_name)
                if file_id:
                    if add_to_knowledge(file_id, collection_id, file_name, fpath):
                        log(f"Archived {fname} to {collection_id} ({info.model})")
                        shutil.move(fpath, os.path.join(ARCHIVE_DIR, fname))
                    else:
                        log(f"Failed to add {fname} to knowledge {collection_id} ({info.model})")
                else:
                    log(f"Failed to upload {fname} to files.")

        except Exception as e:
            log(f"Error: {e}")

        time.sleep(TIMELOOP)
