import os
import json
from openai import OpenAI
from src.schema import MedicalAnswer
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        # Validate required env vars
        base_url = os.getenv("OPENROUTER_BASE_URL")
        api_key = os.getenv("OPENROUTER_API_KEY")
        model = os.getenv("OPENROUTER_MODEL")

        if not all([base_url, api_key, model]):
            missing = []
            if not base_url:
                missing.append("OPENROUTER_BASE_URL")
            if not api_key:
                missing.append("OPENROUTER_API_KEY")
            if not model:
                missing.append("OPENROUTER_MODEL")

            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please check your .env file."
            )

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model
        logger.info(f"LLMClient initialized with model: {model}")

    def generate(self, prompt: str, temperature: float = 0.0, json_mode: bool = True) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature (0.0 = deterministic)
            json_mode: Whether to enforce JSON output format

        Returns:
            The generated text response

        Raises:
            Exception: If the API call fails
        """
        try:
            kwargs = {
                "model": self.model,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            # Only add response_format if json_mode is True
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise


def generate_answer(question: str, retrieved_chunks: list[dict]) -> MedicalAnswer:
    """
    Generate a medical answer from retrieved context chunks.

    Args:
        question: The medical question to answer
        retrieved_chunks: List of dicts with 'pmid' and 'text' keys

    Returns:
        MedicalAnswer object with structured response

    Raises:
        ValueError: If LLM returns invalid JSON
    """
    llm = LLMClient()

    if not retrieved_chunks:
        logger.warning("No chunks retrieved for answer generation")
        # Return minimal answer when no context available
        return MedicalAnswer(
            question=question,
            answer_summary="Insufficient evidence available in the retrieved literature.",
            evidence=[],
            confidence=0.0
        )

    context = "\n\n".join(
        [f"PMID: {c['pmid']}\n{c['text']}" for c in retrieved_chunks]
    )

    prompt = f"""You are a medical research assistant. Your task is to answer the question using ONLY information from the provided context.

**CRITICAL RULES:**
1. Use ONLY the provided context - do not use external knowledge
2. Every claim in your answer must be directly supported by the context
3. Do not invent, infer, or extrapolate beyond what is explicitly stated
4. If the context doesn't contain enough information, say so clearly
5. Quote specific excerpts from the context as evidence
6. Set confidence based on the strength and amount of evidence in the context

**Output Format:**
Return your answer STRICTLY in JSON format with this schema:
{{
  "question": "the original question",
  "answer_summary": "your answer based ONLY on the context",
  "evidence": [
    {{"pmid": "PMID from context", "excerpt": "direct quote from context supporting your answer"}}
  ],
  "confidence": 0.0-1.0
}}

**Confidence Guidelines:**
- 0.8-1.0: Strong, consistent evidence from multiple sources
- 0.5-0.7: Moderate evidence, some supporting information
- 0.0-0.4: Weak or insufficient evidence

**Context (ONLY SOURCE OF TRUTH):**
{context}

**Question:**
{question}

**Remember:** Every single claim in answer_summary must be supported by the context above. If you're unsure, lower your confidence or state the limitation."""

    try:
        raw_output = llm.generate(prompt)
        parsed = json.loads(raw_output)
        return MedicalAnswer(**parsed)
    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}\nOutput: {raw_output}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        raise
