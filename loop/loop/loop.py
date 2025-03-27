import shutil
import time
from webui_api import add_to_knowledge, get_chat_info, is_webui_reachable, upload_file
from config import DEFAULT_KNOWLEDGE_ID, FILENAME_TEMPLATE, MEMORY_DIR, TIMELOOP
from file_utils import extract_from_file, generate_filename, get_archive_path, load_model_collections, get_ongoing_id
from logger import log


def run_loop():
    log("[Archivist] ✅ Entered loop()")
    model_collections = load_model_collections()
    while True:
        last_archived = get_ongoing_id()
        if not is_webui_reachable():
            log("[Archivist] 🚫 WebUI not reachable. Skip updating.")
            time.sleep(TIMELOOP)
            continue
        try:
            files = [
                f for f in MEMORY_DIR.iterdir() if f.is_file() and not f.name.startswith("ongoing_conversation_id")
            ]
            for fpath in files:
                fname = fpath.name
                fbasename = fpath.stem
                if fbasename in last_archived:
                    log(f"⏭️ Skipping active conversation: {fbasename}")
                    continue
                log(f"Last archived: {last_archived} ; Current file: {fbasename}")
                log(f"Processing {fname}")
                info = extract_from_file(fpath)

                collection_id = model_collections.get(info.model) or model_collections.get("default")
                chat_info = get_chat_info(fbasename)
                if not chat_info:
                    log(f"Chat info not found for {fname}")
                    continue
                if not collection_id:
                    collection_id = DEFAULT_KNOWLEDGE_ID or "0"
                file_name: str = generate_filename(FILENAME_TEMPLATE, info.model, info.user, fbasename)
                file_id = upload_file(fpath, file_name)
                if file_id:
                    if add_to_knowledge(file_id, collection_id, file_name, fpath):
                        log(f"Archived {fname} to {collection_id} ({info.model})")
                        shutil.move(fpath, get_archive_path(fname, collection_id))
                    else:
                        log(f"Failed to add {fname} to knowledge {collection_id} ({info.model})")
                else:
                    log(f"Failed to upload {fname} to files.")

        except Exception as e:
            log(f"Error: {e}")

        time.sleep(TIMELOOP)
