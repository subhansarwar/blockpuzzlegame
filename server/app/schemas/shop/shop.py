# app/schemas/shop/shop.py
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.shop.shop_item import ShopItemType


class ShopItemResponse(BaseModel):
    id: int
    code: str
    item_type: ShopItemType
    name: str
    description: str | None
    icon_url: str | None
    price_points: int
    is_stackable: bool
    owned_quantity: int


class ShopListResponse(BaseModel):
    points_balance: int
    items: list[ShopItemResponse]


class PurchaseRequest(BaseModel):
    item_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class PurchaseResponse(BaseModel):
    item_id: int
    quantity: int
    points_spent: int
    points_balance: int
    owned_quantity: int


class WatchAdForPointsResponse(BaseModel):
    points_earned: int
    points_balance: int
    ads_watched_today: int
    ads_remaining_today: int


class InventoryItem(BaseModel):
    item_id: int
    code: str
    name: str
    item_type: ShopItemType
    quantity: int


class InventoryResponse(BaseModel):
    items: list[InventoryItem]
