# 🗃 Archivist
**Archivist** is an open-source tool that automatically archives conversations from Open WebUI into a long-term memory knowledge base (RAG-style). It includes:

- 🔁 A background **FastAPI service** that receives notifications of completed conversations
- 🧠 A **pipeline** (`conversation_saver_pipeline.py`) that saves ongoing conversations to files
- 🐳 A Dockerfile to run the background service in a container
- 🧩 A `model_collections.json` file to map LLM model names to knowledge base collection IDs and name
- 🔐 Optional multi-user API token support via `user_api.json`

---

## 🚀 Features
- Saves conversations into `.txt` or `.md` files
- Automatically removes `<source_context>`, `<source>`, and citations (like `[1]`)
- Organizes archived files by knowledge collection (optional)
- Updates existing files instead of duplicating them
- Tracks active conversations per user to avoid duplicate archiving
- Sends HTTP request to archive a previous conversation before writing the new one
- Supports multiple API tokens (for shared Open WebUI instances)
- Automatically deletes conversations from the knowledge base when deleted from Open WebUI
- Logs actions and history (`archivist.log`, `archivist_history.log`)

---

## 🧠 How it works

1. **Pipeline:**
   - When a user sends a message, the pipeline saves the conversation to `memories/{chat_id}.txt` or `.md`
   - It stores a metadata JSON file per user in `memories/ongoing_conversations/{user_id}.json`
   - When a new conversation is detected, it triggers the API (`/notify`) to archive the previous conversation

2. **FastAPI Archive Service:**
   - The service listens for POST requests to `/notify`
   - On receiving a notification, it:
     - Uploads the conversation file
     - Adds it to the appropriate knowledge base
     - Moves it to the archive folder
     - Optionally removes old knowledge entries if the chat was deleted

---

## 📦 Setup

### 1. Clone the repository
```bash
git clone https://github.com/Mara-Li/OWUI-Archivist.git
cd archivist
```

### 2. Configure
- Create an API token in Open WebUI
- Edit `model_collections.json` to map models:
```json
{
  "llama3.1:latest": {
    "id": "your-knowledge-id",
    "name": "llama knowledge"
  }
}
```
> Use `{ "id": "0", "name": "0" }` to exclude a model
> Set `ignore_models_not_listed: true` in the pipeline to ignore unmapped models

### Optional: Multi-user support
`user_api.json`:
```json
{
  "admin": "sk-admin-token",
  "lili": "sk-user-token"
}
```

### 3. Docker Compose
```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    volumes:
      - ./open-webui:/app/backend/data
      - ./memories:/app/memories
    ports:
      - "8080:8080"
    networks:
      - archivist-net

  ollama:
    image: ollama/ollama:latest
    volumes:
      - /d/ollama/models:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - archivist-net

  pipelines:
    image: ghcr.io/open-webui/pipelines:main
    volumes:
      - ./pipelines:/app/pipelines
      - ./memories:/app/memories
      - ./archivist/model_collections.json:/app/model_collections.json
    environment:
      - PIPELINES_REQUIREMENTS_PATH=/app/pipelines/requirements.txt
      - PIPELINES_API_KEY=0p3n-w3bu!
    ports:
      - "9099:9099"
    networks:
      - archivist-net

  archivist:
    build:
      context: ./archivist
      dockerfile: Dockerfile
    container_name: archivist
    volumes:
      - ./memories:/app/memories
      - ./archivist/model_collections.json:/app/model_collections.json
      - ./archivist/user_api.json:/app/user_api.json
    environment:
      - WEBUI_API=http://open-webui:8080
      - WEBUI_TOKEN=sk-admin-token
      - DEFAULT_KNOWLEDGE_ID=your-default-id
      - MEMORY_DIR=/app/memories
      - COLLECTIONS_FILE=/app/model_collections.json
      - FILENAME_TEMPLATE=conversation_{datetime}.md
      - ARCHIVE_PER_KNOWLEDGE=true
    ports:
      - "9000:9000"
    networks:
      - archivist-net

networks:
  archivist-net:
    driver: bridge
```

```bash
docker compose up -d --build
```

---

## 📁 Files and Structure
| Path                                        | Description                          |
| -------------------------------------------| ------------------------------------ |
| `memories/*.md`                             | Current conversation files           |
| `memories/archived/(knowledge_name)/`       | Archived conversations by collection |
| `memories/ongoing_conversations/{id}.json` | Tracks current conversation per user |
| `memories/logs/archivist.log`               | Real-time logs                       |
| `memories/logs/archivist_history.log`       | Archive history                      |

## ⚙️ Configuration
### 🔁 Archivist (FastAPI) - Environment Variables
| Variable                | Description                                                 |
|------------------------|-------------------------------------------------------------|
| `WEBUI_TOKEN`          | Open WebUI API token (admin)                                |
| `WEBUI_API`            | Open WebUI API base URL                                     |
| `DEFAULT_KNOWLEDGE_ID` | Fallback collection ID if none matched                     |
| `COLLECTIONS_FILE`     | Path to `model_collections.json` in the container           |
| `USERS_API`            | Path to `user_api.json` (multi-user support)                |
| `MEMORY_DIR`           | Path to memory folder (where files are saved)               |
| `ARCHIVE_PER_KNOWLEDGE`| Organize archived files by knowledge name (true/false)      |
| `FILENAME_TEMPLATE`    | Template for archive filename (see below)                   |

> `FILENAME_TEMPLATE` supports:
> - `{model}`
> - `{user}`
> - `{chat_id}`
> - `{date}`, `{time}`, `{datetime}` (use `{datetime:%Y-%m-%d}` to change format)

### 🧠 Pipeline Settings (editable in WebUI Admin Panel)
| Field                    | Description                                                |
|--------------------------|------------------------------------------------------------|
| `save_path`              | Path to store conversations (`/app/memories`)              |
| `archive_path`           | Archive directory (`/app/memories/archived`)              |
| `intro_template`         | Message inserted at the beginning of saved conversations  |
| `debug`                  | Enable console logs                                        |
| `extension`              | File extension: `md` or `txt`                             |
| `archive_per_knowledge`  | Enable per-collection folders                             |
| `ignore_models_not_listed`| Skip archiving if model isn't in JSON                     |
| `models_collections_path`| JSON path inside the container                            |
| `notify_url`             | Archivist API endpoint (default: `http://archivist:9000/notify`) |

---

## ✅ Example Output (Markdown)
```
---
conversation_id: "1234-abcd"
date: "2025-04-02 12:00"
model: "llama3"
user: "Lili"
---
Conversation with Lili using model llama3

**Lili**: Salut !

**Assistant**: Bonjour Lili ! Comment puis-je t’aider ?
```