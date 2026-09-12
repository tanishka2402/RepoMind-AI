"""
Pydantic schemas used by the RepoMind-AI API.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel


# =========================================================
# REPOSITORY
# =========================================================

class RepositoryResponse(BaseModel):
    id: int
    name: str
    full_name: str
    url: str
    default_branch: str


# =========================================================
# ANALYSIS
# =========================================================

class AnalysisResponse(BaseModel):
    id: int
    status: str
    report: str

    grounding_status: str
    evidence_count: int
    warnings: List[str]

    ai_grounding_status: str
    ai_evidence_count: int

    created_at: datetime

    repository: RepositoryResponse

    model_config = {
        "from_attributes": True
    }


# =========================================================
# ANALYZE RESPONSE
# =========================================================

class AnalyzeResponse(BaseModel):
    status: str
    repository: RepositoryResponse
    analysis: AnalysisResponse


# =========================================================
# HISTORY ITEM
# =========================================================

class AnalysisHistoryItem(BaseModel):
    id: int
    status: str

    grounding_status: str
    evidence_count: int

    ai_grounding_status: str
    ai_evidence_count: int

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# =========================================================
# HEALTH
# =========================================================

class HealthResponse(BaseModel):
    status: str


# =========================================================
# ROOT
# =========================================================

class RootResponse(BaseModel):
    message: str
    status: str