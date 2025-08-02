# pip install sqlachemy

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserImage(Base):
    __tablename__ = 'user_images'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    public_id = Column(String, nullable=True)
