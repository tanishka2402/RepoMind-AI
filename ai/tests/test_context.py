from context.context_builder import ContextBuilder
from context.preprocessor import SourcePreprocessor


def test_preprocessor_handles_empty_source_files():
    preprocessor = SourcePreprocessor()

    result = preprocessor.process([])

    assert "No source files were collected" in result


def test_preprocessor_includes_file_path():
    preprocessor = SourcePreprocessor()

    source_files = [
        {
            "path": "index.html",
            "content": "<html><body>Hello</body></html>",
        }
    ]

    result = preprocessor.process(source_files)

    assert "FILE: index.html" in result
    assert "LANGUAGE: HTML" in result
    assert "Hello" in result


def test_preprocessor_detects_python():
    preprocessor = SourcePreprocessor()

    source_files = [
        {
            "path": "main.py",
            "content": "print('hello')",
        }
    ]

    result = preprocessor.process(source_files)

    assert "FILE: main.py" in result
    assert "LANGUAGE: Python" in result


def test_preprocessor_truncates_large_file():
    preprocessor = SourcePreprocessor(
        max_chars=10_000,
        max_file_chars=100,
    )

    source_files = [
        {
            "path": "large.py",
            "content": "x" * 500,
        }
    ]

    result = preprocessor.process(source_files)

    assert "FILE: large.py" in result
    assert "FILE TRUNCATED" in result


def test_context_builder_requires_repository_data():
    builder = ContextBuilder()

    try:
        builder.build({})
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_context_builder_contains_repository_facts():
    builder = ContextBuilder()

    repository_data = {
        "name": "Spoon-Knife",
        "full_name": "octocat/Spoon-Knife",
        "owner": "octocat",
        "description": "A test repository",
        "default_branch": "main",
        "stars": 10,
        "forks": 5,
        "watchers": 3,
        "open_issues": 2,
        "languages": {
            "HTML": 1000,
            "CSS": 500,
        },
        "topics": ["example"],
        "files": ["README.md", "index.html"],
        "branches": ["main"],
        "issues": [],
        "pull_requests": [],
        "source_files": [
            {
                "path": "index.html",
                "content": "<html>Hello</html>",
            }
        ],
    }

    result = builder.build(repository_data)

    assert "REPOSITORY FACTS" in result
    assert "octocat/Spoon-Knife" in result
    assert "README.md" in result
    assert "FILE: index.html" in result
    assert "<html>Hello</html>" in result
