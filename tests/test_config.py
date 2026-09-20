import pytest

from api_client.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("REQUEST_TIMEOUT", "60")
    monkeypatch.setenv("MAX_RETRIES", "5")

    settings = Settings()

    assert settings.github_token == "test_token"
    assert settings.request_timeout == 60.0
    assert settings.max_retries == 5


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.delenv("REQUEST_TIMEOUT", raising=False)
    monkeypatch.delenv("MAX_RETRIES", raising=False)
    monkeypatch.delenv("GITHUB_DEFAULT_USER", raising=False)

    settings = Settings()

    assert settings.request_timeout == 30.0
    assert settings.max_retries == 3
    assert settings.retry_base_delay == 1.0
    assert settings.rate_limit_threshold == 10
    assert settings.cache_ttl == 3600
    assert settings.github_default_user == "octocat"


def test_settings_default_user_override(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("GITHUB_DEFAULT_USER", "hubot")

    settings = Settings()

    assert settings.github_default_user == "hubot"


def test_settings_missing_token_raises(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    with pytest.raises(Exception):  # pydantic.ValidationError
        Settings()
