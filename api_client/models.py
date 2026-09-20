from datetime import datetime

from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
    login: str
    id: int
    name: str | None = None
    email: str | None = None
    public_repos: int
    followers: int
    following: int
    created_at: datetime
    updated_at: datetime
    html_url: str
    avatar_url: str
    bio: str | None = None
    company: str | None = None
    location: str | None = None


class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    description: str | None = None
    private: bool
    html_url: str
    clone_url: str
    language: str | None = None
    stargazers_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    default_branch: str
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None = None
    size: int
    topics: list[str] = Field(default_factory=list)


class GitHubCommitStats(BaseModel):
    total: int
    additions: int
    deletions: int


class RepositoryStats(BaseModel):
    repository: GitHubRepository
    commit_stats: GitHubCommitStats | None = None
    contributor_count: int = 0


class UserStats(BaseModel):
    user: GitHubUser
    repositories: list[RepositoryStats]
    total_repos: int
    total_stars: int
    total_forks: int
    total_commits: int
    total_additions: int
    total_deletions: int
    languages: dict[str, int]


class RateLimitInfo(BaseModel):
    limit: int
    remaining: int
    reset: int
    used: int
