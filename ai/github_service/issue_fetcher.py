import logging

from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class IssueFetcher:
    """Fetch GitHub issues from a repository."""

    def __init__(self, client: GitHubClient | None = None):
        self.client = client or GitHubClient()

    def fetch(self, owner: str, repo: str, limit: int = 100):
        """
        Fetch issues from the repository.

        Pull requests are excluded because GitHub's
        issues endpoint can also return pull requests.
        """

        repository = self.client.get_repository(owner, repo)
        issues = []

        for issue in repository.get_issues(state="all"):
            # GitHub represents pull requests as issues too.
            if issue.pull_request is not None:
                continue

            issues.append(
                {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body or "",
                    "state": issue.state,
                    "author": (
                        issue.user.login
                        if issue.user
                        else None
                    ),
                    "labels": [
                        label.name
                        for label in issue.labels
                    ],
                    "comments": issue.comments,
                    "created_at": (
                        issue.created_at.isoformat()
                        if issue.created_at
                        else None
                    ),
                    "updated_at": (
                        issue.updated_at.isoformat()
                        if issue.updated_at
                        else None
                    ),
                    "url": issue.html_url,
                }
            )

            if len(issues) >= limit:
                break

        logger.info(
            "Fetched %d issues",
            len(issues),
        )

        return issues