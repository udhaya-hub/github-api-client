import pytest


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token_123")
    monkeypatch.setenv("GITHUB_API_BASE_URL", "https://api.github.com")
    monkeypatch.setenv("REQUEST_TIMEOUT", "30")
    monkeypatch.setenv("MAX_RETRIES", "3")
    monkeypatch.setenv("RETRY_BASE_DELAY", "1")
    monkeypatch.setenv("RATE_LIMIT_THRESHOLD", "10")
    monkeypatch.setenv("CACHE_TTL", "3600")
    monkeypatch.setenv("CACHE_DB_PATH", ":memory:")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


@pytest.fixture
def mock_user_response():
    return {
        "login": "octocat",
        "id": 1,
        "name": "The Octocat",
        "email": "octocat@github.com",
        "public_repos": 8,
        "followers": 100,
        "following": 50,
        "created_at": "2011-01-25T18:44:36Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/octocat",
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "bio": "GitHub mascot",
        "company": "GitHub",
        "location": "San Francisco",
    }


@pytest.fixture
def mock_repos_response():
    return [
        {
            "id": 1,
            "name": "Hello-World",
            "full_name": "octocat/Hello-World",
            "description": "My first repository",
            "private": False,
            "html_url": "https://github.com/octocat/Hello-World",
            "clone_url": "https://github.com/octocat/Hello-World.git",
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 5,
            "watchers_count": 10,
            "open_issues_count": 2,
            "default_branch": "main",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "pushed_at": "2024-01-01T00:00:00Z",
            "size": 100,
            "topics": ["python", "tutorial"],
        },
        {
            "id": 2,
            "name": "Another-Repo",
            "full_name": "octocat/Another-Repo",
            "description": "Another repo",
            "private": False,
            "html_url": "https://github.com/octocat/Another-Repo",
            "clone_url": "https://github.com/octocat/Another-Repo.git",
            "language": "JavaScript",
            "stargazers_count": 5,
            "forks_count": 2,
            "watchers_count": 5,
            "open_issues_count": 1,
            "default_branch": "main",
            "created_at": "2021-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "pushed_at": "2024-01-01T00:00:00Z",
            "size": 50,
            "topics": ["javascript"],
        },
    ]


@pytest.fixture
def mock_commits_response():
    return [
        {
            "sha": "abc123",
            "commit": {"message": "Initial commit"},
            "stats": {"additions": 100, "deletions": 10},
        },
        {
            "sha": "def456",
            "commit": {"message": "Add feature"},
            "stats": {"additions": 50, "deletions": 5},
        },
    ]


@pytest.fixture
def mock_contributors_response():
    return [
        {"login": "octocat", "contributions": 10},
        {"login": "user2", "contributions": 5},
    ]
