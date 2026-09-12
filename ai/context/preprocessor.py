"""
RepoMind-AI Source Preprocessor

Prepares repository source files for grounded AI analysis.

The goal is to:
1. Keep source code within reasonable context limits.
2. Preserve file paths.
3. Remove obviously noisy content.
4. Create compact, agent-friendly source context.
"""

from typing import Any, Dict, List


class SourcePreprocessor:
    """Prepare repository source files for AI agents."""

    DEFAULT_MAX_CHARS = 40_000
    DEFAULT_MAX_FILE_CHARS = 8_000

    def __init__(
        self,
        max_chars: int = DEFAULT_MAX_CHARS,
        max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    ) -> None:
        self.max_chars = max_chars
        self.max_file_chars = max_file_chars

    def process(
        self,
        source_files: List[Dict[str, Any]],
    ) -> str:
        """
        Convert source files into compact AI-readable context.
        """

        if not source_files:
            return (
                "SOURCE CODE\n"
                "===========\n\n"
                "No source files were collected from the repository."
            )

        sections: List[str] = []
        total_chars = 0

        for source_file in source_files:
            path = source_file.get("path")

            content = source_file.get(
                "content",
                "",
            )

            if not path:
                continue

            if not isinstance(content, str):
                content = str(content)

            content = self._clean_content(content)

            if not content:
                continue

            # Limit individual files.
            truncated = False

            if len(content) > self.max_file_chars:
                content = content[: self.max_file_chars]
                truncated = True

            section = self._format_file(
                path=path,
                content=content,
                truncated=truncated,
            )

            # Stop when the overall context becomes too large.
            if total_chars + len(section) > self.max_chars:
                remaining = self.max_chars - total_chars

                if remaining > 200:
                    sections.append(section[:remaining])

                break

            sections.append(section)
            total_chars += len(section)

        if not sections:
            return (
                "SOURCE CODE\n"
                "===========\n\n"
                "No usable source-code content was collected."
            )

        return (
            "SOURCE CODE\n"
            "===========\n\n"
            "The following source files were collected directly "
            "from GitHub.\n\n"
            "GROUNDING RULES:\n"
            "- Treat file paths and code below as observed repository facts.\n"
            "- Do not invent code that is not shown.\n"
            "- If a file is truncated, do not assume the missing portion.\n"
            "- If information is unavailable, say so explicitly.\n\n"
            + "\n".join(sections)
        )

    def _clean_content(self, content: str) -> str:
        """Perform minimal safe cleanup."""

        # Normalize line endings.
        content = content.replace("\r\n", "\n")
        content = content.replace("\r", "\n")

        # Remove excessive blank lines.
        lines = content.split("\n")

        cleaned_lines: List[str] = []
        previous_blank = False

        for line in lines:
            is_blank = not line.strip()

            if is_blank and previous_blank:
                continue

            cleaned_lines.append(line.rstrip())
            previous_blank = is_blank

        return "\n".join(cleaned_lines).strip()

    def _format_file(
        self,
        path: str,
        content: str,
        truncated: bool,
    ) -> str:
        """Format one source file."""

        language = self._detect_language(path)

        suffix = ""

        if truncated:
            suffix = (
                "\n\n"
                "[FILE TRUNCATED: only part of this file was "
                "included in the AI context.]"
            )

        return (
            f"FILE: {path}\n"
            f"LANGUAGE: {language}\n"
            f"{'-' * 60}\n"
            f"{content}"
            f"{suffix}\n"
            f"{'-' * 60}\n"
        )

    def _detect_language(self, path: str) -> str:
        """Determine a simple language label from the file extension."""

        extension = ""

        if "." in path:
            extension = "." + path.rsplit(".", 1)[1].lower()

        languages = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript/JSX",
            ".ts": "TypeScript",
            ".tsx": "TypeScript/TSX",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C/C++ Header",
            ".hpp": "C++ Header",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".kts": "Kotlin",
            ".cs": "C#",
            ".scala": "Scala",
            ".sh": "Shell",
            ".bash": "Bash",
            ".sql": "SQL",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".vue": "Vue",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".toml": "TOML",
            ".md": "Markdown",
        }

        return languages.get(
            extension,
            "Unknown",
        )

