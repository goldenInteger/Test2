# run_all.py - 一鍵模擬、訓練與測試流程，支援 CLI 路徑與訓練參數

import subprocess
import datetime
import os

# 建立唯一輸出檔名（加時間戳）
now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
json_path = f"data/selfplay_round_{now}.json"

# [1] 執行模擬對局，產生訓練資料
print("[1] 開始模擬對局...")
subprocess.run(["python", "simulate_selfplay.py", "--output", json_path])

# [2] 執行模型訓練
print("\n[2] 開始模型訓練...")
subprocess.run([
    "python", "train.py",
    "--json_path", json_path,
    "--batch_size", "256",
    "--epochs", "10",
    "--lr", "0.0001",
    "--conv_channels", "128",
    "--num_blocks", "8",
    "--version", "2"
])

# [3] 顯示測試結果
print("\n[3] 測試結果如下：")
with open("models/test_result.json", "r", encoding="utf-8") as f:
    print(f.read())
