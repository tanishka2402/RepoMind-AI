"""
Hashing utilities for RepoMind-AI blockchain records.
"""

import hashlib


def sha256_text(value: str) -> str:
    """Return a SHA-256 hexadecimal hash for text."""
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def repository_hash(repository: str) -> str:
    """Create a deterministic hash for a repository identifier."""
    return sha256_text(
        repository.strip().lower()
    )


def report_hash(report: str) -> str:
    """Create a deterministic hash for a summary report."""
    return sha256_text(report)
