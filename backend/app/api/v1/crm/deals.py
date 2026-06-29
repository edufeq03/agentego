from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.get("/")
def list_deals(db: Session = Depends(get_db)):
    return {"message": "CRM Deals Endpoint"}
