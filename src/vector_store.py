import faiss
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, dim):
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []
        self.metadata = []

    def add(self, embeddings, texts, metadata):
        self.index.add(np.array(embeddings).astype("float32"))
        self.texts.extend(texts)
        self.metadata.extend(metadata)

    def search(self, query_embedding, k=5, score_threshold=None):
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector
            k: Number of results to return
            score_threshold: Optional L2 distance threshold (lower is better)
                           Only return results with distance <= threshold

        Returns:
            List of dicts with 'text', 'pmid', and 'score' keys
        """
        distances, indices = self.index.search(
            np.array([query_embedding]).astype("float32"), k
        )

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            # Skip if above threshold
            if score_threshold is not None and distance > score_threshold:
                continue

            results.append({
                "text": self.texts[idx],
                "pmid": self.metadata[idx]["pmid"],
                "score": float(distance)  # L2 distance (lower is better)
            })

        logger.info(f"Retrieved {len(results)} chunks (k={k}, threshold={score_threshold})")
        return results
