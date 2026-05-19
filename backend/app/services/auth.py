from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY
from app.database import get_db
from app.models import User
from app.services.logging import log_exception, log_warning

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    normalized_email = email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).one_or_none()
    if not user or not user.is_active:
        log_warning("auth_login_failed", email=normalized_email, reason="unknown_or_inactive_user")
        return None
    try:
        password_ok = verify_password(password, user.hashed_password)
    except Exception:
        log_exception("auth_password_verify_exception", email=normalized_email)
        return None
    if not password_ok:
        log_warning("auth_login_failed", email=normalized_email, reason="invalid_password")
        return None
    return user


def create_access_token(user: User) -> str:
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "email": user.email, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise_auth_error()
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise_auth_error()
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user or not user.is_active:
        raise_auth_error()
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        log_warning("auth_admin_forbidden", user_id=user.id, email=user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


def raise_auth_error():
    log_warning("auth_required")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
