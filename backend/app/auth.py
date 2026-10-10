"""
Authentication and authorization utilities for RepoMind-AI.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .database import get_db
from .models import User


JWT_SECRET_KEY = os.getenv(
    "REPOMIND_JWT_SECRET",
    "CHANGE_THIS_IN_PRODUCTION",
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "REPOMIND_ACCESS_TOKEN_MINUTES",
        "60",
    )
)


password_hash = PasswordHash.recommended()

security = HTTPBearer(
    auto_error=False
)


def hash_password(password: str) -> str:
    """Hash a password securely."""
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """Verify a password."""
    return password_hash.verify(
        password,
        hashed_password,
    )


def create_access_token(
    user_id: int,
    role: str,
) -> str:
    """Create a JWT access token."""

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def authenticate_user(
    db: Session,
    email: str,
    password: str,
):
    """Authenticate a user."""

    user = (
        db.query(User)
        .filter(
            User.email == email.lower().strip()
        )
        .first()
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def get_authorization_token(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
) -> str:
    """Extract the Bearer token."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    return credentials.credentials


def get_current_user(
    token: str = Depends(
        get_authorization_token
    ),
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated user."""

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise ValueError(
                "Token subject missing."
            )

        user_id = int(user_id)

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        ) from exc

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    return user


def require_admin(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:
    """Require administrator role."""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return current_user
