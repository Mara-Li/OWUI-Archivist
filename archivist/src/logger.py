from datetime import datetime
from config import LOG_FILE, HISTORY_LOG


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def log_history(action: str, filename: str, knowledge_id: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {action.upper()} → {filename} in knowledge {knowledge_id}"
    with HISTORY_LOG.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
