import json
import requests
from typing import Optional, Dict, Any, List


class LocalLLMClient:
    """
    Universal Open-Source LLM Client for local Windows execution.
    Features Automatic Model Discovery & Recovery to prevent 'model not found' 404 errors.
    100% Real Inference • Extended 300s Timeout for Deep Academic Reasoning.
    """
    def __init__(self, model_name: str = "ollama/llama3", base_url: str = "http://localhost:11434", temperature: float = 0.2):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.is_ollama = model_name.startswith("ollama/") or "localhost:11434" in self.base_url
        self.resolved_model = None

    def check_connection_and_resolve_model(self) -> bool:
        """
        Connects to local Ollama or LM Studio.
        If using Ollama, automatically checks installed models via /api/tags to prevent 404 errors.
        """
        try:
            if self.is_ollama:
                resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if resp.status_code != 200:
                    return False
                
                data = resp.json()
                installed_models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                
                if not installed_models:
                    print("[Ollama Warning] Ollama server is running, but no models are downloaded yet!")
                    return False

                requested_clean = self.model_name.replace("ollama/", "")
                
                # Exact match check
                if requested_clean in installed_models:
                    self.resolved_model = requested_clean
                    return True
                    
                # Partial / Tag prefix match (e.g., requested 'llama3', installed 'llama3:8b')
                for model in installed_models:
                    if model.startswith(requested_clean) or requested_clean in model:
                        print(f"[Ollama Auto-Recovery] Requested '{requested_clean}' not found exactly. Auto-switching to installed model: '{model}'")
                        self.resolved_model = model
                        return True
                
                # Fallback to first available installed model on user's machine
                print(f"[Ollama Auto-Recovery] Requested model not found. Defaulting to first available installed model: '{installed_models[0]}'")
                self.resolved_model = installed_models[0]
                return True

            else:
                # OpenAI-compatible server (LM Studio / LocalAI)
                resp = requests.get(f"{self.base_url}/v1/models", timeout=5)
                if resp.status_code == 200:
                    self.resolved_model = self.model_name.split("/")[-1]
                    return True
                return False

        except Exception as e:
            print(f"[Connection Check Error] {str(e)}")
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4000) -> str:
        """
        Executes genuine LLM text generation with auto-recovered model name.
        Allows extended timeouts (300 seconds / 5 minutes) for unhurried, deep analytical reasoning.
        """
        if not self.check_connection_and_resolve_model():
            return f"[LLM ENGINE OFFLINE OR NO MODELS FOUND] Could not connect to local AI engine at {self.base_url} or no models are downloaded. To perform deep analytical thinking, please start Ollama and ensure at least one model is pulled (e.g., open command prompt and run: 'ollama run llama3' or 'ollama pull mistral')."

        try:
            if self.is_ollama:
                payload = {
                    "model": self.resolved_model,
                    "prompt": prompt if not system_prompt else f"System: {system_prompt}\n\nUser: {prompt}",
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": max_tokens
                    }
                }
                response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=300)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "").strip()
                else:
                    return f"[Ollama API Error] HTTP Status {response.status_code}: {response.text}"
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                payload = {
                    "model": self.resolved_model or "local-model",
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": max_tokens
                }
                response = requests.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=300)
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    return f"[OpenAI API Error] HTTP Status {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return "[LLM TIMEOUT] The AI engine exceeded the 300-second (5 minute) timeout while conducting deep analytical reasoning. Consider selecting a smaller deliverable size or a faster model."
        except Exception as e:
            return f"[LLM EXECUTION EXCEPTION] {str(e)}"
