from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.auth import router as auth_router
from app.api.routes.companies import router as companies_router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
app.include_router(auth_router)
app.include_router(companies_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/health/db", tags=["health"])
def database_health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {"status": "healthy"}
