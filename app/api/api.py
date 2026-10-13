from fastapi import APIRouter
from app.api.endpoints import (
    auth,
    communication_style,
    dealership_profile,
    generation_logs,
    logs,
    posts,
    prompt,
    role,
    sync,
    users,
    vehicles,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(role.router, prefix="/roles", tags=["roles"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(prompt.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(communication_style.router, prefix="/communication-styles", tags=["communication styles"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(generation_logs.router, prefix="/generation-logs", tags=["generation logs"])
api_router.include_router(dealership_profile.router, prefix="/dealership-profile", tags=["dealership profile"])
