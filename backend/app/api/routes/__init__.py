"""API route modules grouped by feature."""

from fastapi import APIRouter

from app.api.routes import (
    alerts,
    auth,
    drivers,
    health,
    phcs,
    predictions,
    routes,
    shipments,
    users,
    vehicles,
    warehouses,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(warehouses.router)
api_router.include_router(phcs.router)
api_router.include_router(drivers.router)
api_router.include_router(vehicles.router)
api_router.include_router(shipments.router)
api_router.include_router(routes.router)
api_router.include_router(predictions.router)
api_router.include_router(alerts.router)
