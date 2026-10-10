"""
RepoMind-AI GitHub Client

Provides authenticated access to the GitHub API.

The GitHub token is loaded explicitly from:

    RepoMind-AI/ai/.env

This avoids relying on the current working directory.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from github import Github
from github.GithubException import (
    BadCredentialsException,
    RateLimitExceededException,
)


# ---------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------

# github_client.py is located at:
#
# RepoMind-AI/
# └── ai/
#     └── github_service/
#         └── github_client.py
#
# Therefore:
# parent      -> github_service/
# parent      -> ai/
AI_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = AI_DIR / ".env"

# Explicitly load ai/.env.
#
# override=True is intentional here because an incorrect/stale
# GITHUB_TOKEN in the shell environment should not silently override
# the token configured for RepoMind-AI.
load_dotenv(ENV_FILE, override=True)


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""


class GitHubAuthenticationError(GitHubClientError):
    """Raised when GitHub authentication fails."""


class GitHubRateLimitError(GitHubClientError):
    """Raised when GitHub API rate limit is exceeded."""


# ---------------------------------------------------------------------
# GitHub client
# ---------------------------------------------------------------------


class GitHubClient:
    """
    Reusable GitHub API client.

    The client uses GITHUB_TOKEN from ai/.env when available.
    """

    def __init__(self, token=None):
        """
        Initialize the GitHub client.

        Parameters
        ----------
        token:
            Optional GitHub token. If not provided, GITHUB_TOKEN
            from ai/.env is used.
        """

        self.token = token or os.getenv("GITHUB_TOKEN")

        if self.token:
            logger.info("Using authenticated GitHub client.")

            # PyGithub's current authentication API.
            #
            # This avoids the deprecated:
            # Github(login_or_token)
            try:
                from github import Auth

                self.client = Github(
                    auth=Auth.Token(self.token)
                )

            except ImportError:
                # Compatibility fallback for older PyGithub versions.
                self.client = Github(self.token)

        else:
            logger.warning(
                "GITHUB_TOKEN not found. "
                "Using unauthenticated GitHub access."
            )

            self.client = Github()

    # -----------------------------------------------------------------
    # Repository
    # -----------------------------------------------------------------

    def get_repository(self, owner, repo):
        """
        Return a GitHub repository object.

        Parameters
        ----------
        owner:
            GitHub repository owner.

        repo:
            Repository name.
        """

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