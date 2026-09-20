import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from api_client.cache import get_cache
from api_client.client import GitHubClient
from api_client.exceptions import (
    APIAuthError,
    APIError,
    APINotFoundError,
    APIRateLimitError,
)
from api_client.logging_config import get_logger, setup_logging
from api_client.models import GitHubRepository, GitHubUser, RepositoryStats, UserStats

logger = get_logger(__name__)
console = Console()


def create_user_stats(username: str) -> UserStats:
    with GitHubClient() as client:
        logger.info("Fetching user: %s", username)
        user_data = client.get_user(username)
        user = GitHubUser(**user_data)

        logger.info("Fetching repositories for user: %s", username)
        repos_data = client.get_user_repos(username)

        repositories: list[RepositoryStats] = []
        total_stars = 0
        total_forks = 0
        total_commits = 0
        total_additions = 0
        total_deletions = 0
        languages: dict[str, int] = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Processing {len(repos_data)} repositories...", total=len(repos_data))

            for repo_data in repos_data:
                repo = GitHubRepository(**repo_data)
                progress.update(task, description=f"Processing {repo.name}...")

                commits_data = client.get_repo_commits(username, repo.name)
                commit_count = len(commits_data)

                contributors_data = client.get_repo_contributors(username, repo.name)
                contributor_count = len(contributors_data)

                additions = sum(c.get("stats", {}).get("additions", 0) for c in commits_data if c.get("stats"))
                deletions = sum(c.get("stats", {}).get("deletions", 0) for c in commits_data if c.get("stats"))

                repo_stats = RepositoryStats(
                    repository=repo,
                    contributor_count=contributor_count,
                )
                repositories.append(repo_stats)

                total_stars += repo.stargazers_count
                total_forks += repo.forks_count
                total_commits += commit_count
                total_additions += additions
                total_deletions += deletions

                if repo.language:
                    languages[repo.language] = languages.get(repo.language, 0) + 1

                progress.advance(task)

        return UserStats(
            user=user,
            repositories=repositories,
            total_repos=len(repositories),
            total_stars=total_stars,
            total_forks=total_forks,
            total_commits=total_commits,
            total_additions=total_additions,
            total_deletions=total_deletions,
            languages=languages,
        )


def print_user_stats(stats: UserStats, output_format: str = "table") -> None:
    if output_format == "json":
        console.print_json(stats.model_dump_json(indent=2))
        return

    user = stats.user
    console.print(f"\n[bold cyan]User:[/bold cyan] {user.login} ({user.name or 'No name'})")
    console.print(f"[bold cyan]Bio:[/bold cyan] {user.bio or 'No bio'}")
    console.print(f"[bold cyan]Location:[/bold cyan] {user.location or 'Unknown'}")
    console.print(f"[bold cyan]Company:[/bold cyan] {user.company or 'Unknown'}")
    console.print(f"[bold cyan]Public Repos:[/bold cyan] {user.public_repos}")
    console.print(f"[bold cyan]Followers:[/bold cyan] {user.followers} | [bold cyan]Following:[/bold cyan] {user.following}")
    console.print(f"[bold cyan]Profile:[/bold cyan] {user.html_url}")

    console.print("\n[bold green]Repository Summary:[/bold green]")
    console.print(f"  Total Repositories: {stats.total_repos}")
    console.print(f"  Total Stars: {stats.total_stars}")
    console.print(f"  Total Forks: {stats.total_forks}")
    console.print(f"  Total Commits: {stats.total_commits}")
    console.print(f"  Total Additions: {stats.total_additions}")
    console.print(f"  Total Deletions: {stats.total_deletions}")

    if stats.languages:
        console.print("\n[bold yellow]Languages:[/bold yellow]")
        lang_table = Table(show_header=True, header_style="bold magenta")
        lang_table.add_column("Language")
        lang_table.add_column("Repositories", justify="right")
        for lang, count in sorted(stats.languages.items(), key=lambda x: x[1], reverse=True):
            lang_table.add_row(lang, str(count))
        console.print(lang_table)

    if stats.repositories:
        console.print("\n[bold green]Repositories:[/bold green]")
        repo_table = Table(show_header=True, header_style="bold magenta")
        repo_table.add_column("Name")
        repo_table.add_column("Description")
        repo_table.add_column("Language")
        repo_table.add_column("Stars", justify="right")
        repo_table.add_column("Forks", justify="right")
        repo_table.add_column("Issues", justify="right")
        repo_table.add_column("Contributors", justify="right")

        for rs in stats.repositories:
            repo = rs.repository
            repo_table.add_row(
                repo.name,
                (repo.description[:50] + "...") if repo.description and len(repo.description) > 50 else (repo.description or ""),
                repo.language or "-",
                str(repo.stargazers_count),
                str(repo.forks_count),
                str(repo.open_issues_count),
                str(rs.contributor_count),
            )
        console.print(repo_table)


def export_stats(stats: UserStats, output_path: Path, format: str) -> None:
    data = stats.model_dump(mode="json")
    if format == "json":
        output_path.write_text(json.dumps(data, indent=2, default=str))
    elif format == "csv":
        import csv
        with output_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Value"])
            writer.writerow(["user_login", stats.user.login])
            writer.writerow(["user_name", stats.user.name or ""])
            writer.writerow(["total_repos", stats.total_repos])
            writer.writerow(["total_stars", stats.total_stars])
            writer.writerow(["total_forks", stats.total_forks])
            writer.writerow(["total_commits", stats.total_commits])
            writer.writerow(["total_additions", stats.total_additions])
            writer.writerow(["total_deletions", stats.total_deletions])
            writer.writerow([])
            writer.writerow(["Repository", "Language", "Stars", "Forks", "Issues", "Contributors"])
            for rs in stats.repositories:
                writer.writerow([
                    rs.repository.name,
                    rs.repository.language or "",
                    rs.repository.stargazers_count,
                    rs.repository.forks_count,
                    rs.repository.open_issues_count,
                    rs.contributor_count,
                ])
    console.print(f"[green]Exported to {output_path}[/green]")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GitHub API Client - Fetch user and repository statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m api_client.cli --user octocat --action repo-stats
  python -m api_client.cli --user octocat --action repo-stats --format json
  python -m api_client.cli --user octocat --action repo-stats --output stats.json --format json
  python -m api_client.cli --user octocat --action rate-limit
  python -m api_client.cli --clear-cache
        """,
    )
    parser.add_argument("--user", "-u", help="GitHub username")
    parser.add_argument(
        "--action",
        "-a",
        choices=["repo-stats", "rate-limit"],
        default="repo-stats",
        help="Action to perform",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path (JSON or CSV)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the cache database",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable cache for this run",
    )

    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.clear_cache:
        count = get_cache().clear_all()
        console.print(f"[green]Cleared {count} cache entries[/green]")
        return 0

    if not args.user:
        args.user = get_settings().github_default_user
        console.print(
            f"[yellow]No --user supplied; using default GitHub user: {args.user}[/yellow]"
        )

    try:
        if args.action == "rate-limit":
            with GitHubClient() as client:
                rate_limit = client.get_rate_limit()
                console.print(f"Rate Limit: {rate_limit.remaining}/{rate_limit.limit}")
                console.print(f"Reset at: {rate_limit.reset}")
            return 0

        stats = create_user_stats(args.user)
        print_user_stats(stats, args.format)

        if args.output:
            export_format = "json" if args.output.suffix == ".json" else "csv"
            export_stats(stats, args.output, export_format)

        return 0

    except APIAuthError as e:
        logger.error("Authentication error: %s", e)
        console.print("[red]Authentication failed. Check your GitHub token in .env file.[/red]")
        return 1
    except APIRateLimitError as e:
        logger.error("Rate limit exceeded: %s", e)
        console.print("[red]Rate limit exceeded. Wait before retrying.[/red]")
        return 1
    except APINotFoundError as e:
        logger.error("User not found: %s", e)
        console.print(f"[red]User '{args.user}' not found.[/red]")
        return 1
    except APIError as e:
        logger.error("API error: %s", e)
        console.print(f"[red]API error: {e}[/red]")
        return 1
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
