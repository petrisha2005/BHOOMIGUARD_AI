"""Provision one development officer in an already-migrated BhoomiGuard database.

This command is intentionally explicit and never contains a password. It is not a
production account-management service; production accounts must be provisioned
through an approved administrator process.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision or reset a development BhoomiGuard officer account.")
    parser.add_argument("--name", help="Officer display name; required when creating an account")
    parser.add_argument("--email", required=True, help="Officer email address")
    parser.add_argument("--role", default="officer", help="Stored role label; endpoint RBAC is not implemented")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Reset an existing development officer password after an interactive confirmation.",
    )
    return parser.parse_args()


def main() -> None:
    if os.environ.get("BHOOMIGUARD_ALLOW_DEVELOPMENT_SEED") != "true":
        raise SystemExit(
            "Refusing to provision an account. Set BHOOMIGUARD_ALLOW_DEVELOPMENT_SEED=true for this one command."
        )
    args = parse_args()
    password = getpass.getpass("Development officer password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords did not match.")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == args.email))
        if existing is not None:
            if not args.reset_password:
                raise SystemExit("An account with this email already exists; no changes were made.")
            existing.password_hash = hash_password(password)
            db.commit()
            print(f"Reset development officer password for {args.email}.")
            return
        if not args.name:
            raise SystemExit("--name is required when creating an account.")
        if args.reset_password:
            raise SystemExit("No account exists for this email; no password was reset.")
        db.add(User(name=args.name, email=args.email, role=args.role, password_hash=hash_password(password)))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Provisioned development officer account for {args.email}.")


if __name__ == "__main__":
    main()
