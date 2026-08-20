from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.campaigns import router as campaigns_router
from app.api.v1.endpoints.contact_lists import router as contact_lists_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.imports import router as imports_router
from app.api.v1.endpoints.templates import router as templates_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.webhooks import router as webhooks_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(contact_lists_router, prefix="/contact-lists", tags=["Contact Lists & Subscribers"])
api_v1_router.include_router(imports_router, prefix="/imports", tags=["Imports"])
api_v1_router.include_router(templates_router, prefix="/templates", tags=["Templates"])
api_v1_router.include_router(campaigns_router, prefix="/campaigns", tags=["Campaigns"])
api_v1_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
