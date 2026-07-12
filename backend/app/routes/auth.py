from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..config import settings
from ..auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

_engine = None
_SessionLocal = None


def _get_session():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(req: RegisterRequest):
    SessionLocal = _get_session()

    with SessionLocal() as session:
        existing = session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": req.email},
        ).fetchone()

        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        existing_user = session.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": req.username},
        ).fetchone()

        if existing_user:
            raise HTTPException(status_code=409, detail="Username already taken")

        hashed = hash_password(req.password)
        result = session.execute(
            text("INSERT INTO users (email, username, password_hash) VALUES (:email, :username, :hash) RETURNING id"),
            {"email": req.email, "username": req.username, "hash": hashed},
        )
        user_id = result.fetchone()[0]
        session.commit()

    return UserResponse(id=user_id, email=req.email, username=req.username)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    SessionLocal = _get_session()

    with SessionLocal() as session:
        row = session.execute(
            text("SELECT id, password_hash FROM users WHERE email = :email"),
            {"email": req.email},
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, password_hash = row

    if not verify_password(req.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": str(user_id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)
