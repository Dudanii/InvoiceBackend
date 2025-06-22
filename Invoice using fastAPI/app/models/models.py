from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Float, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum
from sqlalchemy.orm import backref, relationship


# Enum for role
class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    UNIT_MANAGER = "UNIT_MANAGER"
    USER = "USER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    user_id_code = Column(String, unique=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_users = relationship(
        "User",
        backref=backref("creator", remote_side=lambda: [User.id])
    )
    invoices = relationship("Invoice", back_populates="creator")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, nullable=False)
    invoice_date = Column(Date, nullable=False)
    invoice_amount = Column(Float, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    financial_year = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="invoices")
