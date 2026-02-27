import uuid

from sqlalchemy.dialects.postgresql import UUID
import datetime
from database.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime

class User(Base):
  __tablename__ = "users"
  id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
  username = Column(String, unique=True, index=True)
  name = Column(String)
  password = Column(String)
  nik = Column(String, unique=True, index=True)
  pob = Column(String)
  dob = Column(DateTime(timezone=True))
  isActive = Column(Boolean, default=False)
  