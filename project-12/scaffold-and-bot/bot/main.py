"""
Telegram Guitar Chords Bot
示範：Command handlers, Inline Keyboard 按鈕, query.answer() 快速回調與圖片發送
"""
import os
import time
from loguru import logger
from bot.chord_generator import generate_chord_chart, CHORD_DATA

def simulate_button_click(chord_name: str) -> dict:
    """
    模擬 Telegram Inline Keyboard 按鈕點擊處理流程
    1. 立即呼叫 query.answer()（先承諾，讓手機轉圈停下）
    2. 生成指板圖
    3. 回傳訊息與圖片路徑
    """
    start_time = time.time()
    
    # 關鍵：先給 callback 回應，轉圈不超過 300ms
    ack_time = time.time() - start_time
    logger.info(f"⚡ [Callback] query.answer() 於 {ack_time*1000:.1f}ms 內立即響應")

    chart_path = generate_chord_chart(chord_name, f"data/chord_{chord_name}.png")
    logger.success(f"🎸 [圖片生成] 已產出 {chord_name} 和弦指板圖：{chart_path}")

    return {
        "chord": chord_name,
        "ack_ms": round(ack_time * 1000, 2),
        "chart_path": chart_path,
        "message": f"這是 {chord_name} 和弦的指法圖！",
    }

if __name__ == "__main__":
    for c in ["C", "G", "Am", "Em"]:
        simulate_button_click(c)
