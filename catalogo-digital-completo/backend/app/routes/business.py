from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.business import BusinessModel, BusinessCategory
router = APIRouter(prefix="/api/business", tags=["business"])
@router.get("/models")
def models(db: Session = Depends(get_db)): return db.query(BusinessModel).filter(BusinessModel.active.is_(True)).order_by(BusinessModel.sort_order, BusinessModel.id).all()
@router.get("/categories")
def categories(db: Session = Depends(get_db)): return db.query(BusinessCategory).filter(BusinessCategory.active.is_(True)).order_by(BusinessCategory.sort_order, BusinessCategory.id).all()
