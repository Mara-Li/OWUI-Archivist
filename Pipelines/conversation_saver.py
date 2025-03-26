import os
import re
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        priority: int = 0
        save_path: str = "/app/memories"
        archive_path: str = "/app/memories/archived"
        intro_template: str = "Ceci est l'archive d'une conversation entre {user} avec le modèle **{model}**."
        debug: bool = False

    def __init__(self):
        self.type = "filter"
        self.name = "Conversation Saver Pipeline"
        self.valves = self.Valves()


    def _print(self, *msg: object):
        if self.valves.debug:
            print("[ConversationSaver]", *msg)
    
    async def on_startup(self):
        self._print("[ConversationSaver] on_startup")

    async def on_shutdown(self):
        self._print("[ConversationSaver] on_shutdown")

    def clean_content(self, text: str) -> str:
        # Supprimer les balises <source_context> et <source> ainsi que leur contenu
        text = re.sub(r'<source_context>.*?</source_context>', '', text, flags=re.DOTALL)
        text = re.sub(r'<source>.*?</source>', '', text, flags=re.DOTALL)
        text= re.sub("[source_id:.*]", "", text)
        return text.strip()

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        self._print("[ConversationSaver] outlet called")
        conversation_id = body.get("chat_id") or "unknown"
        model = body.get("model") or "unknown"
        messages = body.get("messages", [])
        username = (user.get("name") or user.get("email") or "User") if user else "User"
        
        if not messages:
            self._print("[ConversationSaver] No messages to save")
            return body

        os.makedirs(self.valves.save_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = os.path.join(self.valves.save_path, f"{conversation_id}.txt")
        intro = self.valves.intro_template.format(user=username, model=model)
        try:
            with open(filename, "w", encoding="utf-8") as f:
                #frontmatter, usefull if used with Obsidian for example
                f.write("---\n")
                f.write(f"conversation_id: \"{conversation_id}\"\n")
                f.write(f"date: \"{timestamp}\"\n")
                f.write(f"model: \"{model}\"\n")
                f.write(f"user: \"{username}\"\n")
                f.write(f"---\n{intro}\n\n")

                for msg in messages:
                    role = msg.get("role", "user")
                    content = self.clean_content(msg.get("content", ""))
                    if not content.strip():
                        continue
                    speaker = username if role == "user" else role.capitalize()
                    f.write(f"**{speaker}**: {content}\n\n")

            self._print(f"[ConversationSaver] Saved to {filename}")
        except Exception as e:
            self._print(f"[ConversationSaver] Failed to write file: {e}")
        return body
