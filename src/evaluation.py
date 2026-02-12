from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def retrieval_recall(retrieved_pmids: List[str], ground_truth_pmids: List[str]) -> float:
    if not ground_truth_pmids:
        return -1.0  # indicates no ground truth available

    hits = len(set(retrieved_pmids) & set(ground_truth_pmids))
    return hits / len(ground_truth_pmids)


def log_retrieval_metrics(query: str, retrieved_pmids: List[str]):
    logger.info({
        "event": "retrieval",
        "query": query,
        "retrieved_count": len(retrieved_pmids),
        "retrieved_pmids": retrieved_pmids,
    })


def log_generation_metrics(query: str, confidence: float):
    logger.info({
        "event": "generation",
        "query": query,
        "model_confidence": confidence,
    })

def check_faithfulness(llm_client, answer: str, context: str) -> bool:
    """
    Check if the answer is grounded in the provided context.

    Args:
        llm_client: LLM client for evaluation
        answer: The generated answer to check
        context: The retrieved context that should support the answer

    Returns:
        True if answer is faithful to context, False otherwise
    """
    prompt = f"""You are evaluating whether an answer is grounded in the provided context.

Your task: Determine if the answer contains ANY claims that are NOT supported by the context.

Answer:
{answer}

Context:
{context}

Instructions:
1. Read the answer carefully
2. Check if EVERY claim in the answer is supported by the context
3. If the answer invents facts, makes unsupported claims, or goes beyond the context, respond "YES"
4. If the answer only uses information from the context, respond "NO"

Respond with ONLY one word: YES or NO"""

    try:
        result = llm_client.generate(prompt, temperature=0.0, json_mode=False)

        # Extract YES/NO from response
        result_clean = result.strip().upper()

        # Check for YES (has unsupported claims) or NO (faithful)
        if "NO" in result_clean:
            return True  # Faithful - no unsupported claims
        elif "YES" in result_clean:
            return False  # Not faithful - has unsupported claims
        else:
            logger.warning(f"Unexpected faithfulness response: {result}")
            return False  # Conservative default

    except Exception as e:
        logger.error(f"Faithfulness check failed: {e}")
        return False  # Conservative default