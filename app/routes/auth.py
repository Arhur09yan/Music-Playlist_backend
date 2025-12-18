from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService
from app.utils.security import decode_token
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/register", response_model=UserResponse)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    user = AuthService.register(db, user_create)
    return user

@router.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    result = AuthService.login(db, user_login)
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "user": {
            "id": result["user"].id,
            "email": result["user"].email,
            "username": result["user"].username
        }
    }

@router.post("/refresh")
def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = int(payload.get("sub"))
    user = AuthService.get_current_user(db, user_id)
    
    from app.utils.security import create_access_token
    new_access_token = create_access_token({"sub": str(user.id)})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = int(payload.get("sub"))
    user = AuthService.get_current_user(db, user_id)
    return user
