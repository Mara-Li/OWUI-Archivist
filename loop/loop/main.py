from delete import delete_archived
from loop import run_loop
from logger import log
import threading

if __name__ == "__main__":
    log("[Archivist] 🟢 Starting archivist...")
    try:
        threading.Thread(target=delete_archived, daemon=True).start()
        run_loop()
    except Exception as e:
        log(f"[Archivist] ❌ Fatal error: {e}")
