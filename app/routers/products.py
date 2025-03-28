from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from slugify import slugify
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Product, Category
from app.routers.auth import get_current_user
from app.schemas import CreateProduct

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).join(Category).where(Product.is_active == True,
                                                                     Category.is_active == True,
                                                                     Product.stock > 0))
    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no products'
        )

    return products.all()


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not (get_user.get('is_admin') or get_user.get('is_supplier')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    category = await db.scalar(select(Category).where(Category.id == product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )

    await db.execute(insert(Product).values(name=product.name,
                                            description=product.description,
                                            price=product.price,
                                            image_url=product.image_url,
                                            stock=product.stock,
                                            supplier_id=get_user.get('id'),
                                            category_id=product.category,
                                            rating=0.0,
                                            slug=slugify(product.name)))
    await db.commit()

    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successfully created product',
    }


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )
    subcategories = await db.scalars(select(Category).where(Category.parent_id == category.id))
    products = await db.scalars(
        select(Product).filter(Product.category_id.in_([category.id] + [s.id for s in subcategories.all()])).where(
            Product.is_active == True, Product.stock > 0))

    return products.all()


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug,
                                                    Product.is_active == True,
                                                    Product.stock > 0))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )

    return product


@router.put('/{product_slug}')
async def update_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str,
                         update_product_model: CreateProduct, get_user: Annotated[dict, Depends(get_current_user)]):
    renew_product = await get_product_only_for_admin_or_supplier(db, get_user, product_slug)

    category = await db.scalar(select(Category).where(Category.id == update_product_model.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )

    renew_product.name = update_product_model.name,
    renew_product.description = update_product_model.description,
    renew_product.price = update_product_model.price,
    renew_product.image_url = update_product_model.image_url,
    renew_product.stock = update_product_model.stock,
    renew_product.category_id = update_product_model.category,
    renew_product.slug = slugify(update_product_model.name)

    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful',
    }


@router.delete('/')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    product = await get_product_only_for_admin_or_supplier(db, get_user, product_slug)
    product.is_active = False
    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful',
    }


async def get_product_only_for_admin_or_supplier(db: Annotated[AsyncSession, Depends(get_db)],
                                                 get_user: Annotated[dict, Depends(get_current_user)],
                                                 product_slug: str):
    if not (get_user.get('is_admin') or get_user.get('is_supplier')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    target_product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if target_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )

    if not (get_user.get('id') == target_product.id or get_user.get('is_admin')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You are not authorized to use this method'
        )

    return target_product
