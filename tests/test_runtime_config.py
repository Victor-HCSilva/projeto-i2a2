from configs.runtime_config import get_llm_config, get_setting


def test_get_setting_prefers_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-gemini-key")
    assert get_setting("GEMINI_API_KEY") == "env-gemini-key"


def test_get_setting_accepts_legacy_name(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "legacy-gemini-key")
    assert get_setting("GEMINI_API_KEY") == "legacy-gemini-key"


def test_get_llm_config_uses_gemini_defaults(monkeypatch):
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "configured-key")
    config = get_llm_config()
    assert config["provider"] == "gemini"
    assert config["api_key"] == "configured-key"
    assert config["model"] == "gemini-3.6-flash"


def test_get_llm_config_prefers_env_keys_over_stale_secret_provider(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "env-gemini-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)

    config = get_llm_config()

    assert config["provider"] == "gemini"
    assert config["api_key"] == "env-gemini-key"
