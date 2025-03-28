# 🗃 Archivist
**Archivist** is an open-source tool that automatically archives conversations from Open WebUI into a long-term memory knowledge base (RAG-style). It includes:

- 🔁 A background service (`archivist_loop.py`) that uploads and cleans up archived conversations
- 🧠 A pipeline (`conversation_saver_pipeline.py`) that saves each conversation to file
- 🐳 A Dockerfile to run the background service in a container
- 🧩 A `model_collections.json` file to map LLM model names to knowledge base collection IDs and name.
- 🔐 Optional multi-user API token support via `user_api.json`

---

## 🚀 Features
- Saves conversations into `.txt` or `.md` files
- Automatically removes `<source_context>`, `<source>`, and citations (like `[1]`)
- Organizes archived files by knowledge collection (optional)
- Updates existing files instead of duplicating them
- Tracks active conversations per user to avoid duplicate archiving
- Supports multiple API tokens (for shared Open WebUI instances)
- Automatically deletes conversations from the knowledge base when deleted from Open WebUI
- Logs actions and history (`archivist.log`, `archivist_history.log`)

---

## 🗜️ How it works
1. **Pipeline:**
   - When the user sends a message, the pipeline saves the conversation to `memories/{chat_id}.txt`
   - The pipeline tracks the current conversation in `memories/ongoing_conversations/{user_id}.txt`
2. **Loop:**
   - The loop scans the `memories` folder for finished conversations (i.e., not active anymore)
   - If a file is not currently ongoing, it:
     - Moves it to the `archived/{knowledge_id}/` folder (if `archive_per_knowledge` is enabled)
     - Uploads and indexes it into the corresponding knowledge base
   - If a chat was deleted, it removes both the file and its knowledge base record

---

## 📦 Setup
### 1. Clone the repository
```bash
git clone https://github.com/Mara-Li/OWUI-Archivist.git
cd archivist
```

### 2. Configure
- Create an API token in Open WebUI
- Edit `model_collections.json` to link each model name to its `knowledge_id` :

```
{
  "model_name": {
    "id": "knowledge_id_here",
    "name": "knowledge_name_here"
  }
}
```

> [!CAUTION]
> The knowledge name must be the same as set in the Open WebUI knowledge panel.

You can exclude:
- Per models, with settings as:

	```json
	  {
	    "model_name": {
	      "id": "0",
	      "name": "0"
	    }
	  }
	```

- All model not listed with the settings `ignore_models_not_listed` in the pipeline settings.

### Multiple user supports
If using multiple users, add their tokens in `api.json` like:

```json
{
  "default": "admin_token_here",
  "mara": "user_token_here"
}
```

- Set environment variables in the docker compose or in a `.env` file.

---

### 3. Docker Compose
Add this to your `docker-compose.yml`:

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main # or :cuda
    volumes:
      - ./open-webui:/app/backend/data
      - ./memories:/app/memories  # required!
    ports:
      - "8080:8080"
    networks:
      - open-webui
    restart: unless-stopped
    container_name: open-webui

  ollama:
    image: ollama/ollama:latest
    volumes:
      - /d/ollama/models:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - open-webui
    restart: unless-stopped
    container_name: ollama

  archivist:
    build:
      context: ./archivist
      dockerfile: Dockerfile
    container_name: archivist
    volumes:
      - ./memories:/app/memories
      - ./archivist/model_collections.json:/app/model_collections.json
      - ./archivist/user_api.json:/app/user_api.json  # optional, for multi-user
    environment:
      - WEBUI_API=http://open-webui:8080
      - WEBUI_TOKEN=your_api_token_here
      - DEFAULT_KNOWLEDGE_ID=your_default_knowledge_id_here
    networks:
      - open-webui
    depends_on:
      - open-webui
    restart: unless-stopped

  pipelines:
    image: ghcr.io/open-webui/pipelines:main
    container_name: pipelines
    volumes:
      - ./pipelines:/app/pipelines
      - ./memories:/app/memories  # required!
      - ./memories/model_collections.json:/app/model_collections.json #must be the same as archivist, the path can be changed in the settings, but you need to load in the container!
    ports:
      - "9099:9099"
    environment:
      - PIPELINES_REQUIREMENTS_PATH=/app/pipelines/requirements.txt
      - PIPELINES_API_KEY=0p3n-w3bu!
    networks:
      - open-webui
    depends_on:
      - open-webui
    restart: unless-stopped

networks:
  open-webui:
    driver: bridge
```

Then run:

```bash
docker compose up -d --build
```

> [!CAUTION]
> **Don't forget to enable the pipeline in Open WebUI's admin panel.**

## 📁 Files and Structure
| Path                                    | Description                          |
| --------------------------------------- | ------------------------------------ |
| `memories/*.{txt\|md}`                  | Current conversation files           |
| `memories/archived/({knowledge_name})/` | Archived conversations by collection |
| `memories/ongoing_conversations/`       | Tracks current conversation per user |
| `memories/logs/archivist.log`           | Real-time logs                       |
| `memories/logs/archivist_history.log`   | Detailed archive/update history      |

## ⚙️ Configuration
### 🌀 Archivist Loop - Environment Variables
You can configure Archivist behavior via environment variables in your Docker setup:

| Variable                | Description                                                                | Default                           |
| ----------------------- | -------------------------------------------------------------------------- | --------------------------------- |
| `WEBUI_TOKEN`           | 🔐 Your Open WebUI API token (**required**), **should be the admin token** | *(none)*                          |
| `WEBUI_API`             | URL of the Open WebUI API                                                  | `http://open-webui:8080`          |
| `DEFAULT_KNOWLEDGE_ID`  | Fallback knowledge ID if no model collection are set                       | *(optional)*                      |
| `FILENAME_TEMPLATE`     | Template to name the memory files                                          | `conversation_{datetime}.txt`     |
| `TIMELOOP`              | Time between each cleanup/upload loop (in seconds)                         | `10`                              |
| `ARCHIVE_PER_KNOWLEDGE` | Store files in subfolders by `knowledge_name` in `/archived/` (true/false) | `false`                           |
| `MEMORY_DIR`            | Path to the memory folder in the container                                 | `/app/memories`                   |
| `COLLECTIONS_FILE`      | Path to the json containing the collections ids (in the container)         | `/app/model_collections.json`     |
| `USERS_API`             | Path to the json containing the differents users api                       | (*optional*) `/app/user_api.json` |

### 🧠 Open WebUI Pipeline - Customizable Settings
Editable directly from the **Open WebUI admin panel**, under `conversation_saver_pipeline.py`:

| Setting                    | Description                                                                            |
| -------------------------- | -------------------------------------------------------------------------------------- |
| `save_path`                | Path to save the live conversation files (must match `MEMORY_DIR`)                     |
| `archive_path`             | Path to move archived conversations (must match `ARCHIVE_DIR`)                         |
| `intro_template`           | Custom intro text in each file (supports `{user}` and `{model}`)                       |
| `debug`                    | Enable verbose logs in Docker output                                                   |
| `extension`                | File format: choose `"md"` or `"txt"`                                                  |
| `archive_per_knowledge`    | If true, archives are stored in `/archived/{knowledge_name}/`                          |
| `ignore_models_not_listed` | Ignore models not listed in the model collections file                                 |
| `models_collections_path`  | Path to the JSON file for model collections to archive conversation and exclude models |

> [!NOTE]
> The file name will always be prefixed with the shortened chat ID (first 8 characters).
> Example: `[a1b2c3d4] conversation_{datetime}.md`