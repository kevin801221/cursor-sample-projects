from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator

def utc_now():
    return datetime.now(timezone.utc)

class ProductPrice(BaseModel):
    product_id: str = Field(..., description="商品唯一識別碼")
    title: str = Field(..., description="商品名稱")
    price: float = Field(..., ge=0, description="目前商品價格")
    currency: str = Field("TWD", description="貨幣代碼")
    in_stock: bool = Field(True, description="是否有庫存")
    url: str = Field(..., description="商品連結")
    scraped_at: datetime = Field(default_factory=utc_now)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        return v.strip()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("商品價格不能為負數")
        return round(v, 2)

class PriceDropAlert(BaseModel):
    product_id: str
    title: str
    old_price: float
    new_price: float
    drop_percentage: float
    url: str
    detected_at: datetime = Field(default_factory=utc_now)
