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
"""
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from .insights import build_insights
from .database import get_db, init_db
from . import crud
from pathlib import Path
import sys
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AI_PATH = PROJECT_ROOT / "ai"

if str(AI_PATH) not in sys.path:
    sys.path.insert(0, str(AI_PATH))


# ============================================================
# AI IMPORT
# ============================================================

from backend_ai import analyze_repository


# ============================================================
# DATABASE IMPORTS
# ============================================================

from .database import get_db, init_db
from . import crud


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


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
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
    def validate_repository(cls, value: str) -> str:
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

            parts = value.strip("/").split("/")

            if len(parts) != 2:
                raise ValueError(
                    "Repository must use owner/name format."
                )

        return value


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
# ANALYZE REPOSITORY
# ============================================================

@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
def analyze(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """
    Run the RepoMind-AI analysis pipeline.

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
    Return result
    """

    try:

        # ----------------------------------------------------
        # 1. Run AI analysis
        # ----------------------------------------------------

        result = analyze_repository(
            request.repository
        )

        # ----------------------------------------------------
        # 2. Get repository data
        # ----------------------------------------------------

        repository_data = result.get(
            "repository",
            {}
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
        )

        # ----------------------------------------------------
        # 5. Build response
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
                grounding_status=analysis.grounding_status,
                evidence_count=analysis.evidence_count,
                warnings=analysis.warnings or [],
                ai_grounding_status=analysis.ai_grounding_status,
                ai_evidence_count=analysis.ai_evidence_count,
                created_at=analysis.created_at.isoformat(),
                repository=RepositoryResponse(
                    id=repository.id,
                    name=repository.name,
                    full_name=repository.full_name,
                    url=repository.url,
                    default_branch=repository.default_branch,
                ),
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
                "Please check the repository and try again."
            ),
        ) from exc


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
) -> AnalysisResponse:
    """
    Retrieve one saved analysis from the database.
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

    repository = crud.get_repository(
        db=db,
        repository_id=analysis.repository_id,
    )

    if repository is None:

        raise HTTPException(
            status_code=404,
            detail="Repository associated with analysis not found.",
        )

    return AnalysisResponse(
        id=analysis.id,
        status=analysis.status,
        report=analysis.report,
        grounding_status=analysis.grounding_status,
        evidence_count=analysis.evidence_count,
        warnings=analysis.warnings or [],
        ai_grounding_status=analysis.ai_grounding_status,
        ai_evidence_count=analysis.ai_evidence_count,
        created_at=analysis.created_at.isoformat(),
        repository=RepositoryResponse(
            id=repository.id,
            name=repository.name,
            full_name=repository.full_name,
            url=repository.url,
            default_branch=repository.default_branch,
        ),
    )


# ============================================================
# GET REPOSITORY ANALYSIS HISTORY
# ============================================================

@app.get(
    "/repositories/{repository_id}/analyses",
    response_model=List[AnalysisHistoryItem],
)
def get_repository_history(
    repository_id: int,
    db: Session = Depends(get_db),
) -> List[AnalysisHistoryItem]:
    """
    Retrieve all saved analyses for a repository.
    """

    repository = crud.get_repository(
        db=db,
        repository_id=repository_id,
    )

    if repository is None:

        raise HTTPException(
            status_code=404,
            detail="Repository not found.",
        )

    analyses = crud.get_repository_history(
        db=db,
        repository_id=repository_id,
    )

    return [
        AnalysisHistoryItem(
            id=analysis.id,
            status=analysis.status,
            grounding_status=analysis.grounding_status,
            evidence_count=analysis.evidence_count,
            ai_grounding_status=analysis.ai_grounding_status,
            ai_evidence_count=analysis.ai_evidence_count,
            created_at=analysis.created_at.isoformat(),
        )
        for analysis in analyses
    ]


# ============================================================
# GET ALL ANALYSIS HISTORY
# ============================================================

@app.get(
    "/analyses",
    response_model=List[AnalysisHistoryItem],
)
def get_all_analyses(
    db: Session = Depends(get_db),
) -> List[AnalysisHistoryItem]:
    """
    Retrieve recent analysis history.

    Default:
        50 most recent analyses.
    """

    analyses = crud.get_all_analyses(
        db=db,
        limit=50,
    )

    return [
        AnalysisHistoryItem(
            id=analysis.id,
            status=analysis.status,
            grounding_status=analysis.grounding_status,
            evidence_count=analysis.evidence_count,
            ai_grounding_status=analysis.ai_grounding_status,
            ai_evidence_count=analysis.ai_evidence_count,
            created_at=analysis.created_at.isoformat(),
        )
        for analysis in analyses
    ]


# ============================================================
# DASHBOARD ANALYTICS
# ============================================================

@app.get(
    "/dashboard",
    response_model=DashboardResponse,
)
def dashboard(
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """
    Return aggregate RepoMind-AI analytics.

    Statistics include:

    - Total analyses
    - Number of repositories
    - Grounding PASS count
    - Grounding WARNING count
    - Grounding FAIL count
    - Total evidence
    - Total warnings
    """
    # --------------------------------------------------------
    # Get analyses
    # --------------------------------------------------------

    analyses = crud.get_all_analyses(
        db=db,
        limit=1000,
    )

    # --------------------------------------------------------
    # Total analyses
    # --------------------------------------------------------

    total_analyses = len(analyses)

    # --------------------------------------------------------
    # Number of unique repositories
    # --------------------------------------------------------

    repositories = len(
        set(
            analysis.repository_id
            for analysis in analyses
        )
    )

    # --------------------------------------------------------
    # Grounding statistics
    # --------------------------------------------------------

    grounded_pass = sum(
        1
        for analysis in analyses
        if analysis.grounding_status == "PASS"
    )

    grounded_warning = sum(
        1
        for analysis in analyses
        if analysis.grounding_status == "WARNING"
    )

    grounded_fail = sum(
        1
        for analysis in analyses
        if analysis.grounding_status == "FAIL"
    )

    # --------------------------------------------------------
    # Evidence statistics
    # --------------------------------------------------------

    total_evidence = sum(
        analysis.evidence_count or 0
        for analysis in analyses
    )

    # --------------------------------------------------------
    # Warning statistics
    # --------------------------------------------------------

    total_warnings = sum(
        len(analysis.warnings or [])
        for analysis in analyses
    )

    # --------------------------------------------------------
    # Return dashboard data
    # --------------------------------------------------------

    return DashboardResponse(
        total_analyses=total_analyses,
        repositories=repositories,
        grounded_pass=grounded_pass,
        grounded_warning=grounded_warning,
        grounded_fail=grounded_fail,
        total_evidence=total_evidence,
        total_warnings=total_warnings,
    )


@app.get("/analyses/{analysis_id}/insights")
def get_analysis_insights(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """
    Return structured dashboard insights for one saved analysis.
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

    insights = build_insights(
        analysis.report
    )

    return {
        "analysis_id": analysis.id,
        "repository_id": analysis.repository_id,
        "grounding_status": analysis.grounding_status,
        "evidence_count": analysis.evidence_count,
        **insights,
    }
