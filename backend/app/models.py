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
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

def utc_now():
    """
    Return the current UTC timestamp.
    """
    return datetime.now(timezone.utc)

# =========================================================
# USER MODEL
# =========================================================

class User(Base):
    """
    Stores authenticated RepoMind-AI users.
    """

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash = Column(
        String(500),
        nullable=False,
    )

    role = Column(
        String(20),
        nullable=False,
        default="user",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    analyses = relationship(
        "Analysis",
        back_populates="user",
    )
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
    user_id = Column(
    Integer,
    ForeignKey("users.id"),
    nullable=True,
    index=True,
)
    user = relationship(
    "User",
    back_populates="analyses",
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

    structured_analysis = relationship(
        "StructuredAnalysis",
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan",
    )

# =========================================================
# STRUCTURED ANALYSIS MODEL
# =========================================================

class StructuredAnalysis(Base):
    """
    Stores the canonical structured analysis associated with
    one completed repository analysis.

    Keeping this in a separate table allows the existing SQLite
    database to continue working without requiring a destructive
    schema migration.
    """

    __tablename__ = "structured_analyses"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    analysis_id = Column(
        Integer,
        ForeignKey("analyses.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    repository = Column(
        String(500),
        nullable=False,
    )

    executive_summary = Column(
        Text,
        nullable=False,
        default="",
    )

    architecture = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    code_quality = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    documentation = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    security = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    risk = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    recommendations = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    analysis = relationship(
        "Analysis",
        back_populates="structured_analysis",
    )
