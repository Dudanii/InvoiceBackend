from app.core.database import SessionLocal

try:
    db = SessionLocal()
    print("Connected to PostgreSQL database")
finally:
    db.close()
