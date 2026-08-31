from fastapi import APIRouter

from app.api.routes.application_events import router as application_events_router
from app.api.routes.applications import router as applications_router
from app.api.routes.auth import router as auth_router
from app.api.routes.companies import router as companies_router

api_router = APIRouter(
    prefix="/api/v1",
)

api_router.include_router(auth_router)
api_router.include_router(companies_router)
api_router.include_router(applications_router)
api_router.include_router(application_events_router)
