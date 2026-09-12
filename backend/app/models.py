"""
SQLAlchemy database models for RepoMind-AI.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def utc_now():
    """
    Return the current UTC timestamp.
    """
    return datetime.now(timezone.utc)


# =========================================================
# REPOSITORY MODEL
# =========================================================

class Repository(Base):
    """
    Stores information about a GitHub repository.
    """

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)

    full_name = Column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
    )

    url = Column(String(1000), nullable=False)

    default_branch = Column(
        String(255),
        nullable=False,
        default="main",
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationship with analyses
    analyses = relationship(
        "Analysis",
        back_populates="repository",
        cascade="all, delete-orphan",
    )


# =========================================================
# ANALYSIS MODEL
# =========================================================

class Analysis(Base):
    """
    Stores one complete RepoMind-AI analysis.
    """

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)

    repository_id = Column(
        Integer,
        ForeignKey("repositories.id"),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # Analysis status
    # -----------------------------------------------------

    status = Column(
        String(50),
        nullable=False,
        default="completed",
    )

    # -----------------------------------------------------
    # Final report
    # -----------------------------------------------------

    report = Column(
        Text,
        nullable=False,
    )

    # -----------------------------------------------------
    # Final grounding information
    # -----------------------------------------------------

    grounding_status = Column(
        String(50),
        nullable=False,
        default="UNKNOWN",
    )

    evidence_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    warnings = Column(
        JSON,
        nullable=False,
        default=list,
    )

    # -----------------------------------------------------
    # Raw AI validation information
    # -----------------------------------------------------

    ai_grounding_status = Column(
        String(50),
        nullable=False,
        default="UNKNOWN",
    )

    ai_evidence_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # -----------------------------------------------------
    # Timestamp
    # -----------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # Relationship
    # -----------------------------------------------------

    repository = relationship(
        "Repository",
        back_populates="analyses",
    )