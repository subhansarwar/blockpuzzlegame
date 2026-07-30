# app/routes/__init__.py
from fastapi import APIRouter
from app.routes.users.profile_api import router as profile_router
from app.routes.users.auth_api import router as auth_router
from app.routes.users.device_tokens_api import router as device_tokens_router
from app.routes.shop.shop_api import router as shop_router
from app.routes.game.game_time_attack import router as attack_router
from app.routes.game.game_classic import router as classic_router
from app.routes.game.game_daily_challenge import router as daily_router
from app.routes.game.game_levels import router as levels_router
from app.routes.social.achievements import router as achievements_router
from app.routes.social.arena import router as arena_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/api")
api_router.include_router(profile_router, prefix="/api")
api_router.include_router(device_tokens_router, prefix="/api")
api_router.include_router(attack_router, prefix="/api")
api_router.include_router(classic_router, prefix="/api")
api_router.include_router(levels_router, prefix="/api")
api_router.include_router(daily_router, prefix="/api")
api_router.include_router(achievements_router, prefix="/api")
api_router.include_router(arena_router, prefix="/api")
api_router.include_router(shop_router, prefix="/api")
