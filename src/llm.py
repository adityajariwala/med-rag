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

    # Sanitize context to remove problematic control characters
    # PubMed abstracts may contain tabs, control chars, etc.
    def sanitize_text(text: str) -> str:
        """Remove or replace control characters"""
        import re
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        # Remove control characters (0x00-0x1F except \n) and DEL (0x7F)
        # Keep newline (\n = 0x0A) for readability
        text = re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', '', text)
        # Normalize whitespace
        text = re.sub(r' +', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n\n+', '\n\n', text)
        return text.strip()

    # Build context with sanitized text
    context_parts = []
    for c in retrieved_chunks:
        sanitized = sanitize_text(c['text'])
        context_parts.append(f"PMID: {c['pmid']}\n{sanitized}")

    context = "\n\n".join(context_parts)

    # Double-check: log if context still has problematic chars
    import re
    if re.search(r'[\x00-\x08\x0B-\x1F\x7F]', context):
        logger.warning("Context still contains control characters after sanitization")

    prompt = f"""You are a medical research assistant. Your task is to answer the question using ONLY information from the provided context.

**CRITICAL RULES:**
1. Use ONLY the provided context - do not use external knowledge
2. Every claim in your answer must be directly supported by the context
3. Do not invent, infer, or extrapolate beyond what is explicitly stated
4. If the context doesn't contain enough information, say so clearly
5. Quote specific excerpts from the context as evidence
6. Set confidence based on the strength and amount of evidence in the context

**Output Format:**
Return your answer STRICTLY in valid JSON format with this schema:
{{
  "question": "the original question",
  "answer_summary": "your answer based ONLY on the context",
  "evidence": [
    {{"pmid": "PMID from context", "excerpt": "direct quote from context supporting your answer"}}
  ],
  "confidence": 0.0-1.0
}}

**IMPORTANT JSON RULES:**
- Return ONLY valid JSON (no markdown, no code blocks, no extra text)
- Use \\n for newlines in strings (not literal newlines)
- Escape all special characters properly
- Do not include any text before or after the JSON object

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

        # Try direct parsing first
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as e:
            # If direct parsing fails, try to clean the JSON
            logger.warning(f"Initial JSON parsing failed at position {e.pos}: {e.msg}")

            # Extract JSON from markdown code blocks if present
            if "```" in raw_output:
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_output, re.DOTALL)
                if json_match:
                    raw_output = json_match.group(1)
                    logger.info("Extracted JSON from markdown code block")
                    try:
                        parsed = json.loads(raw_output)
                        return MedicalAnswer(**parsed)
                    except json.JSONDecodeError:
                        pass  # Continue to next fix attempt

            # Try to extract just the JSON object (in case there's extra text)
            import re
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                potential_json = json_match.group(0)
                try:
                    parsed = json.loads(potential_json)
                    logger.info("Successfully extracted and parsed JSON object")
                    return MedicalAnswer(**parsed)
                except json.JSONDecodeError:
                    pass  # Continue to next fix attempt

            # Last resort: try to fix the LLM's output by cleaning it
            # Sometimes LLMs include literal newlines in JSON strings
            logger.warning("Attempting to fix JSON by escaping control characters in LLM output...")

            # Strategy: Find JSON strings and escape control chars within them
            # This is a heuristic approach
            try:
                # Simple approach: escape unescaped quotes and control chars
                import re

                # First, let's see if there are obvious unescaped newlines in string values
                # Pattern: look for strings that span multiple lines
                def escape_newlines_in_json_strings(text):
                    """Replace literal newlines with \\n in JSON string values"""
                    # This is a simplified heuristic - may not work for all cases
                    # We look for patterns like: "key": "value with
                    # newline"

                    # Try a simple global replacement approach
                    # Replace literal newlines that appear to be within JSON strings
                    lines = text.split('\n')
                    result = []
                    in_string = False

                    for line in lines:
                        # Count unescaped quotes to detect if we're in a string
                        quote_count = 0
                        i = 0
                        while i < len(line):
                            if line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                                quote_count += 1
                            i += 1

                        # If odd number of quotes, we're inside a string
                        if quote_count % 2 == 1:
                            if in_string:
                                # End of multiline string
                                result[-1] += ' ' + line.strip()
                                in_string = False
                            else:
                                # Start of multiline string
                                result.append(line)
                                in_string = True
                        else:
                            if in_string:
                                # Middle of multiline string
                                result[-1] += ' ' + line.strip()
                            else:
                                result.append(line)

                    return '\n'.join(result)

                cleaned = escape_newlines_in_json_strings(raw_output)
                parsed = json.loads(cleaned)
                logger.info("Successfully parsed after escaping newlines in JSON strings")
                return MedicalAnswer(**parsed)

            except Exception as clean_error:
                # If all attempts fail, show the problematic area
                error_pos = e.pos
                context_start = max(0, error_pos - 50)
                context_end = min(len(raw_output), error_pos + 50)
                error_context = raw_output[context_start:context_end]

                # Show the character at the error position
                error_char = raw_output[error_pos] if error_pos < len(raw_output) else 'EOF'
                error_char_repr = repr(error_char)

                logger.error(
                    f"JSON parsing failed after all attempts. Error: {e.msg}\n"
                    f"Position: {error_pos}\n"
                    f"Character at error: {error_char_repr}\n"
                    f"Context around error: ...{repr(error_context)}...\n"
                    f"Full output (first 1000 chars):\n{raw_output[:1000]}"
                )
                raise ValueError(f"LLM returned invalid JSON: {e.msg} at position {e.pos}")

        return MedicalAnswer(**parsed)

    except ValueError:
        raise  # Re-raise ValueError (JSON parsing errors)
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        raise
