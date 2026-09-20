from datetime import datetime

from api_client.models import (
    GitHubCommitStats,
    GitHubRepository,
    GitHubUser,
    RateLimitInfo,
    RepositoryStats,
    UserStats,
)


def test_github_user_model():
    data = {
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
    user = GitHubUser(**data)
    assert user.login == "octocat"
    assert user.id == 1
    assert user.name == "The Octocat"
    assert isinstance(user.created_at, datetime)


def test_github_user_model_optional_fields():
    data = {
        "login": "octocat",
        "id": 1,
        "public_repos": 8,
        "followers": 100,
        "following": 50,
        "created_at": "2011-01-25T18:44:36Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/octocat",
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
    }
    user = GitHubUser(**data)
    assert user.name is None
    assert user.email is None
    assert user.bio is None


def test_github_repository_model():
    data = {
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
    }
    repo = GitHubRepository(**data)
    assert repo.name == "Hello-World"
    assert repo.language == "Python"
    assert repo.stargazers_count == 10
    assert repo.topics == ["python", "tutorial"]


def test_github_repository_model_default_topics():
    data = {
        "id": 1,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "private": False,
        "html_url": "https://github.com/octocat/Hello-World",
        "clone_url": "https://github.com/octocat/Hello-World.git",
        "stargazers_count": 10,
        "forks_count": 5,
        "watchers_count": 10,
        "open_issues_count": 2,
        "default_branch": "main",
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "size": 100,
    }
    repo = GitHubRepository(**data)
    assert repo.topics == []


def test_github_commit_stats_model():
    stats = GitHubCommitStats(total=5, additions=100, deletions=10)
    assert stats.total == 5
    assert stats.additions == 100
    assert stats.deletions == 10


def test_rate_limit_info_model():
    rate_limit = RateLimitInfo(limit=5000, remaining=4999, reset=1234567890, used=1)
    assert rate_limit.limit == 5000
    assert rate_limit.remaining == 4999
    assert rate_limit.reset == 1234567890
    assert rate_limit.used == 1


def test_repository_stats_model():
    repo_data = {
        "id": 1,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "private": False,
        "html_url": "https://github.com/octocat/Hello-World",
        "clone_url": "https://github.com/octocat/Hello-World.git",
        "stargazers_count": 10,
        "forks_count": 5,
        "watchers_count": 10,
        "open_issues_count": 2,
        "default_branch": "main",
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "size": 100,
    }
    repo = GitHubRepository(**repo_data)
    repo_stats = RepositoryStats(repository=repo, contributor_count=3)
    assert repo_stats.repository.name == "Hello-World"
    assert repo_stats.contributor_count == 3
    assert repo_stats.commit_stats is None


def test_user_stats_model():
    user_data = {
        "login": "octocat",
        "id": 1,
        "public_repos": 8,
        "followers": 100,
        "following": 50,
        "created_at": "2011-01-25T18:44:36Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/octocat",
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
    }
    user = GitHubUser(**user_data)

    repo_data = {
        "id": 1,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "private": False,
        "html_url": "https://github.com/octocat/Hello-World",
        "clone_url": "https://github.com/octocat/Hello-World.git",
        "stargazers_count": 10,
        "forks_count": 5,
        "watchers_count": 10,
        "open_issues_count": 2,
        "default_branch": "main",
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "size": 100,
    }
    repo = GitHubRepository(**repo_data)
    repo_stats = RepositoryStats(repository=repo)

    stats = UserStats(
        user=user,
        repositories=[repo_stats],
        total_repos=1,
        total_stars=10,
        total_forks=5,
        total_commits=5,
        total_additions=100,
        total_deletions=10,
        languages={"Python": 1},
    )
    assert stats.user.login == "octocat"
    assert stats.total_repos == 1
    assert stats.languages == {"Python": 1}
