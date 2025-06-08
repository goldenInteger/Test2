# run_all.py - 一鍵模擬、訓練與測試流程，支援 CLI 路徑與訓練參數

import subprocess
import datetime
import os
import sys


# === 確保輸出資料夾存在 ===
os.makedirs("mahjong_ai/data", exist_ok=True)
os.makedirs("mahjong_ai/models", exist_ok=True)

# === 訓練輪數設定 ===
NUM_ROUNDS = 1
   # ← 想跑幾輪你可以改這裡

for i in range(1, NUM_ROUNDS + 1):
    print(f"\n========== 第 {i} 輪訓練開始 ==========")

    # 建立唯一輸出檔名（加時間戳）
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"mahjong_ai/data/selfplay_round_{now}.json"

    # [1] 執行模擬對局，產生訓練資料
    print("[1] 開始模擬對局...")
    subprocess.run([sys.executable, "-m", "mahjong_ai.simulate_selfplay", "--output", json_path])

    # [2] 執行模型訓練
    print("\n[2] 開始模型訓練...")
    subprocess.run([
        sys.executable, "-m", "mahjong_ai.train",
        "--json_path", json_path,
        "--batch_size", "256",
        "--epochs", "50",
        "--lr", "0.0001",
        "--conv_channels", "128",
        "--num_blocks", "8",
        "--version", "2"
    ])

    try:
        with open("mahjong_ai/models/best_reward.txt", "r") as f:
            best = f.read().strip()
        print(f"🏆 當前最佳 reward：{best}")
    except:
        print("⚠️ 尚未產生 best_reward.txt")

print("\n✅ 全部訓練輪數完成")


# [3] 顯示測試結果
"""print("\n[3] 測試結果如下：")
subprocess.run([sys.executable, "-m", "mahjong_ai.test_play"])
with open("mahjong_ai/models/test_result.json", "r", encoding="utf-8") as f:
    print(f.read())"""
