from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_engine("sqlite:///database.db", echo=True)
session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

