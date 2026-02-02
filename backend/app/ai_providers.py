"""
ai_providers.py

AI providers with API keys configured:
- Groq (FREE, fast)
- Gemini (FREE tier)
- DeepSeek (affordable, powerful)
- Ollama (FREE, local)

auto-fallback between providers if one fails.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional

from app.config import (
    GROQ_API_KEY, GROQ_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    AI_PROVIDER
)


class AIProvider(ABC):
    """base class for AI providers"""
    
    name: str = "base"
    
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


class GroqProvider(AIProvider):
    """Groq - FREE, very fast inference"""
    
    name = "groq"
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL or "llama-3.1-8b-instant"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Groq error: {e}")


class GeminiProvider(AIProvider):
    """Google Gemini - FREE tier available"""
    
    name = "gemini"
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL or "gemini-1.5-flash"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            raise Exception("google-generativeai not installed")
        
        try:
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel(self.model)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini error: {e}")


class DeepSeekProvider(AIProvider):
    """DeepSeek - affordable, powerful reasoning"""
    
    name = "deepseek"
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.model = DEEPSEEK_MODEL or "deepseek-chat"
        self.base_url = "https://api.deepseek.com"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.8
                },
                timeout=30
            )
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise Exception(f"DeepSeek error: {e}")


class OllamaProvider(AIProvider):
    """Ollama - FREE, runs locally"""
    
    name = "ollama"
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL or "http://localhost:11434"
        self.model = OLLAMA_MODEL or "llama3"
    
    def is_available(self) -> bool:
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                    "options": {"num_predict": 150, "temperature": 0.8}
                },
                timeout=30
            )
            return response.json()["response"].strip()
        except Exception as e:
            raise Exception(f"Ollama error: {e}")


class MultiProviderAI:
    """
    manages multiple AI providers with auto-fallback.
    tries each provider until one succeeds.
    """
    
    def __init__(self):
        self.providers = {
            "groq": GroqProvider(),
            "gemini": GeminiProvider(),
            "deepseek": DeepSeekProvider(),
            "ollama": OllamaProvider(),
        }
        
        self.priority = ["groq", "deepseek", "gemini", "ollama"]
        self.preferred = AI_PROVIDER.lower() if AI_PROVIDER else "auto"
        
        print(f"[AI] Initialized providers: {self.get_available_providers()}")
    
    def get_available_providers(self) -> list:
        return [name for name, p in self.providers.items() if p.is_available()]
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.preferred != "auto" and self.preferred in self.providers:
            provider = self.providers[self.preferred]
            if provider.is_available():
                try:
                    return provider.generate(system_prompt, user_prompt)
                except Exception as e:
                    print(f"[AI] {self.preferred} failed: {e}, trying fallback...")
        
        errors = []
        for name in self.priority:
            provider = self.providers.get(name)
            if provider and provider.is_available():
                try:
                    result = provider.generate(system_prompt, user_prompt)
                    print(f"[AI] Using {name}")
                    return result
                except Exception as e:
                    errors.append(f"{name}: {e}")
                    continue
        
        raise Exception(f"All AI providers failed: {errors}")


ai = MultiProviderAI()


def generate_response(system_prompt: str, user_prompt: str) -> str:
    return ai.generate(system_prompt, user_prompt)
