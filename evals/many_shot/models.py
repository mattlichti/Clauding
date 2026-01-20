"""
Model wrappers for different API providers.
"""

import os
from abc import ABC, abstractmethod

import anthropic
import openai
import google.generativeai as genai


class BaseModel(ABC):
    """Base class for model wrappers."""

    name: str

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        pass


class ClaudeModel(BaseModel):
    """Anthropic Claude model wrapper."""

    def __init__(self, model_id: str = "claude-sonnet-4-20250514"):
        self.model_id = model_id
        self.name = f"claude:{model_id}"
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    def generate(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


class OpenAIModel(BaseModel):
    """OpenAI model wrapper."""

    def __init__(self, model_id: str = "gpt-4o"):
        self.model_id = model_id
        self.name = f"openai:{model_id}"
        self.client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_id,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content


class GeminiModel(BaseModel):
    """Google Gemini model wrapper."""

    def __init__(self, model_id: str = "gemini-1.5-flash"):
        self.model_id = model_id
        self.name = f"gemini:{model_id}"
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_id)

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text


def get_model(provider: str, model_id: str | None = None) -> BaseModel:
    """
    Factory function to get a model by provider name.

    Args:
        provider: One of 'claude', 'openai', 'gemini'
        model_id: Optional specific model ID

    Returns:
        Model instance
    """
    if provider == "claude":
        return ClaudeModel(model_id) if model_id else ClaudeModel()
    elif provider == "openai":
        return OpenAIModel(model_id) if model_id else OpenAIModel()
    elif provider == "gemini":
        return GeminiModel(model_id) if model_id else GeminiModel()
    else:
        raise ValueError(f"Unknown provider: {provider}")
