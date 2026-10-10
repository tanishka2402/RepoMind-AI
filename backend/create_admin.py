"""
Create the initial administrator account for RepoMind-AI.

Environment variables:

    REPOMIND_ADMIN_USERNAME
    REPOMIND_ADMIN_EMAIL
    REPOMIND_ADMIN_PASSWORD

Example:

    export REPOMIND_ADMIN_USERNAME="admin"
    export REPOMIND_ADMIN_EMAIL="admin@repomind.local"
    export REPOMIND_ADMIN_PASSWORD="ChangeThisPassword123!"
    python create_admin.py
"""

import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.abspath(__file__)
    ),
)

from app.database import SessionLocal, init_db
from app.models import User
from app.auth import hash_password


ADMIN_USERNAME = os.getenv(
    "REPOMIND_ADMIN_USERNAME",
    "admin",
)

ADMIN_EMAIL = os.getenv(
    "REPOMIND_ADMIN_EMAIL",
    "admin@repomind.local",
)

ADMIN_PASSWORD = os.getenv(
    "REPOMIND_ADMIN_PASSWORD",
)


def main():
    if not ADMIN_PASSWORD:
        raise RuntimeError(
            "REPOMIND_ADMIN_PASSWORD is not set."
        )

    if len(ADMIN_PASSWORD) < 12:
        raise RuntimeError(
            "Admin password must contain at least 12 characters."
        )

    init_db()

    db = SessionLocal()

    try:
        existing = (
            db.query(User)
            .filter(
                User.email == ADMIN_EMAIL.lower()
            )
            .first()
        )

        if existing:
            print(
                "Admin account already exists."
            )
            return

        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL.lower(),
            password_hash=hash_password(
                ADMIN_PASSWORD
            ),
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print(
            f"Admin created: {ADMIN_EMAIL}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()