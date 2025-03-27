from collections import namedtuple
from datetime import datetime
import json
from pathlib import Path
import random
import re

import requests
from logger import log

from config import ARCHIVE_DIR, ARCHIVE_PER_KNOWLEDGE, COLLECTIONS_FILE, HEADERS, ONGOING_DIR, USERS_API, WEBUI_API

Info = namedtuple("Info", ["model", "user"])


def read_file_content(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        log(f"Error reading file content: {e}")
    return ""


def get_ongoing_id():
    ids = set()
    try:
        for path in ONGOING_DIR.glob("*.txt"):
            if path.is_file():
                chat_id = path.read_text(encoding="utf-8").strip()
                if chat_id:
                    ids.add(chat_id)
    except Exception as e:
        log(f"[Ongoing] Failed to list ongoing chat IDs: {e}")
    return ids


def extract_from_file(file_path: Path) -> Info:
    info = {"model": "default", "user": "User"}
    try:
        content = file_path.read_text(encoding="utf-8")
        sections = content.split("---")
        if len(sections) > 1:
            frontmatter = sections[1]
            for line in frontmatter.splitlines():
                for key in ("Model", "User", "Title"):
                    match = re.search(rf'{key}:\s*"([^"]+)"', line, re.IGNORECASE)
                    if match:
                        info[key.lower()] = match.group(1).strip()
    except Exception as e:
        log(f"Failed to read metadata from {file_path}: {e}")

    return Info(**info)


def load_user_api():
    try:
        return list(json.loads(USERS_API.read_text(encoding="utf-8")).values())
    except Exception as e:
        log(f"Failed to load user API: {e}")
        return []


def load_model_collections():
    try:
        return json.loads(COLLECTIONS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Failed to load model collections: {e}")
        return {}


def render_datetime_template(text: str):
    now = datetime.now()

    default_formats = {"date": "%Y-%m-%d", "time": "%H:%M", "datetime": "%Y-%m-%d_%H-%M"}

    def replacer(match):
        key = match.group(1)
        format_spec = match.group(2) or default_formats[key]

        if key == "date":
            value = now.date()
        elif key == "time":
            value = now.time()
        elif key == "datetime":
            value = now
        else:
            return match.group(0)

        return value.strftime(format_spec)

    # {clé:%format} ou {clé}
    return re.sub(r"\{(date|time|datetime)(?::(%[^}]+))?\}", replacer, text)


def generate_filename(template: str, model: str = "Default", user: str = "User", chat_id: str = "") -> str:
    """
    Generate a filename based on the template.
    Allowed value:
    - `{model}`: the model used in the conversation
    - `{date}`: the current date
    - `{time}`: the current time
    - `{datetime}`: the current datetime (Format: `YYYY-MM-DD_HH-MM`)
    - `{user}`: the user name
    - `{chat_id}`: the chat id
    For `{date}`, `{time}` and `{datetime}`, you can switch the format with the following syntax:
    `{date:%d-%m-%Y}`
    default: `conversation_{datetime}.txt`

    !!!important
    The conversation name will always be prefixed with the chat_id (with eight characters)
    """

    return f"[{chat_id[:8]}] {render_datetime_template(template).format(model=model.replace(':latest', ''), user=user)}"


def get_uid(filename: str) -> str:
    fn = re.match(r"^\[(\w{8})", filename, re.IGNORECASE)
    if fn:
        return fn.group(1)
    return "".join(map(str, random.sample(range(0, 9), 8)))


def get_knowledge_data(knowledge_id: str):
    try:
        res = requests.get(f"{WEBUI_API}/api/v1/knowledge/{knowledge_id}", headers=HEADERS)
        if res.status_code == 200:
            return res.json()
        else:
            log(f"Failed to fetch knowledge data: {res.status_code}")
    except Exception as e:
        log(f"Error fetching knowledge data: {e}")
    return None


def get_archive_path(fname: str, knowledge_id: str):
    archive_path = Path(ARCHIVE_DIR, fname)
    if ARCHIVE_PER_KNOWLEDGE:
        knowledge_data = get_knowledge_data(knowledge_id)
        if not knowledge_data:
            raise ValueError(f"Knowledge not found: {knowledge_id}")
        knowledge_name = knowledge_data.get("name")
        if not knowledge_name:
            raise ValueError(f"Knowledge name not found: {knowledge_id}")
        archive_path = Path(ARCHIVE_DIR, knowledge_name, fname)
        knowledge_path = Path(ARCHIVE_DIR, knowledge_name)
        if not knowledge_path.exists():
            knowledge_path.mkdir(parents=True, exist_ok=True)
    return archive_path
