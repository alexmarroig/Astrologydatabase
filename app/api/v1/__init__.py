"""API v1 router aggregator."""
from fastapi import APIRouter
from app.api.v1.routers.reference import router as reference_router
from app.api.v1.routers.editorial import router as editorial_router
from app.api.v1.routers.chart import router as chart_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(reference_router, prefix="/reference")
api_v1_router.include_router(editorial_router, prefix="/editorial")
api_v1_router.include_router(chart_router, prefix="/charts")
