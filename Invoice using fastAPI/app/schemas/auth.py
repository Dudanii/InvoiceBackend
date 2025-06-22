from pydantic import BaseModel, EmailStr
from .users import UserOut 

class UserRegister(BaseModel):
    user_name: str
    email: EmailStr
    password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenWithUser(Token):        
    user: UserOut