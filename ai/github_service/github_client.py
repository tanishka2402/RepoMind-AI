import logging
import os
from dotenv import load_dotenv
from github import Github
from github.GithubException import (
    BadCredentialsException,
    RateLimitExceededException,
)

load_dotenv()

logger = logging.getLogger(__name__)


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""


class GitHubAuthenticationError(GitHubClientError):
    """Raised when GitHub authentication fails."""


class GitHubRateLimitError(GitHubClientError):
    """Raised when GitHub API rate limit is exceeded."""


class GitHubClient:
    """Reusable GitHub API client."""

    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")

        if self.token:
            logger.info("Using authenticated GitHub client.")
            self.client = Github(self.token)
        else:
            logger.warning(
                "GITHUB_TOKEN not found. "
                "Using unauthenticated GitHub access."
            )
            self.client = Github()

    def get_repository(self, owner, repo):
        """Return a GitHub repository object."""

        try:
            logger.info(
                "Fetching repository: %s/%s",
                owner,
                repo,
            )

            return self.client.get_repo(
                f"{owner}/{repo}"
            )

        except BadCredentialsException as exc:
            raise GitHubAuthenticationError(
                "Invalid GitHub token."
            ) from exc

        except RateLimitExceededException as exc:
            raise GitHubRateLimitError(
                "GitHub API rate limit exceeded."
            ) from exc

        except Exception as exc:
            raise GitHubClientError(
                f"Unable to fetch {owner}/{repo}: {exc}"
            ) from exc