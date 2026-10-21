import os
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-before-deployment")
ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()
bearer = HTTPBearer()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)

def create_access_token(user_id: int, role: str) -> str:
    payload = {"sub": str(user_id), "role": role,
               "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(role: str):
    def checker(user: User = Depends(current_user)):
        if user.role != role:
            raise HTTPException(status_code=403, detail=f"{role} role required")
        return user
    return checker
