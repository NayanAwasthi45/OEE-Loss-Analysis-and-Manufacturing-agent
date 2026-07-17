"""
Groq LLM Client for the Manufacturing Intelligence Engine.

Handles batch communication with the Groq API, including:
- Chunked batch analysis to stay within token limits
- Retry logic with exponential backoff
- HTTP 429 rate-limit detection and graceful skip
- LLM telemetry logging for auditing
- Fallback responses when the LLM is unavailable

Designed to be replaceable with Azure OpenAI, Ollama, etc.
without affecting business logic.
"""

import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from dotenv import load_dotenv

try:
    import groq
except ImportError:
    groq = None  # type: ignore[assignment]

from llm.prompts import MANUFACTURING_INTELLIGENCE_PROMPT

logger = logging.getLogger(__name__)


class GroqClient:
    """
    Client for interacting with the Groq API as a Manufacturing
    Intelligence Engine.

    Sends filtered, problematic production records for AI validation.
    Tracks response timing for console summary reporting.
    """

    def __init__(self, log_path: str = "logs/llm_responses.jsonl") -> None:
        """
        Initializes the Groq client with API key from environment.

        Args:
            log_path: Path to the JSONL telemetry log file.
        """
        load_dotenv()
        self.log_path = log_path
        self.total_response_time: float = 0.0

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning(
                "GROQ_API_KEY is missing or invalid. LLM features will use fallback."
            )
            self.client = None
        else:
            if groq is None:
                logger.error("groq package not installed. LLM features will use fallback.")
                self.client = None
            else:
                self.client = groq.Groq(api_key=api_key)

        self.model = "llama-3.3-70b-versatile"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def batch_analyze(
        self,
        records: List[Dict[str, Any]],
        chunk_size: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Sends enriched production records to Groq in manageable chunks.

        Large datasets are split into chunks of *chunk_size* to stay
        within the Groq token-per-request limit. Results from every
        chunk are aggregated into a single list.

        Args:
            records: List of dicts with error-code-resolved production data.
            chunk_size: Max records per Groq request.

        Returns:
            Aggregated list of analysis dicts with keys:
            - id, ai_validation, likely_root_cause, ai_observation
        """
        if not self.client:
            logger.error("Groq client not initialized. Returning fallback responses.")
            return self._generate_fallback_response(records)

        all_results: List[Dict[str, Any]] = []
        total_chunks = (len(records) + chunk_size - 1) // chunk_size
        self.total_response_time = 0.0

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            logger.info(
                f"Processing chunk {chunk_num}/{total_chunks} "
                f"({len(chunk)} records)."
            )

            prompt = MANUFACTURING_INTELLIGENCE_PROMPT.format(
                input_records=json.dumps(chunk, indent=2)
            )
            chunk_results = self._invoke_with_retry(prompt, chunk)
            all_results.extend(chunk_results)

        return all_results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _invoke_with_retry(
        self,
        prompt: str,
        original_records: List[Dict[str, Any]],
        retries: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Invokes Groq with one retry and logs every interaction.

        Handles HTTP 429 (rate limit) by returning AI Skipped responses
        instead of Unknown/Pending Review.

        Args:
            prompt: The formatted prompt string.
            original_records: Original records for fallback generation.
            retries: Number of retry attempts.

        Returns:
            List of analysis result dicts.
        """
        attempt = 0
        while attempt <= retries:
            start_time = time.time()
            try:
                logger.info(
                    f"Sending batch analysis request to Groq "
                    f"(Attempt {attempt + 1}/{retries + 1})"
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a Manufacturing Intelligence Engine "
                                "that strictly outputs valid JSON."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                )

                latency = time.time() - start_time
                self.total_response_time += latency
                content = response.choices[0].message.content
                req_id = getattr(response, "id", "unknown")

                try:
                    parsed = json.loads(content)

                    # The model might wrap the array inside a dict key
                    if isinstance(parsed, dict):
                        for val in parsed.values():
                            if isinstance(val, list):
                                parsed = val
                                break

                    if not isinstance(parsed, list):
                        raise ValueError(f"Expected JSON array, got {type(parsed)}")

                    self._log_interaction(self.model, req_id, content, parsed, latency)
                    return parsed

                except json.JSONDecodeError as exc:
                    logger.error(f"Failed to parse JSON from Groq: {exc}")
                    self._log_interaction(
                        self.model, req_id, content, {"error": "JSONDecodeError"}, latency
                    )
                    raise

            except Exception as exc:
                latency = time.time() - start_time
                self.total_response_time += latency

                # Detect HTTP 429 rate limit
                if self._is_rate_limit_error(exc):
                    logger.warning(
                        f"Groq rate limit (429) hit on attempt {attempt + 1}. "
                        f"Skipping batch with AI Skipped - Rate Limit."
                    )
                    return self._generate_rate_limit_response(original_records)

                logger.warning(f"Groq request failed on attempt {attempt + 1}: {exc}")
                attempt += 1

        logger.error("All retries exhausted for Groq batch analysis.")
        return self._generate_fallback_response(original_records)

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        """
        Checks if the exception is an HTTP 429 rate limit error.

        Inspects both groq-specific exception types and generic
        HTTP status code attributes.
        """
        # Check groq library RateLimitError
        if groq and isinstance(exc, groq.RateLimitError):
            return True

        # Check for status_code attribute (common in HTTP exceptions)
        status_code = getattr(exc, "status_code", None)
        if status_code == 429:
            return True

        # Check string representation as last resort
        exc_str = str(exc).lower()
        if "429" in exc_str and "rate" in exc_str:
            return True

        return False

    def _log_interaction(
        self,
        model: str,
        request_id: str,
        raw_json: str,
        parsed_json: Any,
        latency: float,
    ) -> None:
        """Persists LLM telemetry to a JSONL file for auditing."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "request_id": request_id,
            "latency": latency,
            "raw_json": raw_json,
            "parsed_json": parsed_json,
        }
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as exc:
            logger.error(f"Failed to write LLM telemetry log: {exc}")

    def _generate_fallback_response(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fallback when the LLM is unavailable or all retries fail.

        Returns Skipped responses with 'LLM Unavailable' reason.
        """
        return [
            {
                "id": record.get("id"),
                "ai_validation": "Skipped",
                "validation_reason": "LLM Unavailable. Manual review required.",
                "likely_root_cause": "Not Applicable",
                "manufacturing_insight": "LLM service unavailable. No manufacturing insight could be generated.",
            }
            for record in records
        ]

    def _generate_rate_limit_response(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Returns Skipped responses when Groq returns HTTP 429.
        """
        return [
            {
                "id": record.get("id"),
                "ai_validation": "Skipped",
                "validation_reason": "Rate Limit. Record skipped.",
                "likely_root_cause": "Not Applicable",
                "manufacturing_insight": "Groq rate limit reached. No manufacturing insight could be generated.",
            }
            for record in records
        ]
