# app/services/users/profile_service.py
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.core.storage import upload_avatar as storage_upload_avatar, delete_avatar as storage_delete_avatar
from app.models.users.user import User
from app.models.users.auth_provider import AuthProvider
from app.models.users.preferences import UserPreference
from app.models.game.stats import UserGameStats
from app.models.game.time_attack import TimeAttackBest
from app.models.game.classic import ClassicBest
from app.models.game.levels import UserLevelState, LevelProgress
from app.models.game.daily_challenge import DailyChallengeClaim
from app.models.game.game_session import GameSession
from app.models.social.achievement import UserAchievement
from app.models.social.leaderboard import WeeklyScore
from app.schemas.users.profile import ProfileResponse, AvatarResponse
from app.schemas.users.preferences import PreferenceResponse, PreferenceUpdate
from app.services.users import audit_service


async def get_profile(db: AsyncSession, user: User) -> ProfileResponse:
    result = await db.execute(select(AuthProvider.provider).where(AuthProvider.user_id == user.id))
    providers = [row[0] for row in result.all()]
    return ProfileResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        linked_providers=providers,
        created_at=user.created_at,
    )


async def update_name(db: AsyncSession, user: User, new_name: str) -> ProfileResponse:
    if new_name != user.name:
        result = await db.execute(select(User.id).where(User.name == new_name))
        if result.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")
        user.name = new_name
        await audit_service.log_event(db, user_id=user.id, event="profile_update", status="success", detail="name")
        await db.commit()
        await db.refresh(user)
    return await get_profile(db, user)

async def update_avatar(db: AsyncSession, user: User, content: bytes, content_type: str) -> AvatarResponse:
    if content_type not in settings.AVATAR_ALLOWED_CONTENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")
    if len(content) > settings.AVATAR_MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Image must be under {settings.AVATAR_MAX_SIZE_MB}MB")

    old_avatar_url = user.avatar_url
    new_url = await storage_upload_avatar(str(user.id), content, content_type)
    user.avatar_url = new_url
    await audit_service.log_event(db, user_id=user.id, event="avatar_update", status="success")
    await db.commit()

    if old_avatar_url:
        await storage_delete_avatar(old_avatar_url)

    return AvatarResponse(avatar_url=new_url)


async def delete_avatar(db: AsyncSession, user: User) -> AvatarResponse:
    if user.avatar_url:
        await storage_delete_avatar(user.avatar_url)
        user.avatar_url = None
        await audit_service.log_event(db, user_id=user.id, event="avatar_update", status="success", detail="removed")
        await db.commit()
    return AvatarResponse(avatar_url=None)


async def get_preferences(db: AsyncSession, user: User) -> PreferenceResponse:
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user.id))
    pref = result.scalar_one_or_none()
    if not pref:
        pref = UserPreference(user_id=user.id)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return PreferenceResponse.model_validate(pref)


async def update_preferences(db: AsyncSession, user: User, update: PreferenceUpdate) -> PreferenceResponse:
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user.id))
    pref = result.scalar_one_or_none()
    if not pref:
        pref = UserPreference(user_id=user.id)
        db.add(pref)
        await db.flush()

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(pref, field, value)

    await db.commit()
    await db.refresh(pref)
    return PreferenceResponse.model_validate(pref)


_RESET_TABLES = (GameSession, LevelProgress, DailyChallengeClaim, ClassicBest, UserAchievement, WeeklyScore)


async def reset_progress(db: AsyncSession, user: User) -> None:
    """Wipes all gameplay data but keeps the account/auth/preferences intact."""
    for model in _RESET_TABLES:
        await db.execute(delete(model).where(model.user_id == user.id))

    result = await db.execute(select(UserGameStats).where(UserGameStats.user_id == user.id))
    stats = result.scalar_one_or_none()
    if stats:
        stats.all_time_high_score = 0
        stats.max_combo = 0
        stats.total_lines_cleared = 0
        stats.points_balance = 0
        stats.total_points = 0
        stats.coins_balance = 0
        stats.total_coins_earned = 0

    result = await db.execute(select(TimeAttackBest).where(TimeAttackBest.user_id == user.id))
    ta = result.scalar_one_or_none()
    if ta:
        ta.best_score = 0
        ta.last_score = 0

    result = await db.execute(select(UserLevelState).where(UserLevelState.user_id == user.id))
    ls = result.scalar_one_or_none()
    if ls:
        ls.current_level = 1
        ls.best_score = 0
        ls.last_score = 0
        ls.total_points_earned = 0

    await audit_service.log_event(db, user_id=user.id, event="reset_progress", status="success")
    await db.commit()


async def delete_account(db: AsyncSession, user: User, password: str | None) -> None:
    if user.hashed_password:
        if not password or not verify_password(password, user.hashed_password):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    if user.avatar_url:
        await storage_delete_avatar(user.avatar_url)

    await audit_service.log_event(db, user_id=user.id, event="delete_account", status="success")
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()
