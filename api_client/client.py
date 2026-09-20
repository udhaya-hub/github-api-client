import json
import logging
import time
from typing import Any, TypeVar

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from api_client.cache import get_cache
from api_client.config import get_settings
from api_client.exceptions import (
    APIAuthError,
    APIError,
    APINotFoundError,
    APIRateLimitError,
    APIServerError,
    APITimeoutError,
)
from api_client.models import RateLimitInfo

logger = logging.getLogger(__name__)

T = TypeVar("T")


class GitHubClient:
    def __init__(self) -> None:
        s = get_settings()
        self.base_url = s.github_api_base_url.rstrip("/") + "/"
        self.headers = {
            "Authorization": f"token {s.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "api-client/0.1.0",
        }
        self.timeout = s.request_timeout
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "GitHubClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _parse_rate_limit(self, response: httpx.Response) -> RateLimitInfo:
        return RateLimitInfo(
            limit=int(response.headers.get("X-RateLimit-Limit", "0")),
            remaining=int(response.headers.get("X-RateLimit-Remaining", "0")),
            reset=int(response.headers.get("X-RateLimit-Reset", "0")),
            used=int(response.headers.get("X-RateLimit-Used", "0")),
        )

    def _check_rate_limit(self, rate_limit: RateLimitInfo) -> None:
        s = get_settings()
        if rate_limit.remaining <= s.rate_limit_threshold:
            reset_time = rate_limit.reset
            wait_time = max(reset_time - int(time.time()), 0) + 1
            logger.warning(
                "Rate limit threshold reached: %d remaining. Waiting %d seconds",
                rate_limit.remaining,
                wait_time,
            )
            if wait_time > 0:
                time.sleep(wait_time)

    def _handle_error_response(self, response: httpx.Response) -> None:
        rate_limit = self._parse_rate_limit(response)

        if response.status_code == 401:
            raise APIAuthError(
                "Invalid or missing authentication token",
                status_code=response.status_code,
                response_body=response.text,
            )
        elif response.status_code == 403:
            if rate_limit.remaining == 0:
                raise APIRateLimitError(
                    "Rate limit exceeded",
                    status_code=response.status_code,
                    response_body=response.text,
                    retry_after=rate_limit.reset - int(time.time()),
                )
            raise APIAuthError(
                "Access forbidden - check token permissions",
                status_code=response.status_code,
                response_body=response.text,
            )
        elif response.status_code == 404:
            raise APINotFoundError(
                "Resource not found",
                status_code=response.status_code,
                response_body=response.text,
            )
        elif 500 <= response.status_code < 600:
            raise APIServerError(
                f"Server error: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )
        elif response.status_code >= 400:
            raise APIError(
                f"Request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(
            (APIServerError, APITimeoutError, httpx.TimeoutException, httpx.NetworkError)
        ),
        reraise=True,
    )
    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        use_cache: bool = True,
        cache_key: str | None = None,
    ) -> httpx.Response:
        full_cache_key = cache_key or f"{method}:{path}:{json.dumps(params, sort_keys=True)}"

        if use_cache and method == "GET":
            cached = get_cache().get(full_cache_key)
            if cached is not None:
                logger.debug("Cache hit for %s", full_cache_key)
                response = httpx.Response(
                    status_code=200,
                    json=cached,
                    headers={"X-Cache": "HIT"},
                )
                return response

        logger.debug("Making %s request to %s", method, path)
        try:
            response = self.client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
            )
        except httpx.TimeoutException as e:
            logger.warning("Request timeout: %s", e)
            raise APITimeoutError("Request timed out") from e
        except httpx.NetworkError as e:
            logger.warning("Network error: %s", e)
            raise APITimeoutError(f"Network error: {e}") from e

        self._handle_error_response(response)
        rate_limit = self._parse_rate_limit(response)
        self._check_rate_limit(rate_limit)

        logger.debug(
            "Response: %d, Rate limit: %d/%d remaining",
            response.status_code,
            rate_limit.remaining,
            rate_limit.limit,
        )

        if use_cache and method == "GET" and response.status_code == 200:
            try:
                get_cache().set(full_cache_key, response.json())
            except Exception as e:
                logger.warning("Failed to cache response: %s", e)

        return response

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
        cache_key: str | None = None,
    ) -> httpx.Response:
        return self._request("GET", path, params=params, use_cache=use_cache, cache_key=cache_key)

    def get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        per_page: int = 100,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        page = 1
        request_params = {**(params or {}), "per_page": per_page}

        while True:
            request_params["page"] = page
            cache_key = f"paginated:{path}:{json.dumps(request_params, sort_keys=True)}"

            response = self.get(path, params=request_params, use_cache=use_cache, cache_key=cache_key)
            data = response.json()

            if not data:
                break

            all_items.extend(data)

            link_header = response.headers.get("Link", "")
            if 'rel="next"' not in link_header:
                break

            page += 1

        return all_items

    def get_user(self, username: str) -> dict[str, Any]:
        response = self.get(f"users/{username}")
        return response.json()  # type: ignore[no-any-return]

    def get_user_repos(self, username: str) -> list[dict[str, Any]]:
        return self.get_all_pages(f"users/{username}/repos", params={"type": "owner", "sort": "updated"})

    def get_repo_commits(self, owner: str, repo: str) -> list[dict[str, Any]]:
        return self.get_all_pages(f"repos/{owner}/{repo}/commits", params={"per_page": 100})

    def get_repo_contributors(self, owner: str, repo: str) -> list[dict[str, Any]]:
        return self.get_all_pages(f"repos/{owner}/{repo}/contributors", params={"per_page": 100})

    def get_rate_limit(self) -> RateLimitInfo:
        response = self.get("rate_limit", use_cache=False)
        data = response.json()
        core = data.get("resources", {}).get("core", {})
        return RateLimitInfo(
            limit=core.get("limit", 0),
            remaining=core.get("remaining", 0),
            reset=core.get("reset", 0),
            used=core.get("used", 0),
        )
