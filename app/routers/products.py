from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from slugify import slugify
from sqlalchemy import select, insert, update
from sqlalchemy.orm import Session

from app.backend.db_depends import get_db
from app.models import Product, Category
from app.schemas import CreateProduct

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(db: Annotated[Session, Depends(get_db)]):
    products = db.scalars(select(Product).join(Category).where(
        Product.is_active == True,
        Category.is_active == True,
        Product.stock > 0
    )).all()

    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no products'
        )

    return products


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_product(db: Annotated[Session, Depends(get_db)], product: CreateProduct):
    category = db.scalar(select(Category).where(Category.id == product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    db.execute(insert(Product).values(
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=product.image_url,
        stock=product.stock,
        category_id=product.category,
        rating=0.0,
        slug=slugify(product.name)
    ))
    db.commit()

    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successfully created product',
    }


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[Session, Depends(get_db)], category_slug: str):
    category = db.scalar(select(Category).where(Category.slug == category_slug))

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )
    subcategories = db.scalars(select(Category).where(Category.parent_id == category.id)).all()
    products = db.scalars(
        select(Product).filter(Product.category_id.in_([category.id] + [s.id for s in subcategories])).where(
            Product.is_active == True, Product.stock > 0)).all()
    return products


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[Session, Depends(get_db)], product_slug: str):
    product = db.scalar(select(Product).where(Product.slug == product_slug, Product.is_active == True, Product.stock > 0))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )
    return product


@router.put('/{product_slug}')
async def update_product(db: Annotated[Session, Depends(get_db)], product_slug: str, update_product_model: CreateProduct):
    update_product= db.scalar(select(Product).where(Product.slug == product_slug))
    if update_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )
    category = db.scalar(select(Category).where(Category.id == update_product_model.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )

    db.execute(update(Product).where(Product.slug == product_slug).values(
        name=update_product_model.name,
        description=update_product_model.description,
        price=update_product_model.price,
        image_url=update_product_model.image_url,
        stock=update_product_model.stock,
        category_id=update_product_model.category,
        slug=slugify(update_product_model.name)
    ))
    db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful',
    }


@router.delete('/')
async def delete_product(db: Annotated[Session, Depends(get_db)], product_slug: str):
    product = db.scalar(select(Product).where(Product.slug == product_slug))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )
    db.execute(update(Product).where(Product.slug == product_slug).values(is_active=False))
    db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful',
    }
