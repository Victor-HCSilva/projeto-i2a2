import os

try:
    import streamlit as st
except Exception:  # pragma: no cover - optional in non-Streamlit contexts
    st = None


def _secret_value(name: str):
    if st is None:
        return None

    try:
        secrets = st.secrets
    except Exception:
        return None

    if not hasattr(secrets, "get"):
        return None

    value = secrets.get(name)
    return value if value not in (None, "") else None


def get_setting(name: str, default: str | None = None) -> str | None:
    """Return the configured value preferring environment variables over Streamlit secrets."""
    aliases = {
        "GEMINI_API_KEY": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "GOOGLE_API_KEY": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "MODEL_PROVIDER": ["MODEL_PROVIDER"],
        "MODEL_NAME": ["MODEL_NAME", "GEMINI_MODEL", "OPENAI_MODEL"],
        "OPENAI_API_KEY": ["OPENAI_API_KEY"],
        "MISTRAL_API_KEY": ["MISTRAL_API_KEY"],
    }

    candidates = aliases.get(name, [name])

    for candidate in candidates:
        value = os.getenv(candidate)
        if value not in (None, ""):
            return value

    for candidate in candidates:
        value = _secret_value(candidate)
        if value not in (None, ""):
            return value

    return default


def get_llm_config() -> dict:
    env_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    provider = (get_setting("MODEL_PROVIDER") or "").strip().lower()

    secret_gemini_key = _secret_value("GEMINI_API_KEY") or _secret_value(
        "GOOGLE_API_KEY"
    )
    gemini_key = env_gemini_key or secret_gemini_key

    openai_key = get_setting("OPENAI_API_KEY")
    mistral_key = get_setting("MISTRAL_API_KEY")

    if env_gemini_key:
        provider = "gemini"
    elif provider in ("", None):
        if gemini_key:
            provider = "gemini"
        elif openai_key:
            provider = "openai"
        elif mistral_key:
            provider = "mistral"
        else:
            provider = "gemini"

    if provider == "gemini":
        api_key = env_gemini_key or gemini_key or ""
        model = get_setting("MODEL_NAME") or "gemini-3.6-flash"
    elif provider == "openai":
        api_key = openai_key or ""
        model = get_setting("MODEL_NAME") or "gpt-4o-mini"
    elif provider == "mistral":
        api_key = mistral_key or ""
        model = get_setting("MODEL_NAME") or "mistral-small-latest"
    else:
        api_key = gemini_key or openai_key or mistral_key or ""
        model = get_setting("MODEL_NAME") or "gemini-3.6-flash"

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
    }
