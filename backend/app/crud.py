"""
Database CRUD operations for RepoMind-AI.
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from .models import Analysis, Repository

from .models import (
    Analysis,
    Repository,
    StructuredAnalysis,
)


# =========================================================
# REPOSITORY
# =========================================================

def get_or_create_repository(
    db: Session,
    repository_data: Dict[str, Any],
) -> Repository:
    """
    Find an existing repository or create a new one.
    """

    full_name = repository_data.get("full_name")

    if not full_name:
        raise ValueError(
            "Repository data does not contain full_name."
        )

    repository = (
        db.query(Repository)
        .filter(Repository.full_name == full_name)
        .first()
    )

    if repository:
        repository.name = repository_data.get(
            "name",
            repository.name,
        )

        repository.url = repository_data.get(
            "url",
            repository.url,
        )

        repository.default_branch = repository_data.get(
            "default_branch",
            repository.default_branch,
        )

        db.commit()
        db.refresh(repository)

        return repository

    repository = Repository(
        name=repository_data.get(
            "name",
            full_name.split("/")[-1],
        ),
        full_name=full_name,
        url=repository_data.get(
            "url",
            "",
        ),
        default_branch=repository_data.get(
            "default_branch",
            "main",
        ),
    )

    db.add(repository)
    db.commit()
    db.refresh(repository)

    return repository


# =========================================================
# CREATE ANALYSIS
# =========================================================
def create_analysis(
    db: Session,
    repository: Repository,
    result: dict,
    user=None,
):
    """
    Save a completed RepoMind-AI analysis and its structured
    analysis representation.
    """

    analysis_data = result.get(
        "analysis",
        {},
    )

    ai_data = result.get(
        "ai",
        {},
    )

    structured_data = analysis_data.get(
        "structured",
        {},
    )

    analysis = Analysis(
        repository_id=repository.id,

        user_id=(
            user.id
            if user is not None
            else None
        ),

        status=result.get(
            "status",
            "completed",
        ),

        report=analysis_data.get(
            "report",
            "",
        ),

        grounding_status=analysis_data.get(
            "grounding_status",
            "UNKNOWN",
        ),

        evidence_count=analysis_data.get(
            "evidence_count",
            0,
        ),

        warnings=analysis_data.get(
            "warnings",
            [],
        ),

        ai_grounding_status=ai_data.get(
            "grounding_status",
            "UNKNOWN",
        ),

        ai_evidence_count=ai_data.get(
            "evidence_count",
            0,
        ),
    )

    db.add(analysis)

    db.flush()

    structured_analysis = StructuredAnalysis(
        analysis_id=analysis.id,

        repository=structured_data.get(
            "repository",
            repository.full_name,
        ),

        executive_summary=structured_data.get(
            "executive_summary",
            "",
        ),

        architecture=structured_data.get(
            "architecture",
            {},
        ),

        code_quality=structured_data.get(
            "code_quality",
            {},
        ),

        documentation=structured_data.get(
            "documentation",
            {},
        ),

        security=structured_data.get(
            "security",
            {},
        ),

        risk=structured_data.get(
            "risk",
            {},
        ),

        recommendations=structured_data.get(
            "recommendations",
            {},
        ),
    )

    db.add(structured_analysis)

    db.commit()

    db.refresh(analysis)

    return analysis
# =========================================================
# GET ANALYSIS
# =========================================================

def get_analysis(
    db: Session,
    analysis_id: int,
):
    """
    Retrieve one analysis by ID.
    """

    return (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id)
        .first()
    )

# =========================================================
# GET REPOSITORY
# =========================================================

def get_repository(
    db: Session,
    repository_id: int,
):
    """
    Retrieve a repository by ID.
    """

    return (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )


# =========================================================
# ANALYSIS HISTORY
# =========================================================

def get_repository_history(
    db: Session,
    repository_id: int,
) -> List[Analysis]:
    """
    Retrieve all analyses for a repository.
    """

    return (
        db.query(Analysis)
        .filter(
            Analysis.repository_id == repository_id
        )
        .order_by(
            Analysis.created_at.desc()
        )
        .all()
    )


# =========================================================
# ALL ANALYSIS HISTORY
# =========================================================

def get_all_analyses(
    db: Session,
    limit: int = 50,
) -> List[Analysis]:
    """
    Retrieve recent analyses.
    """

    return (
        db.query(Analysis)
        .order_by(
            Analysis.created_at.desc()
        )
        .limit(limit)
        .all()
    )
