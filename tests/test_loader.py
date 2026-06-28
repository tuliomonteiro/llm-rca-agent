"""Tests for document loading and splitting — no LLM calls needed."""
import pytest
from pathlib import Path
from langchain.schema import Document
from src.ingestion.loader import load_documents, split_documents


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary directory with sample runbook files."""
    runbooks = tmp_path / "runbooks"
    runbooks.mkdir()
    (runbooks / "db_runbook.md").write_text(
        "# Database Runbook\nCheck connection pool. Run SELECT count(*) FROM pg_stat_activity.",
        encoding="utf-8",
    )
    (runbooks / "notes.txt").write_text(
        "Restart pods when memory exceeds 90%.", encoding="utf-8"
    )
    # A file with an ignored extension should not be loaded
    (runbooks / "ignore.csv").write_text("col1,col2\n1,2", encoding="utf-8")
    return tmp_path


class TestLoadDocuments:
    def test_loads_md_and_txt_files(self, tmp_data_dir):
        docs = load_documents(str(tmp_data_dir))
        assert len(docs) == 2

    def test_ignores_other_extensions(self, tmp_data_dir):
        docs = load_documents(str(tmp_data_dir))
        sources = [d.metadata.get("source", "") for d in docs]
        assert not any(s.endswith(".csv") for s in sources)

    def test_raises_on_missing_directory(self):
        with pytest.raises(FileNotFoundError):
            load_documents("/nonexistent/path/that/does/not/exist")

    def test_document_has_page_content(self, tmp_data_dir):
        docs = load_documents(str(tmp_data_dir))
        for doc in docs:
            assert isinstance(doc.page_content, str)
            assert len(doc.page_content) > 0

    def test_document_metadata_has_source(self, tmp_data_dir):
        docs = load_documents(str(tmp_data_dir))
        for doc in docs:
            assert "source" in doc.metadata

    def test_empty_directory_returns_empty_list(self, tmp_path):
        (tmp_path / "empty").mkdir()
        docs = load_documents(str(tmp_path / "empty"))
        assert docs == []

    def test_loads_nested_files(self, tmp_path):
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        (nested / "deep.md").write_text("Deep content", encoding="utf-8")
        docs = load_documents(str(tmp_path))
        assert len(docs) == 1
        assert "Deep content" in docs[0].page_content


class TestSplitDocuments:
    @pytest.fixture
    def sample_docs(self):
        long_text = "This is a sentence about database connections. " * 60
        return [
            Document(page_content=long_text, metadata={"source": "runbook.md"}),
        ]

    def test_returns_tuple_of_two_lists(self, sample_docs):
        result = split_documents(sample_docs)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_child_chunks_smaller_than_parent(self, sample_docs):
        child_chunks, parent_chunks = split_documents(sample_docs, chunk_size=200)
        avg_child = sum(len(d.page_content) for d in child_chunks) / len(child_chunks)
        avg_parent = sum(len(d.page_content) for d in parent_chunks) / len(parent_chunks)
        assert avg_child < avg_parent

    def test_child_chunks_respect_chunk_size(self, sample_docs):
        child_chunks, _ = split_documents(sample_docs, chunk_size=300, chunk_overlap=0)
        for chunk in child_chunks:
            # Allow some slack for splitter boundaries
            assert len(chunk.page_content) <= 400

    def test_empty_input_returns_empty_lists(self):
        child, parent = split_documents([])
        assert child == []
        assert parent == []

    def test_metadata_preserved_in_chunks(self, sample_docs):
        child_chunks, _ = split_documents(sample_docs)
        for chunk in child_chunks:
            assert chunk.metadata.get("source") == "runbook.md"
