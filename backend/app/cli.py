import argparse

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, init_db
from app.models import User
from app.services.auth import hash_password


def create_admin(email: str, password: str) -> None:
    init_db()
    db = SessionLocal()
    try:
        user = User(email=email.lower().strip(), hashed_password=hash_password(password), is_active=True, is_admin=True)
        db.add(user)
        db.commit()
        print(f"Created admin user: {user.email}")
    except IntegrityError:
        db.rollback()
        raise SystemExit(f"User already exists: {email}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Scanner admin commands")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_admin_parser = subparsers.add_parser("create-admin", help="Create the first private admin user")
    create_admin_parser.add_argument("--email", required=True)
    create_admin_parser.add_argument("--password", required=True)
    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin(args.email, args.password)


if __name__ == "__main__":
    main()
