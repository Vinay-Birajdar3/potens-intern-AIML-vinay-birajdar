import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.ingest import load_documents, split_documents


def test_load_documents_returns_loaded_documents(monkeypatch):
    class FakeLoader:
        def __init__(self, path):
            self.path = path

        def load(self):
            return ["doc"]

    monkeypatch.setattr("app.ingest.PyPDFDirectoryLoader", FakeLoader)

    documents = load_documents()

    assert documents == ["doc"]


def test_split_documents_returns_chunks_for_loaded_docs():
    docs = [
        type(
            "Doc",
            (),
            {"page_content": "Policy section one.\n\nPolicy section two.", "metadata": {}}
        )()
    ]

    chunks = split_documents(docs)

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(getattr(chunk, "metadata", {}).get("chunk_id") for chunk in chunks)
    assert all(getattr(chunk, "metadata", {}).get("source_name") == "Unknown" for chunk in chunks)


class VectorStoreTests(unittest.TestCase):
    class FixedEmbeddings(Embeddings):
        def embed_documents(self, texts):
            return [[1.0, 0.0] for _ in texts]

        def embed_query(self, text):
            return [1.0, float(bool(text))]

    def test_empty_ingestion_preserves_the_existing_index(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "chroma_db"
            target.mkdir()
            marker = target / "existing.txt"
            marker.write_text("keep this index")

            with patch("app.ingest.config.CHROMA_DB_PATH", str(target)):
                with self.assertRaisesRegex(ValueError, "empty index"):
                    from app.ingest import create_vector_store

                    create_vector_store([])

            self.assertEqual(marker.read_text(), "keep this index")

    def test_failed_build_preserves_the_existing_index(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "chroma_db"
            target.mkdir()
            marker = target / "existing.txt"
            marker.write_text("keep this index")
            chunk = type(
                "Chunk",
                (),
                {
                    "page_content": "Policy excerpt.",
                    "metadata": {
                        "source_name": "Policy.pdf",
                        "page": 0,
                        "chunk_id": 1,
                    },
                },
            )()

            with (
                patch("app.ingest.config.CHROMA_DB_PATH", str(target)),
                patch("app.ingest.get_embedding_model", return_value=object()),
                patch(
                    "app.ingest.Chroma.from_documents",
                    side_effect=RuntimeError("embedding failed"),
                ),
            ):
                from app.ingest import create_vector_store

                with self.assertRaisesRegex(RuntimeError, "embedding failed"):
                    create_vector_store([chunk])

            self.assertEqual(marker.read_text(), "keep this index")
            self.assertEqual(
                [path.name for path in target.parent.iterdir()],
                ["chroma_db"],
            )

    def test_successful_build_replaces_index_after_staging(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "chroma_db"
            target.mkdir()
            (target / "existing.txt").write_text("old index")
            chunk = type(
                "Chunk",
                (),
                {
                    "page_content": "Policy excerpt.",
                    "metadata": {
                        "source_name": "Policy.pdf",
                        "page": 0,
                        "chunk_id": 1,
                    },
                },
            )()

            def build_index(*, persist_directory, **kwargs):
                self.assertIn("ids", kwargs)
                (Path(persist_directory) / "chroma.sqlite3").write_text("new index")
                return object()

            with (
                patch("app.ingest.config.CHROMA_DB_PATH", str(target)),
                patch("app.ingest.get_embedding_model", return_value=object()),
                patch("app.ingest.Chroma.from_documents", side_effect=build_index),
            ):
                from app.ingest import create_vector_store

                create_vector_store([chunk])

            self.assertFalse((target / "existing.txt").exists())
            self.assertEqual((target / "chroma.sqlite3").read_text(), "new index")

    def test_real_chroma_index_is_swapped_from_staging(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "chroma_db"
            target.mkdir()
            (target / "existing.txt").write_text("old index")
            chunk = type(
                "Chunk",
                (),
                {
                    "page_content": "Manager approval is required.",
                    "metadata": {
                        "source": "documents\\Leave_Policy.pdf",
                        "source_name": "Leave_Policy.pdf",
                        "page": 0,
                        "chunk_id": 1,
                    },
                },
            )()

            with (
                patch("app.ingest.config.CHROMA_DB_PATH", str(target)),
                patch(
                    "app.ingest.get_embedding_model",
                    return_value=self.FixedEmbeddings(),
                ),
            ):
                from app.ingest import create_vector_store

                create_vector_store([chunk])

            database = Chroma(
                persist_directory=str(target),
                collection_name="langchain",
                embedding_function=self.FixedEmbeddings(),
            )
            self.assertEqual(len(database.get()["ids"]), 1)
            self.assertFalse((target / "existing.txt").exists())
