from collections import namedtuple
import json
from pathlib import Path
import re
from typing import Literal, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

ModelCollection = namedtuple("ModelCollection", ["id", "name"])


class CollectionLoader:
    def __init__(self, path: str):
        self.path = Path(path)
        self.last_mtime = 0
        self.cache = {}

    def load(self):
        try:
            current_mtime = self.path.stat().st_mtime
            if current_mtime != self.last_mtime:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self.cache = {k: ModelCollection(**v) for k, v in raw.items()}
                self.last_mtime = current_mtime
        except Exception as e:
            print(f"[CollectionLoader] Failed to reload: {e}")
        return self.cache


class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        priority: int = 0
        save_path: str = Field(default="/app/memories", title="Path to save the conversation files")
        archive_path: str = Field(
            default="/app/memories/archived", title="Path to save the archived conversation files"
        )
        intro_template: str = Field(
            default="Conversation with {user} using model {model}", title="Template for the conversation intro"
        )
        debug: bool = Field(default=False, title="Activate debug mode")
        extension: Literal["md", "txt"] = Field(
            default="md",
            title="File extension for the conversation files. Support any text format file (txt, md…)",
        )
        archive_per_knowledge: bool = Field(default=False, title="Archive conversation per knowledge")
        models_collections_path: str = Field(
            default="/app/model_collections.json",
            title="JSON of model collections to archive conversation",
        )
        ignore_models_not_listed: bool = Field(
            default=False,
            title="Ignore models not listed in the model collections files",
        )

    def delete_archived(self, chat_id: str, model_name: str):
        archived_path = Path(self.valves.archive_path, f"{chat_id}.{self.valves.extension}")
        if self.valves.archive_per_knowledge:
            knowledge_name = (
                self.knowledges.get(model_name)
                or self.knowledges.get("default")
                or ModelCollection(id="default", name=model_name)
            )
            archived_path = Path(self.valves.archive_path, knowledge_name.name, f"{chat_id}.{self.valves.extension}")
        if archived_path.exists():
            try:
                archived_path.unlink()
                self._print(f"[ConversationSaver] Deleted {archived_path}")
            except Exception as e:
                self._print(f"[ConversationSaver] Failed to delete archived: {e}")

    def __init__(self):
        self.type = "filter"
        self.name = "Conversation Saver Pipeline"
        self.valves = self.Valves()
        self.collection_loader = CollectionLoader(self.valves.models_collections_path)
        self._print("[ConversationSaver] Initialized")

    def _print(self, *msg: object):
        if self.valves.debug:
            print("[ConversationSaver]", *msg)

    async def on_startup(self):
        self._print("[ConversationSaver] on_startup")

    async def on_shutdown(self):
        self._print("[ConversationSaver] on_shutdown")

    def write_last_archived(self, chat_id: str, user_id: str = ""):
        try:
            with open(
                Path(self.valves.save_path, "ongoing_conversations", f"{user_id}.txt"), "w", encoding="utf-8"
            ) as f:
                f.write(chat_id)
        except FileNotFoundError:
            self._print(f"[ConversationSaver] File not found: {self.valves.save_path}")
        except Exception as e:
            self._print(f"[ConversationSaver] Failed to write last_archived: {e}")

    def get_ongoing_conversation(self) -> str:
        ongoing_txt = Path(self.valves.save_path, "ongoing_conversation_id.txt")
        try:
            return ongoing_txt.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            self._print(f"[ConversationSaver] File not found: {self.valves.save_path}")
            return ""
        except Exception as e:
            self._print(f"[ConversationSaver] Failed to get ongoing conversation id: {e}")
            return ""

    def clean_content(self, text: str) -> str:
        # Supprimer les balises <source_context> et <source> ainsi que leur contenu
        text = re.sub(r"<source(_context)?>.*?</source(_context)?>", "", text, flags=re.DOTALL)
        text = re.sub(r"\[source_id.*\]", "", text)
        text = re.sub(r"\[\d+\]", "", text)
        return text.strip()

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        self._print("[ConversationSaver] outlet called")
        model = body.get("model") or "unknown"
        self.knowledges = self.collection_loader.load()
        self._print(f"[ConversationSaver] Loaded model collections: {self.knowledges}")

        if self.valves.ignore_models_not_listed and model not in self.knowledges:
            self._print(f"[ConversationSaver] Model not listed: {model}")
            return body

        ongoing_id = self.get_ongoing_conversation()
        conversation_id = body.get("chat_id") or "unknown"
        if conversation_id == ongoing_id:
            self._print("[ConversationSaver] Not need to archive: ongoing conversation")
            return body
        messages = body.get("messages", [])
        username = (user.get("name") or user.get("email") or "User") if user else "User"
        user_id = user.get("id", "unknow_user_id") if user else "unknow_user_id"

        if not messages:
            self._print("[ConversationSaver] No messages to save")
            return body

        Path(self.valves.save_path).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = Path(self.valves.save_path, f"{conversation_id}.{self.valves.extension}")
        intro = self.valves.intro_template.format(user=username, model=model)
        self.delete_archived(conversation_id, model)
        try:
            with open(filename, "w", encoding="utf-8") as f:
                # frontmatter, usefull if used with Obsidian for example
                f.write("---\n")
                f.write(f'conversation_id: "{conversation_id}"\n')
                f.write(f'date: "{timestamp}"\n')
                f.write(f'model: "{model}"\n')
                f.write(f'user: "{username}"\n')
                f.write(f"---\n{intro}\n\n")

                for msg in messages:
                    role = msg.get("role", "user")
                    content = self.clean_content(msg.get("content", ""))
                    if not content.strip():
                        continue
                    speaker = username if role == "user" else role.capitalize()
                    f.write(f"**{speaker}**: {content}\n\n")
            self.write_last_archived(conversation_id, user_id)
            self._print(f"[ConversationSaver] Saved to {filename}")
        except Exception as e:
            self._print(f"[ConversationSaver] Failed to write file: {e}")
        return body
