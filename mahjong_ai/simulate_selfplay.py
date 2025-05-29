# simulate_selfplay.py - 產生訓練資料的模擬對局器，支援 CLI 輸出路徑參數

import os
import argparse
import datetime
from mahjong_ai.buffer import ReplayBuffer
from mahjong_ai.table.table import Table

NUM_GAMES = 20  # 對局數

# 主模擬函數：跑多場對局並儲存訓練資料至指定路徑
def simulate_selfplay(output_path):
    buffer = ReplayBuffer(capacity=100000)
    for i in range(NUM_GAMES):
        print(f"=== 第 {i + 1} 場對局 ===")
        table = Table()
        table.run_game_loop(buffer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    buffer.save_to_json(output_path)
    print(f"✓ 所有對局已完成，資料儲存於 {output_path}")

# 命令列入口，支援 --output 參數
def parse_args():
    parser = argparse.ArgumentParser()
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    parser.add_argument("--output", type=str, default=f"mahjong_ai/data/selfplay_round_{now}.json",help="輸出訓練資料的檔案路徑")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    simulate_selfplay(args.output)
