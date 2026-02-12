from sentence_transformers import SentenceTransformer
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str = "pritamdeka/S-PubMedBert-MS-MARCO"):
        """
        Initialize the embedder with a biomedical sentence transformer model.

        Args:
            model_name: HuggingFace model name for embeddings
        """
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info(f"Model loaded successfully. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def embed(self, texts: list[str], show_progress: bool = True) -> np.ndarray:
        """
        Embed a list of texts into vector representations.

        Args:
            texts: List of text strings to embed
            show_progress: Whether to show progress bar

        Returns:
            numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        if not texts:
            logger.warning("Empty text list provided for embedding")
            return np.array([])

        try:
            logger.info(f"Embedding {len(texts)} texts...")
            embeddings = self.model.encode(texts, show_progress_bar=show_progress)
            logger.info(f"Embedding complete. Shape: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
