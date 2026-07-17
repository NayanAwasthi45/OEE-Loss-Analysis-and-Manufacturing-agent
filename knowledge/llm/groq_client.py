import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from dotenv import load_dotenv
import groq

from llm.prompts import MANUFACTURING_ANALYST_PROMPT

logger = logging.getLogger(__name__)


class GroqClient:
    """
    Client for interacting with the Groq API.

    Designed to be replaceable with Azure OpenAI, Ollama, etc.
    without affecting business logic.
    """

    def __init__(self, log_path: str = "logs/llm_responses.jsonl"):
        load_dotenv()
        self.log_path = log_path

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY is missing or invalid. LLM features will use fallback.")
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
        within the Groq token-per-request limit.  Results from every
        chunk are aggregated into a single list.

        Args:
            records: List of dicts with error-code-resolved production data.
            chunk_size: Max records per Groq request.

        Returns:
            Aggregated list of analysis dicts.
        """
        if not self.client:
            logger.error("Groq client not initialized. Returning fallback responses.")
            return self._generate_fallback_response(records)

        all_results: List[Dict[str, Any]] = []
        total_chunks = (len(records) + chunk_size - 1) // chunk_size

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            logger.info(
                f"Processing chunk {chunk_num}/{total_chunks} "
                f"({len(chunk)} records)."
            )

            prompt = MANUFACTURING_ANALYST_PROMPT.format(
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
        """Invokes Groq with one retry and logs every interaction."""
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
                            "content": "You are a helpful assistant that strictly outputs valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                )

                latency = time.time() - start_time
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
                logger.warning(f"Groq request failed on attempt {attempt + 1}: {exc}")
                attempt += 1

        logger.error("All retries exhausted for Groq batch analysis.")
        return self._generate_fallback_response(original_records)

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
        """Fallback when the LLM is unavailable or all retries fail."""
        return [
            {
                "id": record.get("id"),
                "predicted_pillar": "Unknown",
                "root_cause": "Unknown",
                "manager_summary": "LLM unavailable",
                "classification_status": "Pending Review",
            }
            for record in records
        ]
