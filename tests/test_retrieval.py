from src.evaluation import retrieval_recall

def test_retrieval_recall():
    retrieved = ["1", "2", "3"]
    ground_truth = ["2", "3"]

    assert retrieval_recall(retrieved, ground_truth) == 1.0
