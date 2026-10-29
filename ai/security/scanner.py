from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any


MAX_FILES_TO_SCAN = 300
MAX_FILE_CHARS = 100_000
MAX_FINDINGS = 200

IGNORED_PARTS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    "dist", "build", "vendor", "coverage",
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs",
    ".rb", ".php", ".sh", ".bash", ".zsh", ".ps1",
    ".sql", ".html", ".vue", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".conf", ".env.example",
    ".dockerfile", ".tf", ".xml", ".gradle", ".properties",
    ".md", ".txt",
}

# Each rule has an ID, severity, explanation, regex, and remediation.
RULES = [
    {
        "id": "SECRET001",
        "severity": "critical",
        "title": "Possible hardcoded credential",
        "pattern": re.compile(
            r"""(?ix)
            \b(?:api[_-]?key|secret[_-]?key|access[_-]?token|
                auth[_-]?token|password|passwd|client[_-]?secret)
            \b\s*["']?\s*[:=]\s*["']
            (?!your[_ -]?|example|changeme|placeholder|<|xxx)
            [^"'\s]{8,}
            """
        ),
        "remediation": (
            "Remove the credential from source, rotate it if real, "
            "and load it from a server-side secret manager or environment."
        ),
    },
    {
        "id": "EXEC001",
        "severity": "high",
        "title": "Downloaded content may be executed",
        "pattern": re.compile(
            r"""(?ix)
            (?:curl|wget)\b.{0,180}
            (?:\|\s*(?:sh|bash|zsh)\b|-\s*o\s+\S+.{0,80}
            (?:&&|;)\s*(?:sh|bash|python|node)\b)
            """
        ),
        "remediation": (
            "Avoid piping remote content into a shell. Pin and verify "
            "downloads, inspect them, and verify cryptographic checksums."
        ),
    },
    {
        "id": "EXEC002",
        "severity": "high",
        "title": "Dynamic command execution",
        "pattern": re.compile(
            r"""(?ix)
            \b(?:eval|exec)\s*\(
            | \bsubprocess\.(?:Popen|run|call)\s*\(
              [^\n]{0,180}\bshell\s*=\s*True
            | \bos\.system\s*\(
            """
        ),
        "remediation": (
            "Review the call and all input sources. Prefer argument lists "
            "with shell=False and avoid evaluating untrusted strings."
        ),
    },
    {
        "id": "DELETE001",
        "severity": "high",
        "title": "Potentially destructive file operation",
        "pattern": re.compile(
            r"""(?ix)
            \bshutil\.rmtree\s*\(
            | \bos\.remove\s*\(
            | \bos\.unlink\s*\(
            | \brm\s+-[^\n]{0,10}r[^\n]{0,20}(?:/|~|\*)
            | \bDROP\s+(?:DATABASE|TABLE)\b
            """
        ),
        "remediation": (
            "Confirm the target is constrained and authorized. Add path "
            "validation, explicit safeguards, and backups where appropriate."
        ),
    },
    {
        "id": "DESERIALIZE001",
        "severity": "high",
        "title": "Unsafe deserialization API",
        "pattern": re.compile(
            r"""(?ix)
            \bpickle\.(?:loads?|Unpickler)\b
            | \byaml\.load\s*\(
            | \bmarshal\.loads?\s*\(
            """
        ),
        "remediation": (
            "Do not deserialize untrusted data with executable object "
            "formats. Prefer JSON or safe YAML loading when appropriate."
        ),
    },
    {
        "id": "NETWORK001",
        "severity": "medium",
        "title": "Potentially risky remote download",
        "pattern": re.compile(
            r"""(?ix)
            \brequests\.(?:get|post)\s*\(
            | \burllib\.request\.urlopen\s*\(
            | \bhttpx\.(?:get|post)\s*\(
            """
        ),
        "remediation": (
            "Check whether the URL is trusted, validate destinations, "
            "set timeouts, and avoid sending secrets to untrusted hosts."
        ),
    },
    {
        "id": "VERIFY001",
        "severity": "medium",
        "title": "TLS certificate verification disabled",
        "pattern": re.compile(
            r"""(?ix)
            \bverify\s*=\s*False\b
            | \bCERT_NONE\b
            """
        ),
        "remediation": (
            "Enable certificate verification except in a controlled test "
            "with a clear reason."
        ),
    },
]

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _path_is_ignored(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if any(part in IGNORED_PARTS for part in parts):
        return True
    if normalized.startswith("/") or ".." in parts:
        return True
    return False


def _looks_like_text_file(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    suffix = PurePosixPath(name).suffix

    # Include common extensionless deployment files.
    if name in {
        "dockerfile", "makefile", "jenkinsfile",
        ".gitlab-ci.yml", ".dockerignore",
    }:
        return True

    return suffix in TEXT_EXTENSIONS


def _extract_files(repository_data: Any) -> list[tuple[str, str]]:
    """
    Accept common repository-fetcher shapes, for example:
      {"files": [{"path": "app.py", "content": "..."}]}
      {"source_files": [{"name": "app.py", "content": "..."}]}
      {"files": {"app.py": "..."}}

    The scanner never opens local paths or executes repository code.
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(path: Any, content: Any) -> None:
        if not isinstance(path, str) or not isinstance(content, str):
            return
        path = path.replace("\\", "/").strip()
        if not path or path in seen or _path_is_ignored(path):
            return
        if not _looks_like_text_file(path):
            return
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS]
        if "\x00" in content:
            return
        seen.add(path)
        found.append((path, content))

    def walk(obj: Any, depth: int = 0) -> None:
        if depth > 5 or len(found) >= MAX_FILES_TO_SCAN:
            return

        if isinstance(obj, dict):
            path = (
                obj.get("path")
                or obj.get("filename")
                or obj.get("file_path")
                or obj.get("name")
            )
            content = (
                obj.get("content")
                or obj.get("text")
                or obj.get("source")
            )

            if isinstance(path, str) and isinstance(content, str):
                add(path, content)

            for key in (
                "files", "source_files", "file_contents",
                "contents", "tree", "repository_files",
            ):
                value = obj.get(key)
                if isinstance(value, dict):
                    for child_path, child_content in value.items():
                        if isinstance(child_content, str):
                            add(child_path, child_content)
                        else:
                            walk(child_content, depth + 1)
                elif isinstance(value, list):
                    for item in value:
                        walk(item, depth + 1)

        elif isinstance(obj, list):
            for item in obj:
                walk(item, depth + 1)

    walk(repository_data)
    return found


def scan_repository(repository_data: Any) -> dict[str, Any]:
    """
    Perform a bounded, read-only pattern scan of fetched repository content.

    A finding is a review signal, not proof of exploitation or malware.
    """
    files = _extract_files(repository_data)
    findings: list[dict[str, Any]] = []

    for path, content in files:
        for line_number, line in enumerate(content.splitlines(), start=1):
            if len(findings) >= MAX_FINDINGS:
                break

            # Avoid returning a matching secret itself as evidence.
            for rule in RULES:
                match = rule["pattern"].search(line)
                if not match:
                    continue

                # Return a redacted, short excerpt rather than a whole line.
                evidence = line.strip()[:180]
                if rule["id"] == "SECRET001":
                    evidence = re.sub(
                        r"""(?i)(\b(?:api[_-]?key|secret[_-]?key|
                        access[_-]?token|auth[_-]?token|password|
                        passwd|client[_-]?secret)\b\s*["']?\s*[:=]\s*["'])
                        [^"'\s]+""",
                        r"\1[REDACTED]",
                        evidence,
                    )

                findings.append({
                    "rule_id": rule["id"],
                    "severity": rule["severity"],
                    "title": rule["title"],
                    "file": path,
                    "line": line_number,
                    "evidence": evidence,
                    "recommendation": rule["remediation"],
                })

        if len(findings) >= MAX_FINDINGS:
            break

    findings.sort(
        key=lambda item: (
            SEVERITY_RANK.get(item["severity"], 99),
            item["file"],
            item["line"],
        )
    )

    counts = {
        severity: sum(
            1 for finding in findings
            if finding["severity"] == severity
        )
        for severity in ("critical", "high", "medium", "low")
    }

    return {
        "status": "completed" if files else "no_source_files",
        "files_scanned": len(files),
        "findings_count": len(findings),
        "severity_counts": counts,
        "findings_truncated": len(findings) >= MAX_FINDINGS,
        "findings": findings,
        "message": (
            "Potentially risky patterns found. Review each finding."
            if findings
            else (
                "No configured patterns were detected in the inspected files."
                if files
                else (
                    "No supported source file contents were available to scan. "
                    "This does not mean the repository is safe."
                )
            )
        ),
    }
