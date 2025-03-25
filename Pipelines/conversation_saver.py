# ✅ conversation_saver_pipeline.py (Pipeline compatible avec Open WebUI)
import json
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
        collections_models: str = json.dumps({
            "default": "fb2f8415-3936-4bf9-aebc-846365cd92b5"
        })
        intro_template: str = "This is a conversation archive between {user} with **{model}**."
        

    def __init__(self):
        self.type = "filter"
        self.name = "Conversation Saver Pipeline"
        self.valves = self.Valves()
        self.collections = json.loads(self.valves.collections_models)

    async def on_startup(self):
        print(f"[ConversationSaver] on_startup")

    async def on_shutdown(self):
        print(f"[ConversationSaver] on_shutdown")

    def clean_content(self, text: str) -> str:
        # Supprimer les balises <source_context> et <source> ainsi que leur contenu
        text = re.sub(r'<source_context>.*?</source_context>', '', text, flags=re.DOTALL)
        text = re.sub(r'<source>.*?</source>', '', text, flags=re.DOTALL)
        return text.strip()

    def get_collection_for_model(self, model: str) -> str:
        return self.collections.get(model, self.collections.get("default"))

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print("[ConversationSaver] outlet called")
        conversation_id = body.get("chat_id") or "unknown"
        model = body.get("model") or "unknown"
        messages = body.get("messages", [])
        username = (user.get("name") or user.get("email") or "User") if user else "User"
        
        if not messages:
            print("[ConversationSaver] No messages to save")
            return body

        os.makedirs(self.valves.save_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = os.path.join(self.valves.save_path, f"{conversation_id}.txt")
        intro = self.valves.intro_template.format(user=username, model=model)
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Conversation ID: {conversation_id}\n")
                f.write(f"**Date:** {timestamp}\n")
                f.write(f"**Model:** {model}\n")
                f.write("\n---\n")
                f.write(f"\n{intro}\n\n")

                for msg in messages:
                    role = msg.get("role", "user")
                    content = self.clean_content(msg.get("content", ""))
                    if not content.strip():
                        continue
                    speaker = username if role == "user" else role.capitalize()
                    f.write(f"**{speaker}**: {content}\n\n")

            print(f"[ConversationSaver] Saved to {filename}")
        except Exception as e:
            print(f"[ConversationSaver] Failed to write file: {e}")
        return body
