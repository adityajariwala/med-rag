from src.ingestion import fetch_pubmed
from src.chunking import chunk_text
from src.embeddings import Embedder
from src.vector_store import VectorStore
from src.llm import generate_answer
import logging
from src.evaluation import (
    retrieval_recall,
    log_retrieval_metrics,
    log_generation_metrics,
    check_faithfulness
)

logger = logging.getLogger(__name__)


def build_index(query):
    abstracts = fetch_pubmed(query)

    embedder = Embedder()
    all_chunks = []

    for doc in abstracts:
        chunks = chunk_text(doc["text"])
        all_chunks.extend(chunks)

    embeddings = embedder.embed(all_chunks)
    store = VectorStore(dim=len(embeddings[0]))
    store.add(embeddings, all_chunks)

    return store, embedder


def ask(question, store, embedder, llm_client, ground_truth_pmids=None):

    # ---- Retrieval ----
    query_embedding = embedder.embed([question])[0]
    retrieved = store.search(query_embedding)

    retrieved_pmids = [r["pmid"] for r in retrieved]

    log_retrieval_metrics(question, retrieved_pmids)

    # ---- Generation ----
    result = generate_answer(question, retrieved)

    log_generation_metrics(question, result.confidence)

    # ---- Evaluation ----
    recall = retrieval_recall(retrieved_pmids, ground_truth_pmids)

    context = "\n\n".join([r["text"] for r in retrieved])
    faithful = check_faithfulness(llm_client, result.answer_summary, context)

    logger.info({
        "event": "evaluation",
        "retrieval_recall": recall,
        "faithful": faithful
    })

    return {
        "result": result,
        "metrics": {
            "retrieval_recall": recall,
            "faithful": faithful
        }
    }
