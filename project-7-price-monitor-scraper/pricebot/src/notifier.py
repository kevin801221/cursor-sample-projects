from loguru import logger
from src.models import PriceDropAlert

class TelegramNotifier:
    def __init__(self, bot_token: str = "mock_token", chat_id: str = "mock_chat_id"):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_price_drop_alert(self, alert: PriceDropAlert) -> bool:
        msg = (
            f"🚨 <b>【PriceBot 降價通知】</b>\n"
            f"📦 商品：{alert.title}\n"
            f"💰 原價：NT$ {alert.old_price:,.0f} → <b>特價：NT$ {alert.new_price:,.0f}</b>\n"
            f"📉 降幅：<b>-{alert.drop_percentage}%</b>\n"
            f"🔗 連結：{alert.url}"
        )
        logger.success(f"📱 [Telegram 通知已派發] -> {alert.title} 降價 {alert.drop_percentage}% (NT$ {alert.new_price})")
        print("\n" + "="*50)
        print("  📱 模擬 Telegram 推播通知")
        print(f"  {msg.replace('<b>','').replace('</b>','')}")
        print("="*50 + "\n")
        return True
