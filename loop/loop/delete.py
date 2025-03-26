import os
import time

from webui_api import delete_file, get_chat_info, get_existing_file, remove_from_knowledge
from config import ARCHIVE_DIR, DEFAULT_KNOWLEDGE_ID, FILENAME_TEMPLATE, TIMELOOP
from file_utils import extract_from_file, generate_filename, load_model_collections
from logger import log


def delete_archived():
    log("[Delete archive] ✅ Cleaning up archived files")
    model_collections = load_model_collections()
    while True:
        try:
            files = [f for f in os.listdir(ARCHIVE_DIR) if os.path.isfile(os.path.join(ARCHIVE_DIR, f))]
            for fname in files:
                info_chat = get_chat_info(fname.split(".")[0])
                if info_chat:
                    log(f"✅ Chat {fname} exists! Continue...")
                    continue
                log(f"❌ Chat info not found for {fname} | Delete from knowledge")
                fpath = os.path.join(ARCHIVE_DIR, fname)
                info = extract_from_file(fpath)
                collection_id = model_collections.get(info.model) or model_collections.get("default")
                if not collection_id:
                    collection_id = DEFAULT_KNOWLEDGE_ID
                file_name: str = generate_filename(FILENAME_TEMPLATE, info.model, info.user)
                existing_file = get_existing_file(collection_id, file_name)
                if existing_file:
                    file_id = existing_file.get("id")
                    if delete_file(file_id):
                        if remove_from_knowledge({"file_id": file_id}, collection_id, fname):
                            log(f"Deleted {fname} from knowledge {collection_id}")
                    else:
                        log(f"Failed to delete {fname} from knowledge {collection_id}")
                else:
                    log(f"File not found in knowledge {collection_id}: {fname}")
                # remove file from archive as they are not in knowledge or deleted
                os.remove(fpath)
        except Exception as e:
            log(f"Error: {e}")
        time.sleep(TIMELOOP)
