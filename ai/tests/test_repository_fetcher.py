import pytest

from github_service.repository_fetcher import RepositoryURLParser


def test_parse_owner_and_repo():
    owner, repo = RepositoryURLParser.parse("octocat/Hello-World")

    assert owner == "octocat"
    assert repo == "Hello-World"


def test_parse_https_github_url():
    owner, repo = RepositoryURLParser.parse(
        "https://github.com/octocat/Hello-World"
    )

    assert owner == "octocat"
    assert repo == "Hello-World"


def test_parse_github_url_with_git_suffix():
    owner, repo = RepositoryURLParser.parse(
        "https://github.com/octocat/Hello-World.git"
    )

    assert owner == "octocat"
    assert repo == "Hello-World"


def test_parse_www_github_url():
    owner, repo = RepositoryURLParser.parse(
        "https://www.github.com/octocat/Hello-World"
    )

    assert owner == "octocat"
    assert repo == "Hello-World"


def test_reject_empty_repository():
    with pytest.raises(ValueError):
        RepositoryURLParser.parse("")


def test_reject_invalid_repository_format():
    with pytest.raises(ValueError):
        RepositoryURLParser.parse("octocat")


def test_reject_non_github_url():
    with pytest.raises(ValueError):
        RepositoryURLParser.parse(
            "https://gitlab.com/octocat/Hello-World"
        )
