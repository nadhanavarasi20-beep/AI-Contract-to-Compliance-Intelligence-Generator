import json
import re
import time
import threading
from typing import Optional, Dict, Any, List
from backend.config import settings

class GeminiAPIError(Exception):
    """General Gemini API exception."""
    pass

class GeminiQuotaExhaustedError(GeminiAPIError):
    """Raised when Gemini 429 Quota Exceeded occurs."""
    pass

class GeminiClient:
    """Resilient Google Gemini client with rate limiting, retries, and quota protection."""

    # Thread-safe rate limiter lock
    _lock = threading.Lock()
    _last_call_time = 0.0

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        # Map user-facing model name to an active backend model
        self.requested_model = model_name or settings.DISPLAY_MODEL_NAME
        self.active_model = self._resolve_model_name(self.requested_model)
        self.client = None
        self._init_sdk()

    def _resolve_model_name(self, name: str) -> str:
        """Maps model name or alias to standard Gemini model identifiers."""
        name_lower = name.lower()
        if "3.8" in name_lower or "2.5" in name_lower:
            return "gemini-2.5-flash"
        elif "2.0" in name_lower:
            return "gemini-2.0-flash"
        elif "1.5" in name_lower:
            return "gemini-1.5-flash"
        return "gemini-2.5-flash"

    def _init_sdk(self):
        """Initializes the SDK if an API key is available."""
        if not self.api_key:
            return

        try:
            # Try google-genai first
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "google-genai"
        except Exception:
            try:
                # Fallback to google.generativeai
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=self.api_key)
                self.client = genai_legacy.GenerativeModel(self.active_model)
                self.sdk_type = "google-generativeai"
            except Exception as e:
                self.client = None
                self.sdk_type = "none"

    def is_configured(self) -> bool:
        """Returns True if the API key and client are configured."""
        return bool(self.api_key and self.client)

    def _apply_rate_limit(self):
        """Enforces minimum delay between calls to prevent 429 quota exhaustion."""
        with GeminiClient._lock:
            now = time.time()
            elapsed = now - GeminiClient._last_call_time
            min_delay = settings.REQUEST_DELAY_SECONDS
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)
            GeminiClient._last_call_time = time.time()

    def generate_json_response(self, prompt: str, system_instruction: Optional[str] = None, max_retries: int = 2) -> Dict[str, Any]:
        """Generates a structured JSON response from Gemini with backoff retries."""
        if not self.is_configured():
            raise GeminiAPIError("Gemini API key is not configured or client failed to initialize.")

        retry_count = 0
        backoff = 3.0

        while retry_count <= max_retries:
            try:
                self._apply_rate_limit()

                raw_text = ""
                if self.sdk_type == "google-genai":
                    response = self.client.models.generate_content(
                        model=self.active_model,
                        contents=prompt,
                        config={
                            "response_mime_type": "application/json"
                        } if not system_instruction else {
                            "response_mime_type": "application/json",
                            "system_instruction": system_instruction
                        }
                    )
                    raw_text = response.text or ""
                elif self.sdk_type == "google-generativeai":
                    response = self.client.generate_content(
                        prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    raw_text = response.text or ""
                else:
                    raise GeminiAPIError("No supported Gemini SDK loaded.")

                # Parse JSON
                cleaned_json = self._extract_json_block(raw_text)
                return json.loads(cleaned_json)

            except Exception as e:
                error_str = str(e).lower()
                
                # Check for Quota / Rate limit (429)
                if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                    if retry_count < max_retries:
                        time.sleep(backoff)
                        backoff *= 2.0
                        retry_count += 1
                        continue
                    else:
                        raise GeminiQuotaExhaustedError(f"Gemini API quota exceeded (429): {str(e)}")

                # Check for Invalid API Key / Auth error
                if "403" in error_str or "api_key" in error_str or "permission" in error_str or "unauthenticated" in error_str:
                    raise GeminiAPIError(f"Gemini API Authentication Error: {str(e)}")

                # Check for model not found / alias mismatch
                if "404" in error_str or "not found" in error_str:
                    if self.active_model != "gemini-1.5-flash":
                        self.active_model = "gemini-1.5-flash"
                        retry_count += 1
                        continue

                # Other errors
                if retry_count < max_retries:
                    time.sleep(backoff)
                    retry_count += 1
                    continue
                else:
                    raise GeminiAPIError(f"Gemini Generation Error: {str(e)}")

        raise GeminiAPIError("Maximum retries exceeded while calling Gemini API.")

    def _extract_json_block(self, text: str) -> str:
        """Extracts JSON substring from text even if markdown wrappers exist."""
        text = text.strip()
        # Check for ```json ... ```
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            return match.group(1).strip()
        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1].strip()
        return text
