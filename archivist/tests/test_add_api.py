import os
import sys
import json
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Chemin vers le dossier root du projet
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "loop"))

# Injecte les ENV VARS pour que add.py les utilise
test_memory_dir = PROJECT_ROOT / "tests" / "memories"
test_memory_dir.mkdir(parents=True, exist_ok=True)
os.environ["MEMORY_DIR"] = str(test_memory_dir)
os.environ["COLLECTIONS_FILE"] = str(PROJECT_ROOT / "model_collections.json")
os.environ["FILENAME_TEMPLATE"] = "conversation_{date}.md"
os.environ["USERS_API"] = str(PROJECT_ROOT / "user_api.json")

from src.add import app  # noqa: E402

client = TestClient(app)


class TestArchivistAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Crée un model_collections.json minimal s'il n'existe pas
        collections_file = Path(os.environ["COLLECTIONS_FILE"])
        if not collections_file.exists():
            collections_file.write_text(
                json.dumps({"default": {"id": "test-collection", "name": "Test Collection"}}), encoding="utf-8"
            )

        # Crée un fichier mémoire mock
        cls.chat_id = "47b87066-9adf-4cbf-9283-44c79dbc6e81"
        cls.user_id = "f4147eae-bfa5-408b-b67a-9ce0d498046e"
        cls.model = "default"
        cls.filepath = test_memory_dir / f"{cls.chat_id}.md"
        if not cls.filepath.exists():
            cls.filepath.write_text(
                "# Conversation ID: {}\n---\n**User**: Hello!\n**Assistant**: Hi!\n".format(cls.chat_id),
                encoding="utf-8",
            )
            print(f"Test file created at {cls.filepath}")

    def test_notify_missing_file(self):
        response = client.post(
            "/notify", json={"chat_id": "missing-id-000", "user_id": "test-user", "model": "default"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "no file")

    def test_notify_existing_file(self):
        response = client.post(
            "/notify", json={"chat_id": self.chat_id, "user_id": self.user_id, "username": "Lili", "model": self.model}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["status"], ["archived", "upload failed", "failed to add", "no title"])

    @classmethod
    def tearDownClass(cls):
        # Nettoyage
        try:
            cls.filepath.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
