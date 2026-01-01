from fastapi import FastAPI

from routers import products_router, users_router


def get_app() -> FastAPI:
    app = FastAPI(title="ecommerce-app")
    app.include_router(products_router)
    app.include_router(users_router)
    return app


app = get_app()
