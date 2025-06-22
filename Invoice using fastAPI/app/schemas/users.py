from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    user_name: str
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str                 # plain text incoming

class UserOut(UserBase):
    id: int
    user_id_code: Optional[str]
    created_by_id: Optional[int]
    

    class Config:
        orm_mode = True
        from_attributes = True

class UserRoleUpdate(BaseModel):
    role: str
