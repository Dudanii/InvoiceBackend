from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import models
from app.schemas import users
from app.schemas.auth import UserRegister, UserLogin, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from typing import Optional
from app.schemas.users import UserOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_user_id_code(role: str, db: Session):
    prefix = {
        "ADMIN": "A",
        "UNIT_MANAGER": "UM",
        "USER": "U"
    }.get(role.upper())

    if not prefix:
        raise HTTPException(status_code=400, detail="Invalid role for ID generation")

    # Count users with same role
    count = db.query(models.User).filter(models.User.role == role.upper()).count()
    return f"{prefix}{count + 1}"


@router.post("/register", response_model=Token)
def register(
    user: UserRegister,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)  # For RBAC
):
    # Check if user already exists
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # RBAC Logic
    if current_user:
        # Only ADMINs can create ADMINs or UM
        if user.role.upper() in ["ADMIN", "UNIT_MANAGER"] and current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Only admins can create admins or managers")

        # UNIT_MANAGER can only create USERs
        if current_user.role == "UNIT_MANAGER" and user.role.upper() != "USER":
            raise HTTPException(status_code=403, detail="Managers can only create USERs")

        creator_id = current_user.id
    else:
        # If no logged-in user (self-signup scenario)
        creator_id = None

    # Generate user_id_code
    user_id_code = generate_user_id_code(user.role, db)

    # Create user
    hashed_pwd = hash_password(user.password)
    new_user = models.User(
        user_name=user.user_name,
        email=user.email,
        password=hashed_pwd,
        role=user.role.upper(),
        user_id_code=user_id_code,
        created_by_id=creator_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id)})
    return {"access_token": token}


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(models.User)
          .filter(models.User.email == credentials.email)
          .first()
    )
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    print(f"User role: {user.role}")  # This will print the role to your console
    print(f"User object: {user}") 
    token = create_access_token(
        {"sub": str(user.id), "role": user.role, "email": user.email}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": users.UserOut.model_validate(user)   
    }
