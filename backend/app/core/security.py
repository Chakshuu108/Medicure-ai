from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Doctor, Hospital, Patient, Receptionist

security = HTTPBearer(auto_error=False)
settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    role = payload.get("role")
    user_id = payload.get("sub")
    if not role or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    if role == "admin":
        result = await db.execute(select(Hospital).where(Hospital.id == user_id))
        user = result.scalar_one_or_none()
    elif role == "doctor":
        result = await db.execute(select(Doctor).where(Doctor.id == user_id))
        user = result.scalar_one_or_none()
    elif role == "receptionist":
        result = await db.execute(select(Receptionist).where(Receptionist.id == user_id))
        user = result.scalar_one_or_none()
    elif role == "patient":
        result = await db.execute(select(Patient).where(Patient.id == user_id))
        user = result.scalar_one_or_none()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown role")

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {"role": role, "user": user, "user_id": user_id, "hospital_id": getattr(user, "hospital_id", None)}


def require_roles(*roles: str):
    async def checker(current: dict = Depends(get_current_user)) -> dict:
        if current["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current
    return checker
