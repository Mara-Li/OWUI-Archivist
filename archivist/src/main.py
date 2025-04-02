import threading
import uvicorn
from delete import delete_loop
from logger import log


def start_api():
    log("[Archivist] 🌀 Starting Archivist API server...")
    uvicorn.run("add:app", host="0.0.0.0", port=9000, reload=False)


if __name__ == "__main__":
    log("[Archivist] 🟢 Starting archivist...")
    try:
        threading.Thread(target=delete_loop, daemon=True).start()
        start_api()
    except Exception as e:
        log(f"[Archivist] ❌ Fatal error: {e}")
