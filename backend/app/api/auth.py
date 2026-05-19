from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LoginRequest, TokenResponse, UserRead
from app.services.auth import authenticate_user, create_access_token, get_current_user
from app.services.logging import log_exception

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except Exception:
        log_exception("auth_login_exception", email=payload.email.lower().strip())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login service error")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    try:
        return {"access_token": create_access_token(user), "user": user}
    except Exception:
        log_exception("auth_token_exception", user_id=user.id, email=user.email)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token service error")


@router.get("/me", response_model=UserRead)
def me(user=Depends(get_current_user)):
    return user
