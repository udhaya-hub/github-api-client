from api_client.exceptions import (
    APIAuthError,
    APIError,
    APINotFoundError,
    APIRateLimitError,
    APIServerError,
    APITimeoutError,
    APIValidationError,
    CacheError,
)


def test_api_error_base():
    err = APIError("Test error", status_code=500, response_body="body")
    assert err.message == "Test error"
    assert err.status_code == 500
    assert err.response_body == "body"
    assert "Test error" in str(err)
    assert "status=500" in str(err)


def test_api_auth_error():
    err = APIAuthError("Auth failed", status_code=401)
    assert isinstance(err, APIError)
    assert err.message == "Auth failed"
    assert err.status_code == 401


def test_api_rate_limit_error():
    err = APIRateLimitError("Rate limited", status_code=403, retry_after=60)
    assert isinstance(err, APIError)
    assert err.retry_after == 60


def test_api_not_found_error():
    err = APINotFoundError("Not found", status_code=404)
    assert isinstance(err, APIError)
    assert err.status_code == 404


def test_api_server_error():
    err = APIServerError("Server error", status_code=500)
    assert isinstance(err, APIError)
    assert err.status_code == 500


def test_api_timeout_error():
    err = APITimeoutError("Timeout", status_code=408)
    assert isinstance(err, APIError)
    assert err.status_code == 408


def test_api_validation_error():
    err = APIValidationError("Validation failed", status_code=422)
    assert isinstance(err, APIError)
    assert err.status_code == 422


def test_cache_error():
    err = CacheError("Cache failed")
    assert str(err) == "Cache failed"
