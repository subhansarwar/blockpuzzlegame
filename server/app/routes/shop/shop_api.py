# app/routes/shop.py
from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.schemas.shop.shop import (
    InventoryResponse,
    PurchaseRequest,
    PurchaseResponse,
    ShopListResponse,
    WatchAdForPointsResponse,
)
from app.services.shop.shop_service import list_shop, purchase_item, get_inventory, watch_ad_for_points

router = APIRouter(prefix="/shop", tags=["Shop"])


@router.get("/all", response_model=ShopListResponse)
async def list_shop(db: SessionDep, user: CurrentUser):
    return await list_shop(db, user)


@router.post("/purchase", response_model=PurchaseResponse)
async def purchase(req: PurchaseRequest, db: SessionDep, user: CurrentUser):
    return await purchase_item(db, user, req)


@router.get("/inventory", response_model=InventoryResponse)
async def inventory(db: SessionDep, user: CurrentUser):
    return await get_inventory(db, user)


@router.post("/watch-ad", response_model=WatchAdForPointsResponse)
async def watch_ad(db: SessionDep, user: CurrentUser):
    return await watch_ad_for_points(db, user)
