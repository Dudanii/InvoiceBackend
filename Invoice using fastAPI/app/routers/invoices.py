from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import SessionLocal
from app.models.models import Invoice
from app.schemas.invoices import InvoiceCreate, InvoiceRead
from datetime import datetime
from app.core.security import decode_token
from fastapi.security import OAuth2PasswordBearer
from app.models import models
from fastapi import Body
from app.core.dependencies import get_current_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dummy auth for now - Changed now
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(models.User).get(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

# Helper to get financial year from date
def get_financial_year(date_obj):
    if date_obj.month >= 4:
        return f"{date_obj.year}"
    else:
        return f"{date_obj.year - 1}"

@router.post("/", response_model=InvoiceRead)
def create_invoice(data: InvoiceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    fy = get_financial_year(data.invoice_date)

    # Check uniqueness of invoice_number per financial year
    existing = db.query(Invoice).filter_by(invoice_number=data.invoice_number, financial_year=fy).first()
    if existing:
        raise HTTPException(status_code=400, detail="Invoice number already exists for this financial year")
    
    invoice = Invoice(
        invoice_number=data.invoice_number,
        invoice_date=data.invoice_date,
        invoice_amount=data.invoice_amount,
        created_by_id=current_user.id,
        financial_year=fy
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

@router.get("/", response_model=List[InvoiceRead])
def get_invoices(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
    fy: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    query = db.query(Invoice)

    if fy:
        query = query.filter(Invoice.financial_year == fy)
    if start_date and end_date:
        query = query.filter(Invoice.invoice_date.between(start_date, end_date))
    if search:
        query = query.filter(Invoice.invoice_number.ilike(f"%{search}%"))

    return query.offset(skip).limit(limit).all()

@router.put("/{invoice_number}", response_model=InvoiceRead)
def update_invoice(invoice_number: str, data: InvoiceCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    invoice = db.query(Invoice).filter_by(invoice_number=invoice_number).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.invoice_date = data.invoice_date
    invoice.invoice_amount = data.invoice_amount
    db.commit()
    db.refresh(invoice)
    return invoice

@router.delete("/")
def delete_invoices(
    invoice_numbers: List[str] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not invoice_numbers:
        raise HTTPException(status_code=400, detail="No invoice numbers provided.")

    # Start the base query
    query = db.query(Invoice).filter(Invoice.invoice_number.in_(invoice_numbers))

    # Role-Based Access Control
    if current_user.role == "ADMIN":
        pass  # Admins can delete anything
    elif current_user.role == "UNIT_MANAGER":
        # Managers can delete invoices of users they created
        allowed_user_ids = [u.id for u in current_user.created_users] + [current_user.id]
        query = query.filter(Invoice.created_by_id.in_(allowed_user_ids))
    elif current_user.role == "USER":
        # Users can only delete their own invoices
        query = query.filter(Invoice.created_by_id == current_user.id)
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    # Perform delete
    to_delete = query.all()
    if not to_delete:
        raise HTTPException(status_code=404, detail="No matching invoices found or access denied.")

    deleted_count = len(to_delete)
    for inv in to_delete:
        db.delete(inv)
    db.commit()

    return {"message": f"{deleted_count} invoice(s) deleted successfully."}

@router.get("/", response_model=List[InvoiceRead])
def get_invoices(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    fy: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    query = db.query(Invoice)

    if current_user.role == "USER":
        query = query.filter(Invoice.created_by_id == current_user.id)
    elif current_user.role == "UNIT_MANAGER":
        # Get IDs of users this manager created
        user_ids = [u.id for u in current_user.created_users]
        query = query.filter(Invoice.created_by_id.in_(user_ids + [current_user.id]))

    if fy:
        query = query.filter(Invoice.financial_year == fy)
    if start_date and end_date:
        query = query.filter(Invoice.invoice_date.between(start_date, end_date))
    if search:
        query = query.filter(Invoice.invoice_number.ilike(f"%{search}%"))

    return query.offset(skip).limit(limit).all()
