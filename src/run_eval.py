import json
from pipeline import ask

def run_evaluation(eval_file):
    with open(eval_file) as f:
        dataset = json.load(f)

    results = []

    for item in dataset:
        output = ask(
            question=item["question"],
            ground_truth_pmids=item["ground_truth_pmids"]
        )

        results.append(output["metrics"])

    return results
