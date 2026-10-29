
"""
RepoMind-AI Architecture Preview Router.

Builds a lightweight repository structure preview using the GitHub API.
Component relationships are inferred from file paths, not verified imports.
"""

import os
import re
from collections import Counter
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from github import Github
from github.GithubException import (
    GithubException,
    RateLimitExceededException,
)

router = APIRouter(tags=["architecture-preview"])

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "coverage",
    "vendor",
}

MAX_TREE_ITEMS = 1500


class PreviewRequest(BaseModel):
    repository: str = Field(
        min_length=1,
        max_length=500,
        description="GitHub repository URL or owner/repository.",
    )


def parse_repo(value: str) -> tuple[str, str]:
    """Parse a GitHub URL or owner/repository string."""
    value = value.strip()

    if not value:
        raise HTTPException(
            status_code=400,
            detail="Enter a GitHub URL or owner/repository.",
        )

    if value.startswith("http://"):
        raise HTTPException(
            status_code=400,
            detail="Use an HTTPS GitHub URL.",
        )

    if value.startswith("https://"):
        parsed = urlparse(value)

        if (parsed.hostname or "").lower() not in {
            "github.com",
            "www.github.com",
        }:
            raise HTTPException(
                status_code=400,
                detail="URL must point to github.com.",
            )

        parts = [
            part
            for part in parsed.path.strip("/").split("/")
            if part
        ]
    else:
        parts = [
            part
            for part in value.strip("/").split("/")
            if part
        ]

    if len(parts) != 2:
        raise HTTPException(
            status_code=400,
            detail="Enter a GitHub URL or owner/repository.",
        )

    owner, name = parts

    if name.lower().endswith(".git"):
        name = name[:-4]

    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub owner.",
        )

    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise HTTPException(
            status_code=400,
            detail="Invalid repository name.",
        )

    return owner, name


@router.post("/architecture-preview")
def architecture_preview(request: PreviewRequest):
    """Return a structural preview of a public or authorized repository."""
    owner, name = parse_repo(request.repository)

    token = os.getenv("GITHUB_TOKEN")
    client = Github(token) if token else Github()

    try:
        repo = client.get_repo(f"{owner}/{name}")
        branch = repo.default_branch

        tree = repo.get_git_tree(
            branch,
            recursive=True,
        ).tree

        all_files = [
            item.path
            for item in tree
            if item.type == "blob"
            and not any(
                part in SKIP_DIRS
                for part in item.path.split("/")
            )
        ]

        files = all_files[:MAX_TREE_ITEMS]

        if not files:
            raise HTTPException(
                status_code=422,
                detail="No repository files were found.",
            )

        extensions = Counter()
        top_dirs = Counter()

        for path in files:
            base = path.rsplit("/", 1)[-1]

            if "." in base:
                extensions[
                    base.rsplit(".", 1)[-1].lower()
                ] += 1
            else:
                extensions["(no extension)"] += 1

            if "/" in path:
                top_dirs[path.split("/", 1)[0]] += 1

        component_specs = [
            (
                "frontend",
                "Frontend / UI",
                r"(^|/)(frontend|client|ui|web|src/components)(/|$)|\.(html|css|jsx|tsx|vue)$",
            ),
            (
                "backend",
                "Backend / API",
                r"(^|/)(backend|server|api|routes|controllers)(/|$)|(^|/)(main|app)\.py$",
            ),
            (
                "ai",
                "AI / ML",
                r"(^|/)(ai|ml|models|agents|llm)(/|$)|(^|/)[^/]*(openai|llm|agent)[^/]*\.(py|ts|js)$",
            ),
            (
                "database",
                "Data / Database",
                r"(^|/)(models?|schemas?|migrations?|database)(/|$)|\.(sql|prisma)$|(^|/)schema\.",
            ),
            (
                "tests",
                "Tests",
                r"(^|/)(tests?|spec)(/|$)|(^|/)[^/]*_test\.py$|(^|/)[^/]*\.(test|spec)\.[^/]+$",
            ),
            (
                "config",
                "Configuration",
                r"(^|/)(config|\.github)(/|$)|(^|/)(pyproject\.toml|package\.json|requirements[^/]*\.txt|dockerfile|docker-compose[^/]*\.ya?ml|\.env\.example)$",
            ),
        ]

        nodes = [
            {
                "data": {
                    "id": "repo",
                    "label": repo.full_name,
                    "kind": "repository",
                }
            }
        ]

        edges = []
        detected = []

        for node_id, label, pattern in component_specs:
            matches = [
                path
                for path in files
                if re.search(pattern, path, re.IGNORECASE)
            ]

            if matches:
                detected.append((node_id, label, matches))

        for node_id, label, matches in detected:
            nodes.append(
                {
                    "data": {
                        "id": node_id,
                        "label": f"{label}\n{len(matches)} files",
                        "kind": "component",
                    }
                }
            )

            edges.append(
                {
                    "data": {
                        "id": f"repo-{node_id}",
                        "source": "repo",
                        "target": node_id,
                        "label": "contains",
                        "kind": "inferred",
                    }
                }
            )

        if not detected:
            nodes.append(
                {
                    "data": {
                        "id": "source",
                        "label": "Repository files",
                        "kind": "component",
                    }
                }
            )

            edges.append(
                {
                    "data": {
                        "id": "repo-source",
                        "source": "repo",
                        "target": "source",
                        "label": "contains",
                        "kind": "inferred",
                    }
                }
            )

        languages = dict(extensions.most_common(8))
        component_names = [
            label for _, label, _ in detected
        ]

        summary = (
            f"{repo.full_name} contains {len(files)} indexed files "
            f"on its default branch ({branch}). "
            f"Detected areas: "
            f"{', '.join(component_names) if component_names else 'general repository files'}. "
            f"Common file extensions: "
            f"{', '.join(f'{ext} ({count})' for ext, count in languages.items())}. "
            "This is a fast structural preview; connections between "
            "components have not been verified through code imports "
            "or runtime analysis."
        )

        return {
            "repository": repo.full_name,
            "url": repo.html_url,
            "branch": branch,
            "file_count": len(files),
            "truncated": len(all_files) > MAX_TREE_ITEMS,
            "languages_by_extension": languages,
            "top_directories": dict(top_dirs.most_common(10)),
            "summary": summary,
            "nodes": nodes,
            "edges": edges,
        }

    except HTTPException:
        raise

    except RateLimitExceededException as exc:
        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit reached. Try again later.",
        ) from exc

    except GithubException as exc:
        if exc.status == 404:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Repository not found or not accessible. "
                    "Private repositories require authorized access."
                ),
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="GitHub could not provide the repository tree.",
        ) from exc

    finally:
        client.close()
