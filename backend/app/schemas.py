"""
Pydantic schemas used by the RepoMind-AI API.
"""

from datetime import datetime
from typing import List, Optional

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

    blockchain: Optional[dict] = None

# =========================================================
# ANALYZE RESPONSE
# =========================================================

class AnalyzeResponse(BaseModel):
    status: str
    repository: RepositoryResponse
    blockchain: Optional[dict] = None
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

# =========================================================
# AUTHENTICATION
# =========================================================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse