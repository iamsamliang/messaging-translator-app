from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    convo,
    login,
    message,
    user,
    websocket,
    translation,
    aws,
    health,
)

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(user.router, prefix="/users", tags=["user"])
api_router.include_router(convo.router, prefix="/conversations", tags=["convo"])
api_router.include_router(message.router, prefix="/messages", tags=["message"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(
    translation.router, prefix="/translations", tags=["translation"]
)
api_router.include_router(aws.router, prefix="/aws", tags=["aws"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
