"""
RepoMind-AI Backend API

This module exposes the FastAPI backend for RepoMind-AI.

Responsibilities:
- Accept GitHub repository analysis requests
- Run the RepoMind-AI analysis pipeline
- Persist repositories and analyses in SQLite
- Retrieve saved analyses
- Provide analysis history
- Provide dashboard analytics
- Provide authentication and authorization
- Register summarized analysis reports on blockchain
"""

import json
import sys
from pathlib import Path
from typing import List, Optional
from .architecture_preview import router as architecture_preview_router
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
)
from .blockchain.service import BlockchainService
from .database import get_db, init_db
from .insights import build_insights
from . import crud
from .models import Analysis, StructuredAnalysis, User
from .schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


# ============================================================
# PROJECT PATH
# ============================================================

AI_PATH = PROJECT_ROOT / "ai"

if str(AI_PATH) not in sys.path:
    sys.path.insert(0, str(AI_PATH))


# ============================================================
# AI IMPORTS
# ============================================================

from backend_ai import (
    analyze_repository as run_repository_analysis,
)

from reports.scoring import (
    calculate_overall_from_categories,
)

from reports.structured_analysis import (
    build_structured_analysis,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="RepoMind-AI Backend API",
    description=(
        "Backend API for analyzing GitHub repositories "
        "using the RepoMind-AI multi-agent analysis pipeline."
    ),
    version="1.0.0",
)
app.include_router(architecture_preview_router)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():
    """
    Initialize the SQLite database when the backend starts.
    """

    init_db()


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class AnalyzeRequest(BaseModel):
    """
    Request body for repository analysis.
    """

    repository: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description=(
            "GitHub repository URL or owner/name. "
            "Example: octocat/Spoon-Knife"
        ),
    )

    @field_validator("repository")
    @classmethod
    def validate_repository(
        cls,
        value: str,
    ) -> str:
        """
        Validate the repository input.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Repository cannot be empty."
            )

        # Do not allow insecure GitHub URLs.
        if value.startswith("http://"):
            raise ValueError(
                "Use HTTPS for GitHub repository URLs."
            )

        # Full GitHub URL.
        if value.startswith("https://"):

            if "github.com/" not in value.lower():
                raise ValueError(
                    "URL must point to github.com."
                )

        # owner/name format.
        else:

            parts = (
                value
                .strip("/")
                .split("/")
            )

            if len(parts) != 2:
                raise ValueError(
                    "Repository must use owner/name format."
                )

        return value


# ============================================================
# ARCHITECTURE PREVIEW
# ============================================================

@app.post("/architecture-preview")
def architecture_preview(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Return an architecture-focused preview without saving an analysis.

    This route is defined directly on the main app so the frontend's
    POST /architecture-preview URL exists even if the auxiliary router
    uses a different prefix or path.
    """
    try:
        result = run_repository_analysis(request.repository)
        if not isinstance(result, dict):
            raise ValueError("The repository analysis pipeline returned an invalid result.")

        repository_data = result.get("repository") or {}
        analysis_data = result.get("analysis") or {}
        structured = analysis_data.get("structured") or result.get("structured") or {}
        architecture = structured.get("architecture") or result.get("architecture")

        # Some pipeline versions return the architecture section as text
        # inside the generated report rather than as structured data.
        if architecture is None:
            report = analysis_data.get("report") or result.get("report") or result.get("final_report") or ""
            architecture = {
                "summary": "Architecture details were not returned as structured data.",
                "report_excerpt": report[:12000] if isinstance(report, str) else "",
            }

        return {
            "status": result.get("status", "completed"),
            "repository": repository_data.get("full_name") or request.repository,
            "architecture": architecture,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"Architecture preview error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Architecture preview failed. Please check the repository and try again.",
        ) from exc


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class RepositoryResponse(BaseModel):
    """
    Repository information returned by the API.
    """

    id: int
    name: str
    full_name: str
    url: str
    default_branch: str

    model_config = {
        "from_attributes": True
    }


class AnalysisResponse(BaseModel):
    """
    Complete saved analysis response.
    """

    id: int
    status: str
    report: str

    grounding_status: str
    evidence_count: int
    warnings: List[str]

    ai_grounding_status: str
    ai_evidence_count: int

    created_at: str

    repository: RepositoryResponse

    blockchain: Optional[dict] = None

    model_config = {
        "from_attributes": True
    }


class AnalyzeResponse(BaseModel):
    """
    Response returned after creating a new analysis.
    """

    status: str

    repository: RepositoryResponse

    analysis: AnalysisResponse


class AnalysisHistoryItem(BaseModel):
    """
    Compact analysis record used by the history endpoint.
    """

    id: int
    status: str

    grounding_status: str
    evidence_count: int

    ai_grounding_status: str
    ai_evidence_count: int

    created_at: str

    model_config = {
        "from_attributes": True
    }


class DashboardResponse(BaseModel):
    """
    Repository analysis dashboard statistics.
    """

    total_analyses: int
    repositories: int

    grounded_pass: int
    grounded_warning: int
    grounded_fail: int

    total_evidence: int
    total_warnings: int


class HealthResponse(BaseModel):
    """
    Health response.
    """

    status: str


class RootResponse(BaseModel):
    """
    Root endpoint response.
    """

    message: str
    status: str


# ============================================================
# BLOCKCHAIN SUMMARY BUILDER
# ============================================================

def build_blockchain_summary(
    result: dict,
) -> str:
    """
    Build the complete sanitized structured summary
    that will be stored on the blockchain.

    The detailed repository report and source code are
    intentionally not stored on-chain.

    The complete structured summary contains:
    - repository
    - executive summary
    - architecture
    - code quality
    - documentation
    - security
    - risk
    - recommendations
    - overall score
    """

    analysis_data = result.get(
        "analysis",
        {},
    )

    structured = analysis_data.get(
        "structured",
        {},
    )

    repository_data = result.get(
        "repository",
        {},
    )

    summary = {
        "repository": structured.get(
            "repository",
            repository_data.get(
                "full_name",
                "",
            ),
        ),
        "executive_summary": structured.get(
            "executive_summary",
            "",
        ),
        "architecture": structured.get(
            "architecture",
            {},
        ),
        "code_quality": structured.get(
            "code_quality",
            {},
        ),
        "documentation": structured.get(
            "documentation",
            {},
        ),
        "security": structured.get(
            "security",
            {},
        ),
        "risk": structured.get(
            "risk",
            {},
        ),
        "recommendations": structured.get(
            "recommendations",
            {},
        ),
        "overall": structured.get(
            "overall",
            {},
        ),
    }

    return json.dumps(
        summary,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get(
    "/",
    response_model=RootResponse,
)
def root() -> RootResponse:
    """
    Basic API information.
    """

    return RootResponse(
        message="RepoMind-AI backend is running",
        status="ok",
    )


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    """
    Health check endpoint.
    """

    return HealthResponse(
        status="healthy"
    )


# ============================================================
# AUTHENTICATION - REGISTER
# ============================================================

@app.post(
    "/auth/register",
    response_model=UserResponse,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a normal RepoMind-AI user.
    """

    username = request.username.strip()
    email = request.email.lower().strip()

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail=(
                "Username must contain "
                "at least 3 characters."
            ),
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least 8 characters."
            ),
        )

    existing_user = (
        db.query(User)
        .filter(
            or_(
                User.username == username,
                User.email == email,
            )
        )
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Username or email is already registered."
            ),
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(
            request.password
        ),
        role="user",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# AUTHENTICATION - LOGIN
# ============================================================

@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT.
    """

    user = authenticate_user(
        db=db,
        email=request.email,
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user,
    )


# ============================================================
# AUTHENTICATION - CURRENT USER
# ============================================================

@app.get(
    "/auth/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Return the currently authenticated user.
    """

    return current_user


# ============================================================
# ANALYZE REPOSITORY
# ============================================================

@app.post("/analyze")
def analyze_repository(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run the complete RepoMind-AI analysis pipeline.

    Flow:

    GitHub repository
          ↓
    AI analysis pipeline
          ↓
    Grounded final report
          ↓
    Save repository
          ↓
    Save analysis
          ↓
    Build summarized blockchain record
          ↓
    Register summary on blockchain
          ↓
    Return result
    """

    try:

        # ----------------------------------------------------
        # 1. Run AI analysis
        # ----------------------------------------------------

        result = run_repository_analysis(
            request.repository
        )

        # ----------------------------------------------------
        # 2. Get repository data
        # ----------------------------------------------------

        repository_data = result.get(
            "repository",
            {},
        )

        # ----------------------------------------------------
        # 3. Save or update repository
        # ----------------------------------------------------

        repository = crud.get_or_create_repository(
            db=db,
            repository_data=repository_data,
        )

        # ----------------------------------------------------
        # 4. Save analysis
        # ----------------------------------------------------

        analysis = crud.create_analysis(
            db=db,
            repository=repository,
            result=result,
            user=current_user,
        )

        # ----------------------------------------------------
        # 5. Register summarized report on blockchain
        # ----------------------------------------------------

        blockchain_data = None

        try:

            blockchain_summary = (
                build_blockchain_summary(
                    result
                )
            )

            blockchain_service = (
                BlockchainService()
            )

            blockchain_data = (
                blockchain_service.register_analysis(
                    analysis_id=analysis.id,
                    repository=repository.full_name,
                    summary_report=blockchain_summary,
                )
            )

            blockchain_data["status"] = (
                "registered"
            )

        except Exception as blockchain_exc:

            print(
                "Blockchain registration error: "
                f"{blockchain_exc}"
            )

            blockchain_data = {
                "status": "failed",
                "error": str(
                    blockchain_exc
                ),
            }

        # ----------------------------------------------------
        # 6. Build response
        # ----------------------------------------------------

        return AnalyzeResponse(

            status=result.get(
                "status",
                "completed",
            ),

            repository=RepositoryResponse(
                id=repository.id,
                name=repository.name,
                full_name=repository.full_name,
                url=repository.url,
                default_branch=repository.default_branch,
            ),

            analysis=AnalysisResponse(
                id=analysis.id,
                status=analysis.status,
                report=analysis.report,
                grounding_status=(
                    analysis.grounding_status
                ),
                evidence_count=(
                    analysis.evidence_count
                ),
                warnings=(
                    analysis.warnings or []
                ),
                ai_grounding_status=(
                    analysis.ai_grounding_status
                ),
                ai_evidence_count=(
                    analysis.ai_evidence_count
                ),
                created_at=(
                    analysis.created_at.isoformat()
                ),
                repository=RepositoryResponse(
                    id=repository.id,
                    name=repository.name,
                    full_name=repository.full_name,
                    url=repository.url,
                    default_branch=(
                        repository.default_branch
                    ),
                ),
                blockchain=blockchain_data,
            ),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        print(
            f"Repository analysis error: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Repository analysis failed. "
                "Please check the repository "
                "and try again."
            ),
        ) from exc


# ============================================================
# GET ALL ANALYSIS HISTORY
# ============================================================

@app.get(
    "/analyses",
    response_model=List[AnalysisHistoryItem],
)
def get_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve recent analysis history.

    Normal users see only their own analyses.
    Administrators can see all analyses.
    """

    query = db.query(Analysis)

    if current_user.role != "admin":

        query = query.filter(
            Analysis.user_id == current_user.id
        )

    analyses = (
        query
        .order_by(
            Analysis.created_at.desc()
        )
        .limit(50)
        .all()
    )

    return [
        AnalysisHistoryItem(
            id=analysis.id,
            status=analysis.status,
            grounding_status=(
                analysis.grounding_status
            ),
            evidence_count=(
                analysis.evidence_count
            ),
            ai_grounding_status=(
                analysis.ai_grounding_status
            ),
            ai_evidence_count=(
                analysis.ai_evidence_count
            ),
            created_at=(
                analysis.created_at.isoformat()
            ),
        )
        for analysis in analyses
    ]


# ============================================================
# GET SINGLE ANALYSIS
# ============================================================

@app.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResponse,
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    """
    Retrieve one saved analysis.

    Normal users can access only their own analyses.
    Administrators can access all analyses.
    """

    analysis = crud.get_analysis(
        db=db,
        analysis_id=analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    if (
        analysis.user_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this analysis."
            ),
        )

    # --------------------------------------------------------
    # Repository
    # --------------------------------------------------------

    repository = crud.get_repository(
        db=db,
        repository_id=analysis.repository_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Repository associated with "
                "analysis not found."
            ),
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return AnalysisResponse(
        id=analysis.id,
        status=analysis.status,
        report=analysis.report,
        grounding_status=(
            analysis.grounding_status
        ),
        evidence_count=(
            analysis.evidence_count
        ),
        warnings=(
            analysis.warnings or []
        ),
        ai_grounding_status=(
            analysis.ai_grounding_status
        ),
        ai_evidence_count=(
            analysis.ai_evidence_count
        ),
        created_at=(
            analysis.created_at.isoformat()
        ),
        repository=RepositoryResponse(
            id=repository.id,
            name=repository.name,
            full_name=repository.full_name,
            url=repository.url,
            default_branch=repository.default_branch,
        ),
        blockchain=None,
    )


# ============================================================
# GET STRUCTURED ANALYSIS
# ============================================================

@app.get(
    "/analyses/{analysis_id}/structured"
)
def get_structured_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the structured analysis and deterministic
    scoring for a previously completed analysis.
    """

    analysis = crud.get_analysis(
        db=db,
        analysis_id=analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    if (
        analysis.user_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this analysis."
            ),
        )

    # --------------------------------------------------------
    # Structured analysis
    # --------------------------------------------------------

    structured = (
        analysis.structured_analysis
    )

    if structured is None:

        structured_data = (
            build_structured_analysis(
                repository_data={
                    "name": (
                        analysis.repository.name
                    ),
                    "full_name": (
                        analysis.repository.full_name
                    ),
                    "url": (
                        analysis.repository.url
                    ),
                    "default_branch": (
                        analysis.repository.default_branch
                    ),
                },
                raw_ai_report=analysis.report,
            )
        )

        structured = StructuredAnalysis(
            analysis_id=analysis.id,
            repository=(
                structured_data.repository
            ),
            executive_summary=(
                structured_data.executive_summary
            ),
            architecture=(
                structured_data.architecture.to_dict()
            ),
            code_quality=(
                structured_data.code_quality.to_dict()
            ),
            documentation=(
                structured_data.documentation.to_dict()
            ),
            security=(
                structured_data.security.to_dict()
            ),
            risk=(
                structured_data.risk.to_dict()
            ),
            recommendations=(
                structured_data.recommendations.to_dict()
            ),
        )

        db.add(structured)
        db.commit()
        db.refresh(structured)

    # --------------------------------------------------------
    # Calculate overall score
    # --------------------------------------------------------

    categories = {
        "architecture": (
            structured.architecture
        ),
        "code_quality": (
            structured.code_quality
        ),
        "documentation": (
            structured.documentation
        ),
        "security": (
            structured.security
        ),
        "risk": (
            structured.risk
        ),
    }

    overall = (
        calculate_overall_from_categories(
            categories
        )
    )

    # --------------------------------------------------------
    # Return structured data
    # --------------------------------------------------------

    return {
        "analysis_id": (
            structured.analysis_id
        ),
        "repository": (
            structured.repository
        ),
        "executive_summary": (
            structured.executive_summary
        ),
        "overall": overall,
        "architecture": (
            structured.architecture
        ),
        "code_quality": (
            structured.code_quality
        ),
        "documentation": (
            structured.documentation
        ),
        "security": (
            structured.security
        ),
        "risk": (
            structured.risk
        ),
        "recommendations": (
            structured.recommendations
        ),
        "created_at": (
            structured.created_at
        ),
    }

# ============================================================
# VERIFY BLOCKCHAIN INTEGRITY
# ============================================================

@app.get(
    "/analyses/{analysis_id}/verify"
)
def verify_analysis_blockchain(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verify that the saved structured analysis matches
    the report summary registered on the blockchain.
    """

    analysis = crud.get_analysis(
        db=db,
        analysis_id=analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    if (
        analysis.user_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this analysis."
            ),
        )

    # --------------------------------------------------------
    # Structured analysis
    # --------------------------------------------------------

    structured = (
        analysis.structured_analysis
    )

    if structured is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Structured analysis not found."
            ),
        )

    # --------------------------------------------------------
    # Reconstruct the same blockchain summary
    # --------------------------------------------------------

    categories = {
        "architecture": (
            structured.architecture or {}
        ),
        "code_quality": (
            structured.code_quality or {}
        ),
        "documentation": (
            structured.documentation or {}
        ),
        "security": (
            structured.security or {}
        ),
        "risk": (
            structured.risk or {}
        ),
    }

    overall = (
        calculate_overall_from_categories(
            categories
        )
    )

    blockchain_summary = json.dumps(
        {
            "repository": (
                structured.repository
            ),
            "executive_summary": (
                structured.executive_summary
            ),
            "architecture": (
                structured.architecture or {}
            ),
            "code_quality": (
                structured.code_quality or {}
            ),
            "documentation": (
                structured.documentation or {}
            ),
            "security": (
                structured.security or {}
            ),
            "risk": (
                structured.risk or {}
            ),
            "recommendations": (
                structured.recommendations or {}
            ),
            "overall": overall,
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )

    # --------------------------------------------------------
    # Blockchain verification
    # --------------------------------------------------------

    try:
        blockchain_service = (
            BlockchainService()
        )

        verified = (
            blockchain_service.verify_analysis(
                analysis_id=analysis.id,
                summary_report=blockchain_summary,
            )
        )

    except Exception as blockchain_exc:
        return {
            "analysis_id": analysis.id,
            "verified": False,
            "status": "error",
            "message": (
                "Blockchain verification could "
                "not be completed."
            ),
            "error": str(
                blockchain_exc
            ),
        }

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    if verified:
        message = (
            "Analysis report matches the "
            "blockchain record."
        )
    else:
        message = (
            "Analysis report does not match "
            "the blockchain record."
        )

    return {
        "analysis_id": analysis.id,
        "verified": verified,
        "status": (
            "verified"
            if verified
            else "mismatch"
        ),
        "message": message,
    }
# ============================================================
# DASHBOARD
# ============================================================

@app.get(
    "/dashboard",
    response_model=DashboardResponse,
)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """
    Return aggregate RepoMind-AI analytics.

    Normal users see statistics for their own analyses.
    Administrators see statistics for all analyses.
    """

    query = db.query(Analysis)

    if current_user.role != "admin":

        query = query.filter(
            Analysis.user_id == current_user.id
        )

    analyses = (
        query
        .order_by(
            Analysis.created_at.desc()
        )
        .limit(1000)
        .all()
    )

    return DashboardResponse(
        total_analyses=len(
            analyses
        ),

        repositories=len(
            {
                analysis.repository_id
                for analysis in analyses
            }
        ),

        grounded_pass=sum(
            analysis.grounding_status == "PASS"
            for analysis in analyses
        ),

        grounded_warning=sum(
            analysis.grounding_status == "WARNING"
            for analysis in analyses
        ),

        grounded_fail=sum(
            analysis.grounding_status == "FAIL"
            for analysis in analyses
        ),

        total_evidence=sum(
            analysis.evidence_count or 0
            for analysis in analyses
        ),

        total_warnings=sum(
            len(
                analysis.warnings or []
            )
            for analysis in analyses
        ),
    )


# ============================================================
# ANALYSIS INSIGHTS
# ============================================================

@app.get(
    "/analyses/{analysis_id}/insights"
)
def get_analysis_insights(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return structured dashboard insights
    for one saved analysis.
    """

    analysis = crud.get_analysis(
        db=db,
        analysis_id=analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    if (
        analysis.user_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this analysis."
            ),
        )

    insights = build_insights(
        analysis.report
    )

    return {
        "analysis_id": analysis.id,
        "repository_id": (
            analysis.repository_id
        ),
        "grounding_status": (
            analysis.grounding_status
        ),
        "evidence_count": (
            analysis.evidence_count
        ),
        **insights,
    }


# ============================================================
# ADMIN - USERS
# ============================================================

@app.get(
    "/admin/users",
)
def admin_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_admin
    ),
):
    """
    Return all registered users.

    Only administrators can access this endpoint.
    """

    users = (
        db.query(User)
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]
