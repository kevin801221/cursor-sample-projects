import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class URLCreate(BaseModel):
    target_url: str = Field(..., description="要縮短的原始長網址")
    custom_code: Optional[str] = Field(None, description="自訂短代碼 (3-16 字元)")

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("網址必須以 http:// 或 https:// 開頭")
        if len(v) < 8 or "." not in v:
            raise ValueError("請輸入有效的完整網址格式 (例如: https://example.com)")
        return v

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]{3,16}$", v):
            raise ValueError("自訂代碼只能包含 3-16 位的英文字母、數字、底線或破折號")
        return v

class URLResponse(BaseModel):
    short_code: str
    short_url: str
    target_url: str
    clicks: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClickEvent(BaseModel):
    timestamp: datetime
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    referer: Optional[str] = None

class URLStatsResponse(BaseModel):
    short_code: str
    target_url: str
    total_clicks: int
    created_at: datetime
    recent_clicks: list[ClickEvent]
