from collections import namedtuple
from datetime import datetime
import json
import re
from logger import log

from config import COLLECTIONS_FILE, LAST_ARCHIVED

Info = namedtuple("Info", ["model", "user"])


def read_file_content(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log(f"Error reading file content: {e}")
    return ""


def read_last_archived():
    try:
        with open(LAST_ARCHIVED, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        log(f"File not found: {LAST_ARCHIVED}")
        return ""
    except Exception as e:
        log(f"Failed to read last_archived: {e}")
        return ""


def extract_from_file(file_path):
    info = {"model": "default", "user": "User"}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            frontmatter = "".join(f.readlines()).split("---")[1]
            for line in frontmatter.split("\n"):
                for key in ("Model", "User", "Title"):
                    match = re.search(rf"{key}: \"(.*)\"", line, re.IGNORECASE)
                    if match:
                        info[key.lower()] = match.group(1).strip()
    except Exception as e:
        log(f"Failed to read model from {file_path}: {e}")
    return Info(**info)


def load_model_collections():
    try:
        with open(COLLECTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Failed to load model collections: {e}")
        return {}


def render_datetime_template(text):
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


def generate_filename(template: str, model: str = "Default", user: str = "User") -> str:
    """
    Generate a filename based on the template.
    Allowed value:
    - `{model}`: the model used in the conversation
    - `{date}`: the current date
    - `{time}`: the current time
    - `{datetime}`: the current datetime (Format: `YYYY-MM-DD_HH-MM`)
    - `{user}`: the user name
    For `{date}`, `{time}` and `{datetime}`, you can switch the format with the following syntax:
    `{date:%d-%m-%Y}`
    default: `conversation_{datetime}.txt`
    """
    return render_datetime_template(template).format(model=model, user=user)
