"""Thin LLM client with model tiering. Default debate provider: Groq."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Tier defaults (Groq for pipeline; Gemini for judge)
DEFAULT_DEBATE_MODEL = "llama-3.3-70b-versatile"  # Pro / Con — quality-critical
DEFAULT_RESEARCH_MODEL = "llama-3.1-8b-instant"  # structured extract — cheaper
DEFAULT_SUMMARY_MODEL = "llama-3.1-8b-instant"  # synthesis — cheaper
DEFAULT_JUDGE_PROVIDER = "gemini"
DEFAULT_JUDGE_MODEL = "gemini-flash-latest"
DEFAULT_GEMINI_MODEL = "gemini-flash-latest"


def _env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


@dataclass(frozen=True)
class ModelTierConfig:
    """Per-role model IDs. Debate pipeline defaults to Groq; judge to Gemini."""

    provider: str = "groq"
    research_model: str = DEFAULT_RESEARCH_MODEL
    debate_model: str = DEFAULT_DEBATE_MODEL
    summary_model: str = DEFAULT_SUMMARY_MODEL
    judge_provider: str = DEFAULT_JUDGE_PROVIDER
    judge_model: str = DEFAULT_JUDGE_MODEL

    def for_role(self, role: str) -> tuple[str, str]:
        role = role.lower()
        if role == "research":
            return self.provider, self.research_model
        if role in ("debate", "pro", "con"):
            return self.provider, self.debate_model
        if role in ("summary", "summarizer"):
            return self.provider, self.summary_model
        if role == "judge":
            return self.judge_provider, self.judge_model
        raise ValueError(f"Unknown role: {role!r}")

    def as_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "research_model": self.research_model,
            "debate_model": self.debate_model,
            "summary_model": self.summary_model,
            "judge_provider": self.judge_provider,
            "judge_model": self.judge_model,
        }


def resolve_tiers(
    provider: str = "groq",
    *,
    research_model: str | None = None,
    debate_model: str | None = None,
    summary_model: str | None = None,
    judge_provider: str | None = None,
    judge_model: str | None = None,
) -> ModelTierConfig:
    provider = provider.lower().strip()
    if provider == "groq":
        research = (
            research_model
            or _env("GROQ_RESEARCH_MODEL")
            or DEFAULT_RESEARCH_MODEL
        )
        debate = (
            debate_model
            or _env("GROQ_DEBATE_MODEL", "GROQ_MODEL")
            or DEFAULT_DEBATE_MODEL
        )
        summary = (
            summary_model
            or _env("GROQ_SUMMARY_MODEL")
            or DEFAULT_SUMMARY_MODEL
        )
    else:
        # Gemini (or other) as debate provider: use one Gemini model for all
        # pipeline roles unless overridden.
        base = (
            debate_model
            or _env("GEMINI_MODEL")
            or DEFAULT_GEMINI_MODEL
        )
        research = research_model or _env("GEMINI_RESEARCH_MODEL") or base
        debate = base
        summary = summary_model or _env("GEMINI_SUMMARY_MODEL") or base

    j_provider = (
        judge_provider
        or _env("JUDGE_PROVIDER")
        or DEFAULT_JUDGE_PROVIDER
    ).lower()
    j_model = (
        judge_model
        or _env("JUDGE_MODEL", "GEMINI_JUDGE_MODEL")
        or (DEFAULT_JUDGE_MODEL if j_provider == "gemini" else DEFAULT_DEBATE_MODEL)
    )
    return ModelTierConfig(
        provider=provider,
        research_model=research,
        debate_model=debate,
        summary_model=summary,
        judge_provider=j_provider,
        judge_model=j_model,
    )


def get_client(provider: str = "groq") -> OpenAI:
    provider = provider.lower().strip()
    if provider == "groq":
        api_key = _env("groq_api_key", "GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Missing Groq API key. Set groq_api_key in .env")
        return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    if provider == "gemini":
        api_key = _env("gemini_api_key", "GEMINI_API_KEY", "GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing Gemini API key. Set gemini_api_key in .env"
            )
        return OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

    raise ValueError(f"Unknown provider: {provider!r}. Use 'groq' or 'gemini'.")


def default_model_for_provider(provider: str) -> str:
    if provider == "groq":
        return _env("GROQ_MODEL") or DEFAULT_DEBATE_MODEL
    if provider == "gemini":
        return _env("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    raise ValueError(provider)


def chat(
    system: str,
    user: str,
    *,
    provider: str = "groq",
    model: str | None = None,
    temperature: float = 0.4,
    max_tokens: int | None = None,
) -> str:
    client = get_client(provider)
    model_id = model or default_model_for_provider(provider)
    kwargs: dict = {
        "model": model_id,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Empty model response")
    return content.strip()
