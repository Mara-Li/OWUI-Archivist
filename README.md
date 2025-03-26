# 🗃 Archivist

**Archivist** is an open-source utility to automatically archive conversations from Open WebUI into a knowledge base (RAG-style). It consists of:

- 🔁 A background Python script (`archivist_loop.py`)
- 🧠 A pipeline for Open WebUI that saves conversations (`conversation_saver_pipeline.py`)
- 🐳 A Dockerfile to containerize the background service
- 🧩 A JSON file to map LLM model names to knowledge base collection IDs

---

## 🚀 Features

- Saves conversations to `.txt` files
- Automatically cleans up `<source_context>` or `<source>` blocks
- Maps conversations to the correct knowledge collection based on the model used
- Updates existing archived files instead of duplicating
- Logs activity and history in `archivist.log` and `archivist_history.log`

---

## 📦 Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-user/archivist.git
cd archivist
```

### 2. Configure
- Create an API token in Open WebUI
- Edit model_collections.json to map your model(s) to their knowledge base collection ID(s)
- Copy the token into your environnement or `.env` file

### 3. Start with docker compose
```yaml
# docker-compose.yml
services:
  # […] Open web ui configuration & ollama before
  archivist:
    build:
		context: ./loop
		dockerfile: Dockerfile
    container_name: archivist
    restart: unless-stopped
    environment:
      - WEBUI_TOKEN=your_openwebui_token
    volumes:
      - ./memories:/app/memories
      - ./model_collections.json:/app/model_collections.json
    networks:
      - open-webui

	pipelines:
    image: ghcr.io/open-webui/pipelines:main
    volumes:
      - ./pipelines:/app/pipelines
      - ./memories:/app/memories
    restart: unless-stopped
    networks:
      - open-webui
    container_name: pipelines
    depends_on:
      - open-webui
    ports:
      - "9099:9099"
    environment:
      - PIPELINES_REQUIREMENTS_PATH=/app/pipelines/requirements.txt
      - PIPELINES_API_KEY=0p3n-w3bu!
networks:
	open-webui:
    	driver: bridge
```

Then launch : `docker compose up -d`

> [!WARNING]
> Don't forget to connect the Pipeline to the Open WebUI in the admin panel.

## 📁 Generated files
- `memories/*.txt` — stored conversations
- `memories/archived/` — already archived files
- `memories/logs/archivist.log` — real-time logs
- `memories/logs/archivist_history.log` — persistent archive history

## ⚙️ Customization

### Loop
You can edit the environment variable to customize the loop behavior:

- `TIMELOOP` : time between each loop (in seconds)
- `MEMORY_DIR` : directory where the memories are stored **in the docker**
- `COLLECTIONS_FILE` : path to the collections json file
- `DEFAULT_KNOWLEDGE_ID` : default knowledge collection ID
- `WEBUI_API` : Open WebUI API URL
- `TOKEN` (mandatory) : Open WebUI API token
- `FILENAME_TEMPLATE` : template for the filename of the memories

#### Defaults values:
- `TIMELOOP` : 10
- `MEMORY_DIR` : `app/memories`
- `COLLECTIONS_FILE` : `app/model_collections.json`
- `DEFAULT_KNOWLEDGE_ID` : `None`
- `WEBUI_API` : `http://localhost:8000`
- `FILENAME_TEMPLATE` : `conversation_{timestamp}.txt`
- `ARCHIVE_DIR` : `app/memories/archived`

#### Filename

Generate a filename based on the template.
  Allowed value:
  - `{model}`: the model used in the conversation
  - `{date}`: the current date
  - `{time}`: the current time
  - `{datetime}`: the current datetime (Format: YYYY-MM-DD_HH-MM)
  - `{user}`: the user name
  For `{date}`, `{time}` and `{datetime}`, you can switch the format with the following syntax:
  `{date:%d-%m-%Y}`
default: `conversation_{datetime}.txt`

### Pipeline

In the **Pipeline** part of the Open Web UI admin panel, you can choose `conversation_saver.py` and edit the parameters:
- Save path: `/app/memories/`
  Should be the same as the `MEMORY_DIR` in the loop
- Archive path: `/app/memories/archived/`
  Should be the same as the `ARCHIVE_DIR` in the loop
- Intro template: A template for the introduction of the file, after mandatory information. You can use `{user}` and `{model}` to replace by the user and the model used.

> [!WARNING]
> The path should be the path in your docker instance, not in your computer.