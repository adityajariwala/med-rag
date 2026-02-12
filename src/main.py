import logging
from app_state import AppState
from pipeline import ask
import argparse

logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    app = AppState()
    app.build_index(force_refresh=args.refresh)

    while True:
        question = input("Ask a medical question (or 'exit'): ")
        if question == "exit":
            break

        output = ask(
            question=question,
            store=app.store,
            embedder=app.embedder,
            llm_client=app.llm_client
        )

        print(output["result"].answer_summary)
        print("Metrics:", output["metrics"])


if __name__ == "__main__":
    main()
