from pydantic import BaseModel
from datetime import date
from typing import Optional

class InvoiceCreate(BaseModel):
    invoice_number: str
    invoice_date: date
    invoice_amount: float

class InvoiceRead(BaseModel):
    id: int
    invoice_number: str
    invoice_date: date
    invoice_amount: float
    financial_year: Optional[str]

    class Config:
        orm_mode = True
