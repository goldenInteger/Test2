# test_play.py - 測試模型表現，回傳 avg_reward / win_rate / avg_rank

import json
from mahjong_ai.table.table import Table
from mahjong_ai.buffer import ReplayBuffer

NUM_TEST_GAMES = 5
OUTPUT_PATH = "mahjong_ai/models/test_result.json"


def evaluate_model(num_games=NUM_TEST_GAMES):
    total_reward = 0
    total_win = 0
    total_rank_sum = 0

    for i in range(num_games):
        table = Table()
        buffer = ReplayBuffer(capacity=1)  # 不紀錄資料，只跑模型
        table.run_game_loop(buffer)

        ai_player = next(p for p in table.players if p.is_ai)
        total_reward += ai_player.points

        ranks = sorted(table.players, key=lambda p: p.points, reverse=True)
        rank_index = ranks.index(ai_player)
        total_rank_sum += (rank_index + 1)

        if rank_index == 0:
            total_win += 1

    avg_reward = total_reward / num_games
    win_rate = total_win / num_games
    avg_rank = total_rank_sum / num_games

    result = {
        "avg_reward": round(avg_reward, 2),
        "win_rate": round(win_rate, 3),
        "avg_rank": round(avg_rank, 2)
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f" 測試完成：{num_games} 局結果寫入 {OUTPUT_PATH}")
    print(result)


if __name__ == "__main__":
    evaluate_model()
