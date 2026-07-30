# app/models/shop/shop_item.py
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ShopItemType(str, enum.Enum):
    consumable = "consumable"
    skin = "skin"


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    item_type: Mapped[ShopItemType] = mapped_column(SAEnum(ShopItemType, name="shop_item_type"), nullable=False)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500))
    icon_url: Mapped[str | None] = mapped_column(String(500))
    price_points: Mapped[int] = mapped_column(Integer, nullable=False)
    is_stackable: Mapped[bool] = mapped_column(Boolean, default=True)  # consumables stack, skins are one-time
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    purchases = relationship("UserPurchase", back_populates="item", cascade="all, delete-orphan")
