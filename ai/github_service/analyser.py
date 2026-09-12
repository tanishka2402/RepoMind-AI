import logging
from typing import Any

from .branch_fetcher import BranchFetcher
from .github_client import GitHubClient
from .issue_fetcher import IssueFetcher
from .pr_fetcher import PullRequestFetcher
from .repository_fetcher import RepositoryFetcher, RepositoryURLParser

logger = logging.getLogger(__name__)


class GitHubRepositoryAnalyzer:
    """
    Collects all relevant GitHub repository information.

    This class acts as the single entry point for the GitHub
    data collection layer.
    """

    def __init__(self, github_client: GitHubClient | None = None):
        self.github_client = github_client or GitHubClient()

        self.repository_fetcher = RepositoryFetcher(
            self.github_client
        )

        self.issue_fetcher = IssueFetcher(
            self.github_client
        )

        self.pr_fetcher = PullRequestFetcher(
            self.github_client
        )

        self.branch_fetcher = BranchFetcher(
            self.github_client
        )

    def analyze(
        self,
        repository_url: str,
    ) -> dict[str, Any]:
        """
        Collect complete repository context.

        Args:
            repository_url: GitHub repository URL.

        Returns:
            Complete JSON-serializable repository context.
        """

        owner, repo_name = RepositoryURLParser.parse(
            repository_url
        )

        logger.info(
            "Starting repository analysis: %s/%s",
            owner,
            repo_name,
        )

        repository_data = self.repository_fetcher.fetch(
            repository_url
        )

        issues = self.issue_fetcher.fetch(
            owner,
            repo_name,
        )

        pull_requests = self.pr_fetcher.fetch(
            owner,
            repo_name,
        )

        branches = self.branch_fetcher.fetch(
            owner,
            repo_name,
        )

        result = {
            **repository_data,
            "issues": issues,
            "pull_requests": pull_requests,
            "branches": branches,
        }

        logger.info(
            "Repository data collection completed."
        )

        return result