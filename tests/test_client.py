import httpx
import pytest
import respx

from api_client.client import GitHubClient
from api_client.exceptions import (
    APIAuthError,
    APINotFoundError,
    APIRateLimitError,
    APIServerError,
    APITimeoutError,
)


@pytest.fixture(autouse=True)
def mock_cache():
    from unittest.mock import MagicMock, patch
    with patch("api_client.client.get_cache") as mock_get_cache:
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_cache_instance.set.return_value = None
        mock_get_cache.return_value = mock_cache_instance
        yield mock_cache_instance


@respx.mock
def test_get_user_success(mock_user_response, mock_cache):
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=httpx.Response(
            200,
            json=mock_user_response,
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )
    )

    with GitHubClient() as client:
        result = client.get_user("octocat")

    assert result["login"] == "octocat"
    assert result["id"] == 1


@respx.mock
def test_get_user_auth_error(mock_cache):
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=httpx.Response(
            401,
            json={"message": "Bad credentials"},
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )
    )

    with GitHubClient() as client:
        with pytest.raises(APIAuthError) as exc_info:
            client.get_user("octocat")

    assert exc_info.value.status_code == 401


@respx.mock
def test_get_user_not_found(mock_cache):
    respx.get("https://api.github.com/users/nonexistent").mock(
        return_value=httpx.Response(
            404,
            json={"message": "Not Found"},
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )
    )

    with GitHubClient() as client:
        with pytest.raises(APINotFoundError) as exc_info:
            client.get_user("nonexistent")

    assert exc_info.value.status_code == 404


@respx.mock
def test_get_user_rate_limit(mock_cache):
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1234567890",
            },
        )
    )

    with GitHubClient() as client:
        with pytest.raises(APIRateLimitError) as exc_info:
            client.get_user("octocat")

    assert exc_info.value.status_code == 403
    assert exc_info.value.retry_after is not None


@respx.mock
def test_get_user_server_error(mock_cache):
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=httpx.Response(
            500,
            json={"message": "Internal Server Error"},
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )
    )

    with GitHubClient() as client:
        with pytest.raises(APIServerError) as exc_info:
            client.get_user("octocat")

    assert exc_info.value.status_code == 500


@respx.mock
def test_get_user_repos_pagination(mock_repos_response, mock_cache):
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        page = request.url.params.get("page", "1")
        if page == "1":
            return httpx.Response(
                200,
                json=mock_repos_response,
                headers={
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "4999",
                    "X-RateLimit-Reset": "1234567890",
                    "Link": '<https://api.github.com/users/octocat/repos?page=2>; rel="next"',
                },
            )
        return httpx.Response(
            200,
            json=[],
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4998",
                "X-RateLimit-Reset": "1234567890",
            },
        )

    respx.get("https://api.github.com/users/octocat/repos").mock(side_effect=handler)

    with GitHubClient() as client:
        result = client.get_user_repos("octocat")

    assert len(result) == 2
    assert result[0]["name"] == "Hello-World"
    assert result[1]["name"] == "Another-Repo"
    assert call_count == 2


@respx.mock
def test_get_repo_commits(mock_commits_response, mock_cache):
    respx.get("https://api.github.com/repos/octocat/Hello-World/commits").mock(
        return_value=httpx.Response(
            200,
            json=mock_commits_response,
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )
    )

    with GitHubClient() as client:
        result = client.get_repo_commits("octocat", "Hello-World")

    assert len(result) == 2
    assert result[0]["sha"] == "abc123"


@respx.mock
def test_get_repo_contributors(mock_contributors_response, mock_cache):
    respx.get("https://api.github.com/repos/octocat/Hello-World/contributors").mock(
        return_value=httpx.Response(
            200,
            json=mock_contributors_response,
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )
    )

    with GitHubClient() as client:
        result = client.get_repo_contributors("octocat", "Hello-World")

    assert len(result) == 2
    assert result[0]["login"] == "octocat"


@respx.mock
def test_get_rate_limit(mock_cache):
    respx.get("https://api.github.com/rate_limit").mock(
        return_value=httpx.Response(
            200,
            json={
                "resources": {
                    "core": {
                        "limit": 5000,
                        "remaining": 4999,
                        "reset": 1234567890,
                        "used": 1,
                    }
                }
            },
        )
    )

    with GitHubClient() as client:
        rate_limit = client.get_rate_limit()

    assert rate_limit.limit == 5000
    assert rate_limit.remaining == 4999


@respx.mock
def test_retry_on_server_error(mock_cache):
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(500, json={"message": "Server Error"})
        return httpx.Response(
            200,
            json={"login": "octocat"},
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
            },
        )

    respx.get("https://api.github.com/users/octocat").mock(side_effect=handler)

    with GitHubClient() as client:
        result = client.get_user("octocat")

    assert result["login"] == "octocat"
    assert call_count == 3


@respx.mock
def test_timeout_error(mock_cache):
    respx.get("https://api.github.com/users/octocat").mock(
        side_effect=httpx.TimeoutException("Timeout")
    )

    with GitHubClient() as client:
        with pytest.raises(APITimeoutError):
            client.get_user("octocat")
