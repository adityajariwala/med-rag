from src.ingestion import fetch_pubmed_with_cache
from src.chunking import chunk_text
from src.embeddings import Embedder
from src.vector_store import VectorStore
from src.llm import LLMClient
import logging
import os

logger = logging.getLogger(__name__)


class AppState:
    def __init__(self):
        self.embedder = Embedder()
        self.llm_client = LLMClient()
        self.store = None

    def build_index(
        self,
        query: str | None = None,
        max_results: int = 100,
        force_refresh: bool = False
    ):
        """
        Build the vector index from PubMed abstracts.

        Args:
            query: PubMed search query. Defaults to env var or fallback query.
            max_results: Maximum number of abstracts to retrieve
            force_refresh: Force refresh cache even if it exists
        """
        # Get query from env var or use default
        if query is None:
            query = os.getenv(
                "PUBMED_DEFAULT_QUERY",
                "GLP-1 cardiovascular outcomes"
            )

        logger.info(f"Building index with query: '{query}' (max_results={max_results})")

        abstracts = fetch_pubmed_with_cache(
            query,
            max_results=max_results,
            force_refresh=force_refresh
        )

        logger.info(f"Retrieved {len(abstracts)} abstracts from PubMed")

        all_chunks = []
        metadata = []

        for doc in abstracts:
            chunks = chunk_text(doc["text"])
            for chunk in chunks:
                all_chunks.append(chunk)
                metadata.append({"pmid": doc["pmid"]})

        logger.info(f"Created {len(all_chunks)} chunks from abstracts")

        embeddings = self.embedder.embed(all_chunks)

        store = VectorStore(dim=len(embeddings[0]))
        store.add(embeddings, all_chunks, metadata)

        self.store = store
        logger.info("Index built successfully")
