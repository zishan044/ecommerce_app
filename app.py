import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth_router, products_router, users_router


def get_app() -> FastAPI:
    app = FastAPI(title="ecommerce-app")
    
    # CORS configuration
    # Allow all origins in development, can be restricted via CORS_ORIGINS env var
    cors_origins_env = os.getenv("CORS_ORIGINS", "*")
    if cors_origins_env == "*":
        cors_origins = ["*"]
        allow_credentials = False  # Cannot use credentials with wildcard origin
    else:
        cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
        allow_credentials = True
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(auth_router)
    app.include_router(products_router)
    app.include_router(users_router)
    return app


app = get_app()
