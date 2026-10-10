from typing import Any, Dict, List, Optional, Tuple

from github.GithubException import GithubException

from github_service.github_client import GitHubClient

class RepositoryURLParser:
    """Parse GitHub repository URLs or owner/name strings."""

    @staticmethod
    def parse(repository: str) -> tuple[str, str]:
        """Return (owner, repo_name) from a GitHub URL or short form."""
        return RepositoryFetcher._parse_repository(repository)
class RepositoryFetcher:
    """
    Fetches repository metadata, files, source files, issues,
    pull requests, and branches from GitHub.

    The returned data is intentionally normalized so downstream
    AI and repository-intelligence modules receive clean data.
    """

    MAX_FILES = 100
    MAX_FILE_SIZE = 100_000

    SOURCE_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".h",
        ".cpp",
        ".cc",
        ".cxx",
        ".hpp",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".kts",
        ".cs",
        ".scala",
        ".sh",
        ".bash",
        ".zsh",
        ".sql",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".vue",
    }

    DOCUMENTATION_EXTENSIONS = {
        ".md",
        ".mdx",
        ".rst",
        ".txt",
    }

    CONFIGURATION_FILES = {
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "pipfile",
        "pipfile.lock",
        "setup.py",
        "setup.cfg",
        "cargo.toml",
        "cargo.lock",
        "go.mod",
        "go.sum",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "composer.json",
        "gemfile",
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        ".env.example",
        ".gitignore",
        "tsconfig.json",
        "vite.config.js",
        "vite.config.ts",
        "webpack.config.js",
        "webpack.config.ts",
    }

    IGNORE_DIRECTORIES = {
        ".git",
        ".github",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        ".env",
        "dist",
        "build",
        ".idea",
        ".vscode",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        ".next",
        ".nuxt",
        "target",
    }

    def __init__(self, github_client: Optional[GitHubClient] = None):
        self.github_client = github_client or GitHubClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self, repository: str) -> Dict[str, Any]:
        """
        Fetch and normalize a GitHub repository.

        Accepts:
            owner/repository
            https://github.com/owner/repository
            https://github.com/owner/repository.git
        """

        owner, repo_name = self._parse_repository(repository)

        repo = self.github_client.get_repository(
            owner=owner,
            repo=repo_name,
        )

        files = self._get_files(repo)
        source_files = self._get_source_files(repo)
        issues = self._get_issues(repo)
        pull_requests = self._get_pull_requests(repo)
        branches = self._get_branches(repo)

        return {
            "name": repo.name,
            "full_name": repo.full_name,
            "owner": owner,
            "description": repo.description or "",
            "default_branch": repo.default_branch,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "watchers": repo.watchers_count,
            "open_issues": repo.open_issues_count,
            "url": repo.html_url,
            "topics": self._get_topics(repo),
            "languages": self._get_languages(repo),
            "files": files,
            "source_files": source_files,
            "issues": issues,
            "pull_requests": pull_requests,
            "branches": branches,
        }

    # ------------------------------------------------------------------
    # Repository parsing
    # ------------------------------------------------------------------

    def _parse_repository(self, repository: str) -> Tuple[str, str]:
        repository = repository.strip()

        if repository.startswith("https://github.com/"):
            repository = repository[len("https://github.com/"):]

        elif repository.startswith("http://github.com/"):
            repository = repository[len("http://github.com/"):]

        repository = repository.rstrip("/")

        if repository.endswith(".git"):
            repository = repository[:-4]

        parts = repository.split("/")

        if len(parts) != 2:
            raise ValueError(
                "Repository must be in the form 'owner/repository' "
                "or a GitHub repository URL."
            )

        owner, repo_name = parts

        if not owner or not repo_name:
            raise ValueError(
                "Both GitHub owner and repository name are required."
            )

        return owner, repo_name

    # ------------------------------------------------------------------
    # Repository metadata
    # ------------------------------------------------------------------

    def _get_topics(self, repo) -> List[str]:
        try:
            return list(repo.get_topics() or [])
        except Exception:
            return []

    def _get_languages(self, repo) -> Dict[str, int]:
        """
        Return only actual GitHub language statistics.

        PyGithub may expose a metadata field named 'url' alongside
        language byte counts depending on the response structure.
        That URL is not a programming language and must never enter
        the repository language analysis.
        """

        try:
            languages = repo.get_languages() or {}
        except Exception:
            return {}

        clean_languages: Dict[str, int] = {}

        for language, byte_count in languages.items():
            if not isinstance(language, str):
                continue

            language = language.strip()

            if not language:
                continue

            # Explicitly reject API metadata accidentally returned
            # alongside the language statistics.
            if language.lower() in {
                "url",
                "links",
                "metadata",
            }:
                continue

            # Language byte counts should be numeric.
            if isinstance(byte_count, bool):
                continue

            if not isinstance(byte_count, (int, float)):
                continue

            clean_languages[language] = int(byte_count)

        return clean_languages

    # ------------------------------------------------------------------
    # Repository files
    # ------------------------------------------------------------------

    def _get_files(self, repo) -> List[Dict[str, Any]]:
        """
        Collect top-level repository files/directories.

        This is intentionally limited because the full source tree
        is collected separately by _get_source_files().
        """

        files: List[Dict[str, Any]] = []

        try:
            contents = repo.get_contents("")
        except GithubException:
            return files
        except Exception:
            return files

        for item in contents[: self.MAX_FILES]:
            files.append(
                {
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": getattr(item, "size", 0),
                }
            )

        return files

    # ------------------------------------------------------------------
    # Source files
    # ------------------------------------------------------------------

    def _get_source_files(self, repo) -> List[Dict[str, Any]]:
        """
        Recursively collect actual source files.

        Documentation files such as README.md are deliberately
        excluded from source_files.

        This keeps:
            source_files  -> implementation/code
            documentation -> README/docs
        """

        source_files: List[Dict[str, Any]] = []

        try:
            self._scan_directory(
                repo=repo,
                path="",
                source_files=source_files,
            )
        except Exception:
            return source_files

        return source_files[: self.MAX_FILES]

    def _scan_directory(
        self,
        repo,
        path: str,
        source_files: List[Dict[str, Any]],
    ) -> None:
        if len(source_files) >= self.MAX_FILES:
            return

        try:
            contents = repo.get_contents(path)
        except Exception:
            return

        for item in contents:
            if len(source_files) >= self.MAX_FILES:
                return

            item_path = item.path
            item_name = item.name

            if self._should_ignore_path(item_path):
                continue

            if item.type == "dir":
                self._scan_directory(
                    repo=repo,
                    path=item_path,
                    source_files=source_files,
                )
                continue

            if item.type != "file":
                continue

            if not self._is_source_file(item_name):
                continue

            size = getattr(item, "size", 0) or 0

            if size > self.MAX_FILE_SIZE:
                continue

            try:
                decoded_content = item.decoded_content
                content = decoded_content.decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                continue

            source_files.append(
                {
                    "name": item_name,
                    "path": item_path,
                    "type": "file",
                    "size": size,
                    "content": content,
                }
            )

    def _is_source_file(self, filename: str) -> bool:
        """
        Decide whether a file contains implementation/source code.
        """

        lower_name = filename.lower()

        # README/docs are never source files.
        if lower_name.startswith("readme"):
            return False

        extension = self._get_extension(filename)

        if extension in self.DOCUMENTATION_EXTENSIONS:
            return False

        # Configuration files are handled separately by repository
        # intelligence and should not be treated as source code.
        if lower_name in {
            name.lower()
            for name in self.CONFIGURATION_FILES
        }:
            return False

        return extension in self.SOURCE_EXTENSIONS

    # ------------------------------------------------------------------
    # Path filtering
    # ------------------------------------------------------------------

    def _should_ignore_path(self, path: str) -> bool:
        parts = path.replace("\\", "/").split("/")

        for part in parts:
            if part in self.IGNORE_DIRECTORIES:
                return True

        return False

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    def _get_extension(self, filename: str) -> str:
        filename = filename.lower()

        if "." not in filename:
            return ""

        return "." + filename.rsplit(".", 1)[1]

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------

    def _get_issues(self, repo) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        try:
            for issue in repo.get_issues(
                state="all",
                sort="updated",
                direction="desc",
            ):
                # GitHub issues API also returns pull requests.
                if getattr(issue, "pull_request", None):
                    continue

                issues.append(
                    {
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "url": issue.html_url,
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
                    }
                )

                if len(issues) >= self.MAX_FILES:
                    break

        except Exception:
            return issues

        return issues

    # ------------------------------------------------------------------
    # Pull requests
    # ------------------------------------------------------------------

    def _get_pull_requests(self, repo) -> List[Dict[str, Any]]:
        pull_requests: List[Dict[str, Any]] = []

        try:
            for pr in repo.get_pulls(
                state="all",
                sort="updated",
                direction="desc",
            ):
                pull_requests.append(
                    {
                        "number": pr.number,
                        "title": pr.title,
                        "state": pr.state,
                        "url": pr.html_url,
                        "created_at": (
                            pr.created_at.isoformat()
                            if pr.created_at
                            else None
                        ),
                        "updated_at": (
                            pr.updated_at.isoformat()
                            if pr.updated_at
                            else None
                        ),
                    }
                )

                if len(pull_requests) >= self.MAX_FILES:
                    break

        except Exception:
            return pull_requests

        return pull_requests

    # ------------------------------------------------------------------
    # Branches
    # ------------------------------------------------------------------

    def _get_branches(self, repo) -> List[str]:
        branches: List[str] = []

        try:
            for branch in repo.get_branches():
                branches.append(branch.name)

                if len(branches) >= self.MAX_FILES:
                    break

        except Exception:
            return branches

        return branches