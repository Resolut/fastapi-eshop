import os
from datetime import timedelta, timezone, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import jwt

from app.backend.db_depends import get_db
from app.models.user import User
from app.schemas import CreateUser

load_dotenv()

router = APIRouter(prefix='/auth', tags=['auth'])
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(db: Annotated[AsyncSession, Depends(get_db)], create_user: CreateUser):
    await db.execute(insert(User).values(first_name=create_user.first_name,
                                         last_name=create_user.last_name,
                                         username=create_user.username,
                                         email=create_user.email,
                                         hashed_password=bcrypt_context.hash(create_user.password),
                                         ))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


async def authenticate_user(db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str):
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.hashed_password) or user.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post('/token')
async def login(db: Annotated[AsyncSession, Depends(get_db)], form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(db, form_data.username, form_data.password)
    token = await create_access_token(user.username, user.id, user.is_admin, user.is_supplier, user.is_customer, expires_delta=timedelta(minutes=20))

    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.get('/read_current_user')
async def read_current_user(user: User = Depends(oauth2_scheme)):
    return user


async def create_access_token(username: str, user_id: int, is_admin: bool, is_supplier: bool, is_customer: bool, expires_delta: timedelta = timedelta(minutes=15)):
    payload = {
        'sub': username,
        'id': user_id,
        'is_admin': is_admin,
        'is_supplier': is_supplier,
        'is_customer': is_customer,
        'exp': int((datetime.now(timezone.utc) + expires_delta).timestamp()),
    }

    return jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm=os.getenv('ALGORITHM'))
