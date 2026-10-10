"""
Repository Intelligence for RepoMind-AI.

This module builds a deterministic repository-level summary from the
data collected by RepositoryFetcher.

The goal is to help a user understand a GitHub repository without
having to read the entire codebase.

The module intentionally separates:

    Repository facts
        ↓
    Deterministic heuristics
        ↓
    Repository Intelligence Summary

It does not call an LLM and does not require external packages.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


# ============================================================
# LANGUAGE DETECTION
# ============================================================

LANGUAGE_EXTENSIONS: Dict[str, str] = {
    ".py": "Python",
    ".pyw": "Python",

    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",

    ".ts": "TypeScript",
    ".tsx": "TypeScript",

    ".java": "Java",

    ".c": "C",
    ".h": "C",

    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",

    ".cs": "C#",

    ".go": "Go",

    ".rs": "Rust",

    ".rb": "Ruby",

    ".php": "PHP",

    ".swift": "Swift",

    ".kt": "Kotlin",
    ".kts": "Kotlin",

    ".dart": "Dart",

    ".scala": "Scala",

    ".sh": "Shell",
    ".bash": "Shell",

    ".zsh": "Shell",

    ".ps1": "PowerShell",

    ".sql": "SQL",

    ".r": "R",

    ".lua": "Lua",

    ".pl": "Perl",

    ".ex": "Elixir",
    ".exs": "Elixir",

    ".erl": "Erlang",
    ".hrl": "Erlang",

    ".hs": "Haskell",

    ".fs": "F#",
    ".fsx": "F#",

    ".vue": "Vue",
    ".svelte": "Svelte",

    ".html": "HTML",
    ".htm": "HTML",

    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",

    ".xml": "XML",

    ".yaml": "YAML",
    ".yml": "YAML",

    ".json": "JSON",

    ".toml": "TOML",

    ".ini": "INI",

    ".md": "Markdown",
}


# These are documentation formats and should not be counted as
# normal application source code.
DOCUMENTATION_EXTENSIONS = {
    ".md",
    ".markdown",
    ".rst",
    ".adoc",
    ".asciidoc",
    ".txt",
}


# Configuration files should not normally be classified as source.
CONFIGURATION_FILENAMES = {
    ".env",
    ".env.example",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "makefile",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pipfile",
    "pipfile.lock",
    "cargo.toml",
    "cargo.lock",
    "go.mod",
    "go.sum",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}


# ============================================================
# TECHNOLOGY INDICATORS
# ============================================================

TECHNOLOGY_INDICATORS: Dict[str, Dict[str, List[str]]] = {
    "frontend": {
        "HTML": [".html", ".htm"],
        "CSS": [".css", ".scss", ".sass", ".less"],
        "JavaScript": [".js", ".jsx", ".mjs", ".cjs"],
        "TypeScript": [".ts", ".tsx"],
        "React": ["react", "react-dom"],
        "Next.js": ["next.config.js", "next.config.mjs"],
        "Vue": [".vue", "vue"],
        "Angular": ["angular.json", "@angular/core"],
        "Svelte": [".svelte", "svelte"],
    },

    "backend": {
        "Python": [".py"],
        "FastAPI": ["fastapi"],
        "Flask": ["flask"],
        "Django": ["django"],
        "Node.js": ["express", "node"],
        "Java": [".java"],
        "Spring": ["spring-boot", "springframework"],
        "PHP": [".php"],
        "Ruby": [".rb"],
        "Go": [".go"],
        "Rust": [".rs"],
    },

    "ai_ml": {
        "PyTorch": ["torch", "pytorch"],
        "TensorFlow": ["tensorflow"],
        "Transformers": ["transformers"],
        "Hugging Face": ["huggingface", "transformers"],
        "LangChain": ["langchain"],
        "CrewAI": ["crewai"],
        "OpenAI": ["openai"],
        "scikit-learn": ["sklearn", "scikit-learn"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
    },

    "database": {
        "SQLite": [".db", "sqlite", "sqlite3"],
        "PostgreSQL": ["postgres", "psycopg", "postgresql"],
        "MySQL": ["mysql", "pymysql"],
        "MongoDB": ["mongodb", "pymongo"],
        "Redis": ["redis"],
        "SQL": [".sql"],
    },

    "blockchain": {
        "Solidity": [".sol"],
        "Web3.py": ["web3"],
        "Ethereum": ["ethereum"],
        "Hardhat": ["hardhat"],
        "Foundry": ["foundry.toml"],
    },

    "testing": {
        "Pytest": ["pytest"],
        "Jest": ["jest"],
        "Vitest": ["vitest"],
        "Mocha": ["mocha"],
        "JUnit": ["junit"],
        "Playwright": ["playwright"],
        "Cypress": ["cypress"],
    },

    "devops": {
        "Docker": ["dockerfile", "docker-compose", "compose.yml"],
        "GitHub Actions": [".github/workflows"],
        "Kubernetes": [".yaml", ".yml", "kubernetes"],
        "Terraform": [".tf"],
        "Ansible": ["ansible"],
    },
}


# ============================================================
# SOURCE FILE EXTENSIONS
# ============================================================

SOURCE_EXTENSIONS = {
    extension
    for extension, language in LANGUAGE_EXTENSIONS.items()
    if language
    and language not in {
        "Markdown",
        "JSON",
        "YAML",
        "TOML",
        "INI",
        "XML",
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _safe_list(value: Any) -> List[Any]:
    """
    Convert common iterable/list-like values into a safe list.
    """
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    try:
        return list(value)
    except Exception:
        return []


def _path_from_item(item: Any) -> str:
    """
    Extract a repository file path from different possible formats.
    """
    if isinstance(item, str):
        return item

    if isinstance(item, dict):
        for key in (
            "path",
            "name",
            "filename",
            "file",
        ):
            value = item.get(key)

            if value:
                return str(value)

    return ""


def _content_from_item(item: Any) -> str:
    """
    Extract file content when available.
    """
    if not isinstance(item, dict):
        return ""

    for key in (
        "content",
        "text",
        "source",
        "decoded_content",
    ):
        value = item.get(key)

        if value is None:
            continue

        if isinstance(value, bytes):
            try:
                return value.decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                return ""

        return str(value)

    return ""


def _normalize_path(path: str) -> str:
    """
    Normalize repository paths for comparisons.
    """
    return path.strip().replace("\\", "/")


def _extension(path: str) -> str:
    """
    Return lowercase file extension.
    """
    return Path(path).suffix.lower()


def _filename(path: str) -> str:
    """
    Return lowercase basename.
    """
    return Path(path).name.lower()


def _contains_any(
    text: str,
    patterns: Iterable[str],
) -> bool:
    """
    Case-insensitive substring check.
    """
    text = text.lower()

    return any(
        pattern.lower() in text
        for pattern in patterns
    )


# ============================================================
# REPOSITORY INTELLIGENCE
# ============================================================


class RepositoryIntelligence:
    """
    Build a deterministic high-level understanding of a repository.
    """

    def __init__(
        self,
        repository_data: Dict[str, Any],
    ) -> None:

        self.repository_data = (
            repository_data
            if isinstance(repository_data, dict)
            else {}
        )

        self.files = self._extract_files()

        self.file_paths = [
            _path_from_item(item)
            for item in self.files
            if _path_from_item(item)
        ]

        self.file_paths = [
            _normalize_path(path)
            for path in self.file_paths
        ]

        self.source_files = (
            self._extract_source_files()
        )

    # ========================================================
    # DATA EXTRACTION
    # ========================================================

    def _extract_files(self) -> List[Any]:
        """
        Support multiple repository-data schemas.
        """

        for key in (
            "files",
            "repository_files",
            "file_tree",
            "contents",
        ):
            value = self.repository_data.get(key)

            if value:
                return _safe_list(value)

        return []

    def _extract_source_files(self) -> List[Any]:
        """
        Prefer the fetcher's explicit source_files field.

        If it is unavailable, derive source files from the
        collected repository files.
        """

        explicit = self.repository_data.get(
            "source_files"
        )

        if explicit:
            return _safe_list(explicit)

        result = []

        for item in self.files:
            path = _path_from_item(item)

            if not path:
                continue

            if self.is_source_file(path):
                result.append(item)

        return result

    # ========================================================
    # FILE CLASSIFICATION
    # ========================================================

    def is_documentation_file(
        self,
        path: str,
    ) -> bool:

        path = _normalize_path(path)

        name = _filename(path)
        extension = _extension(path)

        if extension in DOCUMENTATION_EXTENSIONS:
            return True

        if name.startswith("readme"):
            return True

        if name.startswith("changelog"):
            return True

        if name.startswith("contributing"):
            return True

        if name.startswith("license"):
            return True

        return False

    def is_configuration_file(
        self,
        path: str,
    ) -> bool:

        path = _normalize_path(path)

        name = _filename(path)

        if name in CONFIGURATION_FILENAMES:
            return True

        if name.startswith(".env"):
            return True

        if "/.github/" in f"/{path.lower()}":
            return True

        return False

    def is_test_file(
        self,
        path: str,
    ) -> bool:

        path = _normalize_path(path)

        name = _filename(path)

        parts = [
            part.lower()
            for part in Path(path).parts
        ]

        if (
            "test" in parts
            or "tests" in parts
            or "__tests__" in parts
        ):
            return True

        if name.startswith("test_"):
            return True

        if name.endswith("_test.py"):
            return True

        if name.endswith(".test.js"):
            return True

        if name.endswith(".test.ts"):
            return True

        if name.endswith(".spec.js"):
            return True

        if name.endswith(".spec.ts"):
            return True

        return False

    def is_source_file(
        self,
        path: str,
    ) -> bool:

        if self.is_documentation_file(path):
            return False

        if self.is_configuration_file(path):
            return False

        if self.is_test_file(path):
            return False

        extension = _extension(path)

        return extension in SOURCE_EXTENSIONS

    # ========================================================
    # LANGUAGE DETECTION
    # ========================================================

    def _detect_languages(
        self,
    ) -> List[Dict[str, Any]]:

        github_languages = (
            self.repository_data.get(
                "languages"
            )
        )

        evidence: Counter[str] = Counter()

        # ----------------------------------------------------
        # First preference: GitHub language metadata
        # ----------------------------------------------------

        if isinstance(
            github_languages,
            dict,
        ):

            for language, amount in (
                github_languages.items()
            ):

                if not language:
                    continue

                # Important:
                # Only accept actual known language names.
                # This prevents artifacts such as "url"
                # from becoming programming languages.
                if not self._is_valid_language_name(
                    str(language)
                ):
                    continue

                try:
                    evidence[
                        str(language)
                    ] += int(amount)
                except Exception:
                    evidence[
                        str(language)
                    ] += 1

        # ----------------------------------------------------
        # Supplement with file extensions
        # ----------------------------------------------------

        for path in self.file_paths:

            extension = _extension(path)

            language = LANGUAGE_EXTENSIONS.get(
                extension
            )

            if not language:
                continue

            # Do not count Markdown as programming source.
            if language == "Markdown":
                continue

            evidence[language] += 1

        if not evidence:
            return []

        total = sum(evidence.values())

        if total <= 0:
            return []

        result = []

        for language, amount in (
            evidence.most_common()
        ):

            percentage = round(
                (amount / total) * 100,
                1,
            )

            result.append(
                {
                    "language": language,
                    "evidence": amount,
                    "percentage": percentage,
                }
            )

        return result

    @staticmethod
    def _is_valid_language_name(
        language: str,
    ) -> bool:
        """
        Filter obvious metadata artifacts.

        GitHub normally returns real language names.
        This defensive filter prevents values such as:
        url, link, unknown, file, binary, etc.
        """

        normalized = (
            language
            .strip()
            .lower()
        )

        invalid = {
            "",
            "url",
            "link",
            "unknown",
            "file",
            "binary",
            "text",
            "data",
        }

        if normalized in invalid:
            return False

        known_languages = set(
            LANGUAGE_EXTENSIONS.values()
        )

        known_lower = {
            item.lower()
            for item in known_languages
        }

        return normalized in known_lower

    # ========================================================
    # TECHNOLOGY STACK
    # ========================================================

    def _detect_technology_stack(
        self,
    ) -> Dict[str, List[str]]:

        result: Dict[str, List[str]] = {
            "frontend": [],
            "backend": [],
            "ai_ml": [],
            "database": [],
            "blockchain": [],
            "testing": [],
            "devops": [],
            "other": [],
        }

        paths_text = "\n".join(
            self.file_paths
        ).lower()

        content_text = "\n".join(
            _content_from_item(item)
            for item in self.files
        ).lower()

        combined = (
            paths_text
            + "\n"
            + content_text
        )

        languages = self._detect_languages()

        language_names = {
            item["language"]
            for item in languages
        }

        # ----------------------------------------------------
        # Language-based technology detection
        # ----------------------------------------------------

        language_category_map = {
            "HTML": "frontend",
            "CSS": "frontend",
            "SCSS": "frontend",
            "Sass": "frontend",
            "Less": "frontend",
            "JavaScript": "frontend",
            "TypeScript": "frontend",
            "Vue": "frontend",
            "Svelte": "frontend",

            "Python": "backend",
            "Java": "backend",
            "Go": "backend",
            "Rust": "backend",
            "PHP": "backend",
            "Ruby": "backend",
            "C#": "backend",
        }

        for language in language_names:

            category = language_category_map.get(
                language
            )

            if category and language not in result[
                category
            ]:
                result[category].append(
                    language
                )

        # ----------------------------------------------------
        # Indicator-based detection
        # ----------------------------------------------------

        for category, technologies in (
            TECHNOLOGY_INDICATORS.items()
        ):

            for technology, indicators in (
                technologies.items()
            ):

                detected = False

                for indicator in indicators:

                    indicator_lower = (
                        indicator.lower()
                    )

                    if (
                        indicator_lower.startswith(".")
                        and len(indicator_lower) <= 6
                    ):
                        if any(
                            path.lower().endswith(
                                indicator_lower
                            )
                            for path in self.file_paths
                        ):
                            detected = True
                            break

                    elif (
                        indicator_lower
                        in combined
                    ):
                        detected = True
                        break

                if detected:

                    if technology not in result[
                        category
                    ]:
                        result[category].append(
                            technology
                        )

        # ----------------------------------------------------
        # Remove duplicate language/framework entries
        # ----------------------------------------------------

        for category in result:

            result[category] = list(
                dict.fromkeys(
                    result[category]
                )
            )

        return result

    # ========================================================
    # PROJECT TYPE
    # ========================================================

    def _infer_project_type(
        self,
        languages: List[Dict[str, Any]],
        technology_stack: Dict[str, List[str]],
    ) -> str:

        frontend = technology_stack.get(
            "frontend",
            [],
        )

        backend = technology_stack.get(
            "backend",
            [],
        )

        ai_ml = technology_stack.get(
            "ai_ml",
            [],
        )

        blockchain = technology_stack.get(
            "blockchain",
            [],
        )

        has_html = "HTML" in frontend
        has_css = "CSS" in frontend
        has_js = "JavaScript" in frontend
        has_ts = "TypeScript" in frontend

        if blockchain:
            return (
                "Blockchain / Web3 application"
            )

        if ai_ml:
            return (
                "AI / Machine Learning application"
            )

        if frontend and backend:
            return (
                "Full-stack web application"
            )

        if backend:
            return (
                "Backend / server-side application"
            )

        if (
            has_html
            or has_css
            or has_js
            or has_ts
        ):
            return (
                "Frontend web application"
            )

        if any(
            item["language"] == "Python"
            for item in languages
        ):
            return "Python software project"

        if any(
            item["language"] == "Java"
            for item in languages
        ):
            return "Java software project"

        if any(
            item["language"] == "Go"
            for item in languages
        ):
            return "Go software project"

        if any(
            item["language"] == "Rust"
            for item in languages
        ):
            return "Rust software project"

        if languages:
            return "Software project"

        return "Repository / project"

    # ========================================================
    # DOMAIN
    # ========================================================

    def _infer_domain(
        self,
        technology_stack: Dict[str, List[str]],
    ) -> str:

        repository_name = str(
            self.repository_data.get(
                "name",
                "",
            )
        ).lower()

        description = str(
            self.repository_data.get(
                "description",
                "",
            )
        ).lower()

        topics = " ".join(
            str(item).lower()
            for item in _safe_list(
                self.repository_data.get(
                    "topics"
                )
            )
        )

        combined = (
            repository_name
            + " "
            + description
            + " "
            + topics
        )

        if technology_stack.get("blockchain"):
            return (
                "Blockchain / Web3"
            )

        if technology_stack.get("ai_ml"):
            return (
                "Artificial Intelligence / Machine Learning"
            )

        if any(
            term in combined
            for term in (
                "github",
                "repository",
                "developer",
                "developer tools",
                "software",
                "code",
                "programming",
            )
        ):
            return (
                "Software Engineering / Developer Tools"
            )

        if technology_stack.get("frontend"):
            return "Web Development"

        if technology_stack.get("database"):
            return "Data / Database Systems"

        return "Software Development"

    # ========================================================
    # PURPOSE
    # ========================================================

    def _infer_purpose(
        self,
        project_type: str,
        domain: str,
    ) -> str:

        description = (
            self.repository_data.get(
                "description"
            )
        )

        if description:
            description = str(
                description
            ).strip()

            if description:
                return (
                    f"The repository is intended "
                    f"for {description}"
                )

        name = str(
            self.repository_data.get(
                "name",
                "this repository",
            )
        )

        name_lower = name.lower()

        if (
            "spoon-knife" in name_lower
            or name_lower == "spoon-knife"
        ):
            return (
                "The repository is a GitHub demonstration "
                "repository intended to illustrate the basic "
                "fork-and-edit workflow."
            )

        if "hello-world" in name_lower:
            return (
                "The repository appears to provide a simple "
                "demonstration or learning example."
            )

        if (
            "portfolio" in name_lower
            or "website" in name_lower
        ):
            return (
                "The repository appears to contain a "
                "web-based project or website."
            )

        if (
            "api" in name_lower
            or "server" in name_lower
            or "backend" in name_lower
        ):
            return (
                "The repository appears to implement "
                "backend or API functionality."
            )

        if (
            "test" in name_lower
            or "demo" in name_lower
            or "example" in name_lower
        ):
            return (
                "The repository appears to provide an "
                "example, demonstration, or testing project."
            )

        return (
            f"The repository appears to be a "
            f"{project_type.lower()} in the "
            f"{domain.lower()} domain."
        )

    # ========================================================
    # TOP-LEVEL STRUCTURE
    # ========================================================

    def _build_repository_structure(
        self,
    ) -> Dict[str, Any]:

        directories = Counter()
        extensions = Counter()

        for path in self.file_paths:

            parts = Path(path).parts

            if len(parts) > 1:

                directories[
                    parts[0]
                ] += 1

            extension = _extension(path)

            if extension:
                extensions[
                    extension
                ] += 1

        return {
            "top_level_directories": [
                {
                    "directory": directory,
                    "file_count": count,
                }
                for directory, count
                in directories.most_common()
            ],
            "file_extensions": [
                {
                    "extension": extension,
                    "count": count,
                }
                for extension, count
                in extensions.most_common()
            ],
        }

    # ========================================================
    # MAJOR COMPONENTS
    # ========================================================

    def _build_major_components(
        self,
        technology_stack: Dict[str, List[str]],
    ) -> List[Dict[str, str]]:

        components = []

        paths_lower = [
            path.lower()
            for path in self.file_paths
        ]

        def has_path_keyword(
            keywords: Iterable[str],
        ) -> bool:

            return any(
                any(
                    keyword in path
                    for keyword in keywords
                )
                for path in paths_lower
            )

        # ----------------------------------------------------
        # Frontend
        # ----------------------------------------------------

        if technology_stack.get(
            "frontend"
        ):

            components.append(
                {
                    "name": "Frontend",
                    "purpose": (
                        "Provides the user-facing "
                        "interface and presentation layer."
                    ),
                    "evidence": (
                        "Frontend languages or technologies "
                        "were detected."
                    ),
                }
            )

        # ----------------------------------------------------
        # Backend
        # ----------------------------------------------------

        if technology_stack.get(
            "backend"
        ):

            components.append(
                {
                    "name": "Backend / API",
                    "purpose": (
                        "Provides server-side application "
                        "logic or API functionality."
                    ),
                    "evidence": (
                        "Backend languages or frameworks "
                        "were detected."
                    ),
                }
            )

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        if technology_stack.get(
            "ai_ml"
        ):

            components.append(
                {
                    "name": "AI / Machine Learning",
                    "purpose": (
                        "Contains machine-learning, "
                        "generative-AI, or model-related "
                        "functionality."
                    ),
                    "evidence": (
                        "AI/ML frameworks or libraries "
                        "were detected."
                    ),
                }
            )

        # ----------------------------------------------------
        # Database
        # ----------------------------------------------------

        if technology_stack.get(
            "database"
        ):

            components.append(
                {
                    "name": "Database / Data Layer",
                    "purpose": (
                        "Stores, retrieves, or processes "
                        "application data."
                    ),
                    "evidence": (
                        "Database technologies or SQL "
                        "artifacts were detected."
                    ),
                }
            )

        # ----------------------------------------------------
        # Blockchain
        # ----------------------------------------------------

        if technology_stack.get(
            "blockchain"
        ):

            components.append(
                {
                    "name": "Blockchain / Web3",
                    "purpose": (
                        "Provides blockchain, smart-contract, "
                        "or Web3 functionality."
                    ),
                    "evidence": (
                        "Blockchain-related technologies "
                        "were detected."
                    ),
                }
            )

        # ----------------------------------------------------
        # Testing
        # ----------------------------------------------------

        has_tests = any(
            self.is_test_file(path)
            for path in self.file_paths
        )

        if (
            has_tests
            or technology_stack.get("testing")
        ):

            components.append(
                {
                    "name": "Testing",
                    "purpose": (
                        "Contains automated or structured "
                        "software testing resources."
                    ),
                    "evidence": (
                        "Test files or testing frameworks "
                        "were detected."
                    ),
                }
            )

        # ----------------------------------------------------
        # GitHub integration
        # ----------------------------------------------------

        if has_path_keyword(
            (
                "github",
                ".github",
            )
        ):

            components.append(
                {
                    "name": "GitHub Integration",
                    "purpose": (
                        "Contains GitHub-specific workflows, "
                        "configuration, or integration logic."
                    ),
                    "evidence": (
                        "GitHub-related repository paths "
                        "were detected."
                    ),
                }
            )

        # ----------------------------------------------------
        # Documentation
        # ----------------------------------------------------

        documentation_files = [
            path
            for path in self.file_paths
            if self.is_documentation_file(path)
        ]

        if documentation_files:

            components.append(
                {
                    "name": "Documentation",
                    "purpose": (
                        "Contains project documentation "
                        "and explanatory material."
                    ),
                    "evidence": (
                        "Documentation files were detected."
                    ),
                }
            )

        # ----------------------------------------------------
        # Reporting
        # ----------------------------------------------------

        if has_path_keyword(
            (
                "report",
                "reports",
                "export",
            )
        ):

            components.append(
                {
                    "name": "Reporting",
                    "purpose": (
                        "Generates, formats, or exports "
                        "analysis results or project information."
                    ),
                    "evidence": (
                        "Report or export-related paths "
                        "were detected."
                    ),
                }
            )

        return components

    # ========================================================
    # CODEBASE COMPOSITION
    # ========================================================

    def _build_codebase_composition(
        self,
        languages: List[Dict[str, Any]],
        technology_stack: Dict[str, List[str]],
    ) -> List[str]:

        composition = []

        language_names = [
            item["language"]
            for item in languages
        ]

        if language_names:

            composition.append(
                "The repository contains "
                + ", ".join(language_names)
                + " code or repository artifacts."
            )

        if technology_stack.get(
            "frontend"
        ):

            composition.append(
                "Frontend or user-interface code is present."
            )

        if technology_stack.get(
            "backend"
        ):

            composition.append(
                "Backend or server-side functionality is present."
            )

        if technology_stack.get(
            "ai_ml"
        ):

            composition.append(
                "AI or machine-learning functionality is present."
            )

        if technology_stack.get(
            "database"
        ):

            composition.append(
                "Database or data-storage functionality is present."
            )

        if technology_stack.get(
            "blockchain"
        ):

            composition.append(
                "Blockchain or Web3 functionality is present."
            )

        if any(
            self.is_test_file(path)
            for path in self.file_paths
        ):

            composition.append(
                "Automated or structured test files are present."
            )

        if any(
            self.is_documentation_file(path)
            for path in self.file_paths
        ):

            composition.append(
                "Documentation files are present."
            )

        if not composition:

            composition.append(
                "The available repository data is "
                "insufficient for detailed codebase classification."
            )

        return composition

    # ========================================================
    # WORKFLOW
    # ========================================================

    def _build_workflow(
        self,
        technology_stack: Dict[str, List[str]],
        components: List[Dict[str, str]],
    ) -> List[str]:

        workflow = []

        has_frontend = bool(
            technology_stack.get(
                "frontend"
            )
        )

        has_backend = bool(
            technology_stack.get(
                "backend"
            )
        )

        has_database = bool(
            technology_stack.get(
                "database"
            )
        )

        has_ai = bool(
            technology_stack.get(
                "ai_ml"
            )
        )

        has_blockchain = bool(
            technology_stack.get(
                "blockchain"
            )
        )

        if has_frontend:

            workflow.append(
                "Users interact with the frontend or "
                "user-facing application interface."
            )

        if has_backend:

            workflow.append(
                "The frontend or external clients communicate "
                "with backend/server-side application logic."
            )

        if has_ai:

            workflow.append(
                "AI or machine-learning components process "
                "input data to generate predictions, analysis, "
                "or generated results."
            )

        if has_database:

            workflow.append(
                "Application data is stored or retrieved "
                "through the detected database/data layer."
            )

        if has_blockchain:

            workflow.append(
                "Blockchain or smart-contract components "
                "provide decentralized or integrity-related functionality."
            )

        if not workflow:

            if (
                self.repository_data.get(
                    "description"
                )
            ):

                workflow.append(
                    "The repository provides the functionality "
                    "described by its GitHub repository metadata."
                )

            else:

                workflow.append(
                    "The repository workflow could not be "
                    "determined confidently from the collected evidence."
                )

        return workflow

    # ========================================================
    # IMPORTANT FILES
    # ========================================================

    def _build_important_modules(
        self,
    ) -> List[Dict[str, str]]:

        result = []

        priority_names = {
            "readme.md": (
                "Project documentation and repository overview."
            ),
            "index.html": (
                "Primary HTML entry point for the web interface."
            ),
            "app.py": (
                "Likely application entry point."
            ),
            "main.py": (
                "Likely application entry point."
            ),
            "server.py": (
                "Likely server entry point."
            ),
            "package.json": (
                "Defines JavaScript/Node.js project metadata "
                "and dependencies."
            ),
            "requirements.txt": (
                "Defines Python project dependencies."
            ),
            "pyproject.toml": (
                "Defines Python project configuration and dependencies."
            ),
            "dockerfile": (
                "Defines container image/build configuration."
            ),
            "docker-compose.yml": (
                "Defines multi-container application configuration."
            ),
            "docker-compose.yaml": (
                "Defines multi-container application configuration."
            ),
            "go.mod": (
                "Defines Go module metadata and dependencies."
            ),
            "cargo.toml": (
                "Defines Rust package metadata and dependencies."
            ),
        }

        # First collect known important files.
        for path in self.file_paths:

            name = _filename(path)

            if name in priority_names:

                result.append(
                    {
                        "name": path,
                        "purpose": priority_names[name],
                    }
                )

        # Then identify likely entry-point directories/files.
        keywords = (
            "main",
            "app",
            "server",
            "api",
            "index",
            "config",
        )

        for path in self.file_paths:

            if len(result) >= 12:
                break

            if self.is_documentation_file(path):
                continue

            name = _filename(path)

            stem = Path(name).stem.lower()

            if any(
                keyword == stem
                for keyword in keywords
            ):

                if any(
                    item["name"] == path
                    for item in result
                ):
                    continue

                result.append(
                    {
                        "name": path,
                        "purpose": (
                            "Potential application entry point "
                            "or central project module."
                        ),
                    }
                )

        # Finally include a small number of source files.
        for path in self.file_paths:

            if len(result) >= 12:
                break

            if not self.is_source_file(path):
                continue

            if any(
                item["name"] == path
                for item in result
            ):
                continue

            result.append(
                {
                    "name": path,
                    "purpose": (
                        "Collected source file relevant "
                        "to the repository implementation."
                    ),
                }
            )

        return result

    # ========================================================
    # STATISTICS
    # ========================================================

    def _calculate_total_lines(
        self,
    ) -> int:

        total = 0

        for item in self.files:

            content = _content_from_item(item)

            if not content:
                continue

            total += len(
                content.splitlines()
            )

        return total

    def _build_statistics(
        self,
        languages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        documentation_files = [
            path
            for path in self.file_paths
            if self.is_documentation_file(path)
        ]

        test_files = [
            path
            for path in self.file_paths
            if self.is_test_file(path)
        ]

        configuration_files = [
            path
            for path in self.file_paths
            if self.is_configuration_file(path)
        ]

        source_files = [
            path
            for path in self.file_paths
            if self.is_source_file(path)
        ]

        branches = _safe_list(
            self.repository_data.get(
                "branches"
            )
        )

        issues = _safe_list(
            self.repository_data.get(
                "issues"
            )
        )

        pull_requests = _safe_list(
            self.repository_data.get(
                "pull_requests"
            )
        )

        return {
            "files_analyzed": len(
                self.file_paths
            ),
            "source_files": len(
                source_files
            ),
            "test_files": len(
                test_files
            ),
            "documentation_files": len(
                documentation_files
            ),
            "configuration_files": len(
                configuration_files
            ),
            "total_lines_analyzed": (
                self._calculate_total_lines()
            ),
            "languages_detected": len(
                languages
            ),
            "branches": len(
                branches
            ),
            "issues": len(
                issues
            ),
            "pull_requests": len(
                pull_requests
            ),
        }

    # ========================================================
    # TARGET USERS
    # ========================================================

    def _infer_target_users(
        self,
        project_type: str,
        domain: str,
    ) -> List[str]:

        users = []

        if (
            "Developer"
            in domain
            or "Software"
            in domain
            or "software"
            in project_type.lower()
        ):

            users.extend(
                [
                    "Software developers",
                    "Repository maintainers",
                    "Development teams",
                ]
            )

        if "web" in project_type.lower():

            users.append(
                "Web application users"
            )

        if "AI" in project_type:

            users.append(
                "AI / machine-learning developers"
            )

        if "Blockchain" in project_type:

            users.append(
                "Blockchain / Web3 developers"
            )

        if not users:

            users.append(
                "Developers and repository users"
            )

        return list(
            dict.fromkeys(users)
        )

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    def _build_executive_summary(
        self,
        project_type: str,
        domain: str,
        purpose: str,
        languages: List[Dict[str, Any]],
        technology_stack: Dict[str, List[str]],
        components: List[Dict[str, str]],
        statistics: Dict[str, Any],
    ) -> str:

        repository_name = self.repository_data.get(
            "full_name"
        )

        if not repository_name:
            repository_name = self.repository_data.get(
                "name",
                "The repository",
            )

        language_names = [
            item["language"]
            for item in languages
        ]

        if language_names:

            language_text = ", ".join(
                language_names
            )

        else:

            language_text = (
                "no programming languages confidently detected"
            )

        component_names = [
            item["name"]
            for item in components
        ]

        if component_names:

            component_text = ", ".join(
                component_names
            )

        else:

            component_text = (
                "no major components confidently detected"
            )

        return (
            f"{repository_name} is a {project_type.lower()} "
            f"in the {domain.lower()} domain. "
            f"{purpose} "
            f"The collected repository evidence identifies "
            f"{language_text}. "
            f"Major detected components include "
            f"{component_text}. "
            f"The analysis pipeline collected "
            f"{statistics.get('files_analyzed', 0)} files, "
            f"including "
            f"{statistics.get('source_files', 0)} source files, "
            f"{statistics.get('test_files', 0)} test files, "
            f"and "
            f"{statistics.get('documentation_files', 0)} "
            f"documentation files."
        )

    # ========================================================
    # PUBLIC BUILD METHOD
    # ========================================================

    def build(
        self,
    ) -> Dict[str, Any]:

        languages = self._detect_languages()

        technology_stack = (
            self._detect_technology_stack()
        )

        project_type = (
            self._infer_project_type(
                languages=languages,
                technology_stack=technology_stack,
            )
        )

        domain = (
            self._infer_domain(
                technology_stack=technology_stack,
            )
        )

        purpose = (
            self._infer_purpose(
                project_type=project_type,
                domain=domain,
            )
        )

        structure = (
            self._build_repository_structure()
        )

        components = (
            self._build_major_components(
                technology_stack=technology_stack,
            )
        )

        composition = (
            self._build_codebase_composition(
                languages=languages,
                technology_stack=technology_stack,
            )
        )

        workflow = (
            self._build_workflow(
                technology_stack=technology_stack,
                components=components,
            )
        )

        important_modules = (
            self._build_important_modules()
        )

        statistics = (
            self._build_statistics(
                languages=languages,
            )
        )

        target_users = (
            self._infer_target_users(
                project_type=project_type,
                domain=domain,
            )
        )

        executive_summary = (
            self._build_executive_summary(
                project_type=project_type,
                domain=domain,
                purpose=purpose,
                languages=languages,
                technology_stack=technology_stack,
                components=components,
                statistics=statistics,
            )
        )

        repository_info = {
            "name": self.repository_data.get(
                "name"
            ),
            "full_name": self.repository_data.get(
                "full_name"
            ),
            "url": self.repository_data.get(
                "url"
            ),
            "default_branch": self.repository_data.get(
                "default_branch"
            ),
            "description": self.repository_data.get(
                "description"
            ),
            "stars": self.repository_data.get(
                "stars",
                0,
            ),
            "forks": self.repository_data.get(
                "forks",
                0,
            ),
            "watchers": self.repository_data.get(
                "watchers",
                0,
            ),
            "open_issues": self.repository_data.get(
                "open_issues",
                0,
            ),
            "topics": _safe_list(
                self.repository_data.get(
                    "topics"
                )
            ),
        }

        return {
            "repository": repository_info,

            "project_type": project_type,

            "domain": domain,

            "purpose": purpose,

            "executive_summary": (
                executive_summary
            ),

            "languages": languages,

            "technology_stack": (
                technology_stack
            ),

            "repository_structure": (
                structure
            ),

            "major_components": (
                components
            ),

            "codebase_composition": (
                composition
            ),

            "workflow": workflow,

            "important_modules": (
                important_modules
            ),

            "repository_statistics": (
                statistics
            ),

            "target_users": target_users,

            "analysis_scope": {
                "files_analyzed": statistics[
                    "files_analyzed"
                ],
                "source_files": statistics[
                    "source_files"
                ],
                "test_files": statistics[
                    "test_files"
                ],
                "documentation_files": statistics[
                    "documentation_files"
                ],
                "configuration_files": statistics[
                    "configuration_files"
                ],
            },
        }


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================


def build_repository_intelligence(
    repository_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build repository intelligence from RepositoryFetcher output.
    """

    intelligence = RepositoryIntelligence(
        repository_data
    )

    return intelligence.build()