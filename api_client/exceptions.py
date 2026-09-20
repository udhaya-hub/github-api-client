class APIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        return " ".join(parts)


class APIAuthError(APIError):
    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message, status_code, response_body)


class APIRateLimitError(APIError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: int | None = None,
        response_body: str | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message, status_code, response_body)
        self.retry_after = retry_after


class APINotFoundError(APIError):
    def __init__(
        self,
        message: str = "Resource not found",
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message, status_code, response_body)


class APIServerError(APIError):
    def __init__(
        self,
        message: str = "Server error",
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message, status_code, response_body)


class APITimeoutError(APIError):
    def __init__(
        self,
        message: str = "Request timed out",
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message, status_code, response_body)


class APIValidationError(APIError):
    def __init__(
        self,
        message: str = "Response validation failed",
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message, status_code, response_body)


class CacheError(Exception):
    pass
