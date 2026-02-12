from src.vector_store import VectorStore
import numpy as np

def test_vector_store_basic():
    store = VectorStore(dim=3)

    embeddings = np.array([
        [1,0,0],
        [0,1,0],
        [0,0,1]
    ])

    texts = ["a", "b", "c"]
    metadata = [{"pmid":"1"}, {"pmid":"2"}, {"pmid":"3"}]

    store.add(embeddings, texts, metadata)

    results = store.search(np.array([1,0,0]), k=1)

    assert results[0]["pmid"] == "1"
