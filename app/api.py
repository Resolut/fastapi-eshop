from fastapi import FastAPI
from app.routers.categories import router as categories_router
from app.routers.products import router as products_router
from app.routers.auth import router as auth_router
from app.routers.permission import router as permission_router

app = FastAPI()


@app.get("/")
async def welcome():
    return {"message": "My e-commerce app"}

app.include_router(categories_router)
app.include_router(products_router)
app.include_router(auth_router)
app.include_router(permission_router)