from delete import delete_loop
from add import add_loop
from logger import log
import threading

if __name__ == "__main__":
    log("[Archivist] 🟢 Starting archivist...")
    try:
        threading.Thread(target=delete_loop, daemon=True).start()
        add_loop()
    except Exception as e:
        log(f"[Archivist] ❌ Fatal error: {e}")
