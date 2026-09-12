"""
Database CRUD operations for RepoMind-AI.
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from .models import Analysis, Repository


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
    result: Dict[str, Any],
) -> Analysis:
    """
    Save a completed RepoMind-AI analysis.
    """

    analysis_data = result.get("analysis", {})
    ai_data = result.get("ai", {})

    analysis = Analysis(
        repository_id=repository.id,

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