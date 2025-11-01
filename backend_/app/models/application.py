from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db import Base

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    position = Column(String(255))
    sent_date = Column(DateTime, default=datetime.utcnow)
    email_id = Column(String(255))
    status = Column(String(50), default="Awaiting Reply")
    summary = Column(Text, nullable=True)

    company = relationship("Company", back_populates="applications")