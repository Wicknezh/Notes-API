from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.deps import CurrentUser, DbSession, OptionalUser

from app.models import Role, User
from app.schemas import Token, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession, caller: OptionalUser):

    if data.role == "admin":
        if caller is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Log in as an admin to create an admin account",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if caller.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create admin accounts",
            )

    existing = db.scalar(select(User).where(User.username == data.username))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        role=Role(data.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    user = db.scalar(select(User).where(User.username == form.username))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user