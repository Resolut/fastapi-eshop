from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.backend.db import Base


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    comment = Column(String, nullable=True)
    comment_date = Column(DateTime, default=datetime.utcnow)
    grade = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship('User', back_populates='reviews')
    product = relationship('Product', back_populates='reviews')
