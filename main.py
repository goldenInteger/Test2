from mahjong_ai.table.table import Table
from mahjong_ai.buffer import ReplayBuffer
buffer = ReplayBuffer(capacity=50000)
table = Table()
table.run_game_loop(buffer)
rewards = [item['reward'] for item in buffer.buffer if 'reward' in item]
print("All rewards:", rewards)

def run_training_simulations(num_games: int):
    buffer = ReplayBuffer(capacity=50000)
    for i in range(num_games):
        print(f"\n=== 第 {i+1} 場對局 ===")
        table = Table()
        table.run_game_loop(buffer)
    buffer.save_to_json("output/train_batch.json")
    print("所有對局資料已儲存")
