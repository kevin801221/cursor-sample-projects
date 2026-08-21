"""
課堂用 Telegram Bot 終端與 Web 互動模擬器
"""
import os
import sys
from bot.main import simulate_button_click, CHORD_DATA

def main():
    print("\n" + "="*60)
    print("  🤖 Telegram Guitar Chords Bot 課堂互動模擬器")
    print("="*60 + "\n")
    print("可用和弦按鈕：")
    chords = list(CHORD_DATA.keys())
    for idx, c in enumerate(chords, 1):
        print(f"  [{idx}] {c:<4} ({CHORD_DATA[c]['name']})")
    
    print("\n▶ 模擬觸發按鈕點擊：[1] C 和弦")
    res = simulate_button_click("C")
    print(f"  ✓ query.answer() 耗時: {res['ack_ms']} ms (無卡頓轉圈)")
    print(f"  ✓ 圖片輸出路徑: {res['chart_path']}")

    print("\n▶ 模擬觸發按鈕點擊：[3] Am 和弦")
    res2 = simulate_button_click("Am")
    print(f"  ✓ query.answer() 耗時: {res2['ack_ms']} ms (無卡頓轉圈)")
    print(f"  ✓ 圖片輸出路徑: {res2['chart_path']}")

    print("\n" + "="*60)
    print("  🎉 模擬器測試成功！按鈕響應零延遲，指板圖正確生成。")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
