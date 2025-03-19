from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine('postgresql+asyncpg://eshop:eshoppwd@localhost:5432/eshopdb', echo=True)
session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass
