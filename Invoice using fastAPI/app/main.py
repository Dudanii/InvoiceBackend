from fastapi import FastAPI
from app.routers import auth
from app.routers import invoices
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users

app = FastAPI(title="Invoice & User Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],  # React dev server and Backend server
    allow_credentials=True,
    allow_methods=["*"],                      # ← * means all, must include OPTIONS
    allow_headers=["Authorization", "Content-type"],                      # ← must include Authorization and Content-type
)
# Include route groups
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def root():
    return {"message": "Backend is up and running!"}
#Token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzUwNDY2MzY4fQ.qaKcN-nlXXuZ65bK7zg33MGXhK1VNzbGviZP6Wy31_s