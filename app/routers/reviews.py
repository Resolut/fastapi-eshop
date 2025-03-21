from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Review, Product
from app.routers.auth import get_current_user

router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Review).join(Product).where(Review.is_active == True,
                                                                     Product.is_active == True))
    if reviews is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no reviews'
        )

    return reviews.all()


@router.get('/{product_slug}')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    pass


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_review(db: Annotated[AsyncSession, Depends(get_db)],
                        get_user: Annotated[dict, Depends(get_current_user)]):
    pass


@router.get('/')
async def delete_reviews(db: Annotated[AsyncSession, Depends(get_db)], review_id: int,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )
    
    target_review = await db.scalar(select(Review).where(Review.id == review_id))
    if target_review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no review found'
        )

    target_review.is_active = False
    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Review delete is successful',
    }
