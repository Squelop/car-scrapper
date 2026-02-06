from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, unique=True, index=True)
    source_url = Column(String)
    platform = Column(String)  # otomoto, olx, etc.
    
    brand = Column(String, index=True)
    model = Column(String, index=True)
    generation = Column(String, nullable=True)
    
    production_year = Column(Integer, nullable=True)
    fuel_type = Column(String, nullable=True)
    power = Column(Integer, nullable=True) # HP
    engine_capacity = Column(Float, nullable=True) # cm3
    
    price = Column(Float, nullable=True)
    currency = Column(String, default="PLN")
    
    mileage = Column(Integer, nullable=True) # km
    
    body_type = Column(String, nullable=True)
    color = Column(String, nullable=True)
    condition = Column(String, nullable=True) # used, new, damage
    
    location = Column(String, nullable=True)
    
    created_at_source = Column(String, nullable=True) # Raw string for now, parse if possible
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
