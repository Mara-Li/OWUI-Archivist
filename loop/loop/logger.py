from datetime import datetime
from config import LOG_FILE, HISTORY_LOG


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
