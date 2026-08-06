# app/services/shop/shop_service.py
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.redis import redis_client, rkey
from app.models.shop.shop_item import ShopItem, ShopItemType
from app.models.shop.purchase import UserPurchase
from app.models.shop.ad_reward_log import AdRewardLog, AdRewardContext
from app.models.users.user import User
from app.schemas.shop.shop import (
    InventoryItem,
    InventoryResponse,
    PurchaseRequest,
    PurchaseResponse,
    ShopItemResponse,
    ShopListResponse,
    WatchAdForPointsResponse,
)
from app.services.game import stats_service
from app.services.users import audit_service

_DEFAULT_ITEMS = [
    dict(code="extra_life", item_type=ShopItemType.consumable, name="Extra Life",
         description="One extra life for your next run", price_points=150, is_stackable=True),
    dict(code="time_boost", item_type=ShopItemType.consumable, name="Time Boost",
         description="+15 seconds in Time Attack", price_points=120, is_stackable=True),
    dict(code="hint_reveal", item_type=ShopItemType.consumable, name="Hint Reveal",
         description="Reveals the best next move", price_points=80, is_stackable=True),
    dict(code="skin_neon", item_type=ShopItemType.skin, name="Neon Blocks",
         description="Neon-glow block skin", price_points=500, is_stackable=False),
    dict(code="skin_galaxy", item_type=ShopItemType.skin, name="Galaxy Theme",
         description="Galaxy-themed block skin", price_points=750, is_stackable=False),
    dict(code="skin_retro", item_type=ShopItemType.skin, name="Retro Skin",
         description="Retro arcade block skin", price_points=500, is_stackable=False),
]


def _today_key(user_id) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    return rkey("shop", "ad_count", str(user_id), today)


async def ensure_seeded(db: AsyncSession) -> None:
    result = await db.execute(select(ShopItem.id).limit(1))
    if result.scalar_one_or_none():
        return
    for data in _DEFAULT_ITEMS:
        db.add(ShopItem(**data))
    await db.commit()


async def _owned_quantities(db: AsyncSession, user_id) -> dict[int, int]:
    result = await db.execute(
        select(UserPurchase.item_id, func.sum(UserPurchase.quantity))
        .where(UserPurchase.user_id == user_id)
        .group_by(UserPurchase.item_id)
    )
    return {item_id: int(qty) for item_id, qty in result.all()}


async def list_shop(db: AsyncSession, user: User) -> ShopListResponse:
    stats = await stats_service.get_or_create_stats(db, user.id)
    result = await db.execute(select(ShopItem).where(ShopItem.is_active == True).order_by(ShopItem.price_points))  # noqa: E712
    items = result.scalars().all()
    owned = await _owned_quantities(db, user.id)

    return ShopListResponse(
        points_balance=stats.points_balance,
        items=[
            ShopItemResponse(
                id=i.id, code=i.code, item_type=i.item_type, name=i.name, description=i.description,
                icon_url=i.icon_url, price_points=i.price_points, is_stackable=i.is_stackable,
                owned_quantity=owned.get(i.id, 0),
            )
            for i in items
        ],
    )


async def purchase_item(db: AsyncSession, user: User, req: PurchaseRequest) -> PurchaseResponse:
    result = await db.execute(select(ShopItem).where(ShopItem.id == req.item_id, ShopItem.is_active == True))  # noqa: E712
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Item not found")

    quantity = req.quantity
    if not item.is_stackable:
        owned = await _owned_quantities(db, user.id)
        if owned.get(item.id, 0) > 0:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="You already own this item")
        quantity = 1

    total_price = item.price_points * quantity
    stats = await stats_service.spend_points(db, user.id, total_price)

    db.add(UserPurchase(user_id=user.id, item_id=item.id, quantity=quantity, price_paid_points=total_price))
    await audit_service.log_event(db, user_id=user.id, event="shop_purchase", status="success", detail=item.code)
    await db.commit()

    owned = await _owned_quantities(db, user.id)
    return PurchaseResponse(
        item_id=item.id, quantity=quantity, points_spent=total_price,
        points_balance=stats.points_balance, owned_quantity=owned.get(item.id, 0),
    )


async def get_inventory(db: AsyncSession, user: User) -> InventoryResponse:
    result = await db.execute(
        select(ShopItem.id, ShopItem.code, ShopItem.name, ShopItem.item_type, func.sum(UserPurchase.quantity))
        .join(UserPurchase, UserPurchase.item_id == ShopItem.id)
        .where(UserPurchase.user_id == user.id)
        .group_by(ShopItem.id, ShopItem.code, ShopItem.name, ShopItem.item_type)
    )
    items = [
        InventoryItem(item_id=row[0], code=row[1], name=row[2], item_type=row[3], quantity=int(row[4]))
        for row in result.all()
    ]
    return InventoryResponse(items=items)


async def watch_ad_for_points(db: AsyncSession, user: User) -> WatchAdForPointsResponse:
    key = _today_key(user.id)
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 60 * 60 * 26)  # a bit over a day, safe against clock drift

    if count > settings.SHOP_AD_DAILY_LIMIT:
        await redis_client.decr(key)
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail="Daily ad-reward limit reached")

    stats = await stats_service.add_points(db, user.id, settings.SHOP_AD_REWARD_POINTS)
    db.add(AdRewardLog(user_id=user.id, context=AdRewardContext.shop_points, reward_points=settings.SHOP_AD_REWARD_POINTS))
    await audit_service.log_event(db, user_id=user.id, event="ad_reward", status="success", detail="shop_points")
    await db.commit()

    return WatchAdForPointsResponse(
        points_earned=settings.SHOP_AD_REWARD_POINTS,
        points_balance=stats.points_balance,
        ads_watched_today=count,
        ads_remaining_today=max(settings.SHOP_AD_DAILY_LIMIT - count, 0),
    )
