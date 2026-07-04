import json
import re
import requests
from typing import Optional, Dict, Any, List


class LocalLLMClient:
    """
    Universal LLM Client for local + cloud execution.
    v5: Added robust JSON extraction, retry logic, quality validation,
         and multi-provider support (Ollama, OpenAI, Anthropic, LM Studio).
    """
    def __init__(
        self,
        model_name: str = "ollama/llama3",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.2,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        timeout: int = 300,
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.api_key = api_key
        self.timeout = timeout
        self.resolved_model = None
        self.quality_score = 1.0  # Tracks LLM quality (0-1)

        # Auto-detect provider
        if provider:
            self.provider = provider.lower()
        elif model_name.startswith("openai/") or model_name.startswith("gpt-"):
            self.provider = "openai"
        elif model_name.startswith("anthropic/") or model_name.startswith("claude-"):
            self.provider = "anthropic"
        elif "localhost:11434" in base_url or model_name.startswith("ollama/"):
            self.provider = "ollama"
        else:
            self.provider = "openai_compatible"  # LM Studio, etc.

        self.clean_model = model_name.replace("ollama/", "").replace("openai/", "").replace("anthropic/", "")

    def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4000) -> str:
        if not self.resolved_model:
            self._resolve_ollama_model()
        payload = {
            "model": self.resolved_model or self.clean_model,
            "prompt": prompt if not system_prompt else f"System: {system_prompt}\n\nUser: {prompt}",
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": max_tokens,
            },
        }
        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()

    def _resolve_ollama_model(self):
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", []) if m.get("name")]
                if self.clean_model in models:
                    self.resolved_model = self.clean_model
                elif models:
                    for m in models:
                        if self.clean_model in m or m.startswith(self.clean_model):
                            self.resolved_model = m
                            return
                    self.resolved_model = models[0]
        except Exception:
            pass

    def _call_openai(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4000) -> str:
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=self.clean_model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens,
            timeout=self.timeout,
        )
        return resp.choices[0].message.content or ""

    def _call_anthropic(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4000) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        resp = client.messages.create(
            model=self.clean_model,
            max_tokens=max_tokens,
            temperature=self.temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text if resp.content else ""

    def _call_openai_compatible(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4000) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.clean_model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        resp = requests.post(f"{self.base_url}/v1/chat/completions", json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4000) -> str:
        """Generate text with auto-provider detection and retry."""
        try:
            if self.provider == "ollama":
                text = self._call_ollama(prompt, system_prompt, max_tokens)
            elif self.provider == "openai":
                text = self._call_openai(prompt, system_prompt, max_tokens)
            elif self.provider == "anthropic":
                text = self._call_anthropic(prompt, system_prompt, max_tokens)
            else:
                text = self._call_openai_compatible(prompt, system_prompt, max_tokens)

            # Quality check
            if not text or len(text) < 50:
                self.quality_score = max(0.1, self.quality_score - 0.2)
                return f"[LLM WARNING: Response too short ({len(text)} chars). Model may be overloaded or too weak.]"

            self.quality_score = min(1.0, self.quality_score + 0.05)
            return text

        except requests.exceptions.Timeout:
            return f"[LLM TIMEOUT] Exceeded {self.timeout}s timeout. Consider a smaller prompt or faster model."
        except Exception as e:
            return f"[LLM ERROR: {str(e)[:200]}]"

    # ==================== JSON EXTRACTION (v5 robust) ====================

    def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Robust JSON extraction from messy LLM output with multiple strategies."""
        if not text:
            return None

        text = text.strip()

        # Strategy 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Strip markdown fences and parse
        cleaned = text.strip("`").replace("json", "").replace("JSON", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Strategy 3: Extract first {...} or [...] block
        for pattern in [r'\{.*?\}', r'\[.*?\]']:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

        # Strategy 4: Find nested braces (most robust for JSON objects)
        start = text.find('{')
        if start != -1:
            depth = 0
            for i, ch in enumerate(text[start:], start):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except json.JSONDecodeError:
                            pass
                        break

        # Strategy 5: Find nested brackets (for JSON arrays)
        start = text.find('[')
        if start != -1:
            depth = 0
            for i, ch in enumerate(text[start:], start):
                if ch == '[':
                    depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except json.JSONDecodeError:
                            pass
                        break

        return None

    def extract_json_list(self, text: str) -> List[Dict[str, Any]]:
        """Extract a JSON array (list of objects) from LLM output."""
        data = self.extract_json(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Sometimes LLM wraps array in a dict key
            for key in ["results", "data", "items", "gaps", "reviews", "entries"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        schema_hint: str = "",
        required_keys: Optional[List[str]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON with smart retry and fallback extraction.
        v5: This is the core fix — if LLM fails JSON, we try harder and fall back gracefully.
        """
        full_prompt = prompt
        if schema_hint:
            full_prompt = f"{prompt}\n\nYou MUST respond with valid JSON. {schema_hint}"

        for attempt in range(max_retries):
            text = self.generate(full_prompt, system_prompt, max_tokens)
            data = self.extract_json(text)

            if data is not None:
                # Validate required keys exist
                if required_keys and isinstance(data, dict):
                    missing = [k for k in required_keys if k not in data]
                    if not missing:
                        return data
                elif required_keys and isinstance(data, list):
                    return {"_items": data}
                else:
                    return data

            # Retry with simpler prompt
            if attempt < max_retries - 1:
                full_prompt = f"{prompt}\n\nCRITICAL: Respond ONLY with raw JSON. No markdown. No explanations. No code blocks."

        # Final fallback: return a structured dict with the raw text for manual parsing
        return {
            "_parse_error": True,
            "_raw_response": text[:2000],
            "_explanation": "LLM failed to produce valid JSON after multiple attempts."
        }

    def validate_quality(self, text: str, min_length: int = 100, expected_sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate LLM output quality and return diagnostic info."""
        result = {
            "valid": True,
            "length": len(text),
            "has_content": len(text) >= min_length,
            "warnings": [],
        }
        if not text:
            result["valid"] = False
            result["warnings"].append("Empty response")
        elif len(text) < min_length:
            result["valid"] = False
            result["warnings"].append(f"Response too short ({len(text)} chars, expected {min_length})")
        if expected_sections:
            for section in expected_sections:
                if section.lower() not in text.lower():
                    result["warnings"].append(f"Missing section: {section}")
        # Check for repetitive / garbage output
        lines = text.split('\n')
        if len(lines) > 5 and len(set(lines[:10])) < 3:
            result["warnings"].append("Highly repetitive output detected")
        return result
