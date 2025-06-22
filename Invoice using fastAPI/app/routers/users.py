from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.core.security import hash_password
from app.models import models
from app.schemas.users import UserCreate, UserOut, UserRoleUpdate

router = APIRouter()

# ---------- helpers --------------------------------------------------------- #

def generate_user_id_code(role: str, db: Session):
    """Generate A1 / UM1 / U1 style codes."""
    prefix = {"ADMIN": "A", "UNIT_MANAGER": "UM", "USER": "U"}.get(role.upper())
    count  = db.query(models.User).filter(models.User.role == role.upper()).count()
    return f"{prefix}{count+1}"

def visible_users_for(current: models.User, db: Session):
    """Return a query for users the caller may view."""
    q = db.query(models.User)
    if current.role == "ADMIN":
        return q
    if current.role == "UNIT_MANAGER":
        ids = [u.id for u in current.created_users] + [current.id]
        return q.filter(models.User.id.in_(ids))
    return q.filter(models.User.id == current.id)

# --------------------------------------------------------------------------- #

# GET /users/  -------------------------------------------------------------- #
@router.get("/", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user)
):
    return visible_users_for(current, db).all()

# POST /users/  ------------------------------------------------------------- #
@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user)
):
    # role checks
    role = payload.role.upper()
    if role not in ("ADMIN", "UNIT_MANAGER", "USER"):
        raise HTTPException(400, "Unsupported role")

    if current.role == "USER":
        raise HTTPException(403, "Users cannot create accounts")
    if current.role == "UNIT_MANAGER" and role != "USER":
        raise HTTPException(403, "Unit Managers may create only USER accounts")

    # email uniqueness
    if db.query(models.User).filter_by(email=payload.email).first():
        raise HTTPException(400, "Email already registered")

    new_user = models.User(
        user_name    = payload.user_name,
        email        = payload.email,
        password     = hash_password(payload.password),
        role         = role,
        user_id_code = generate_user_id_code(role, db),
        created_by_id= current.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# PATCH /users/{id}  -------------------------------------------------------- #
@router.patch("/{user_id}", response_model=UserOut)
def update_role(
    user_id: int,
    body: UserRoleUpdate,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user)
):
    if current.role != "ADMIN":
        raise HTTPException(403, "Only admins may change roles")

    target = db.query(models.User).get(user_id)
    if not target:
        raise HTTPException(404, "User not found")

    target.role = body.role.upper()
    db.commit()
    db.refresh(target)
    return target

# DELETE /users/{id}  ------------------------------------------------------- #
@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user)
):
    if current.role != "ADMIN":
        raise HTTPException(403, "Only admins may delete users")

    target = db.query(models.User).get(user_id)
    if not target:
        raise HTTPException(404, "User not found")

    db.delete(target)
    db.commit()
