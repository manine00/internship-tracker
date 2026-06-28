from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db import Base

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    
    # AI-populated fields (Nullable because they start empty)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    position = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    
    # Core Email fields
    sent_date = Column(DateTime, default=datetime.utcnow)
    email_id = Column(String(255), unique=True)
    status = Column(String(50), default="Pending AI Analysis") 
    
    # --- NEW PIPELINE FIELDS ---
    raw_text = Column(Text, nullable=True) 
    ai_status = Column(String(50), default="PENDING") # PENDING, COMPLETED, FAILED

    company = relationship("Company", back_populates="applications")