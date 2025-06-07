# train.py - 擴充參數控制版本，支援完整可調設定與詳細註解

import json
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from mahjong_ai.model.model import Brain, DQN
import os
import argparse
import subprocess
import sys


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 訓練過程中 loss/reward 儲存路徑
LOSS_LOG_PATH = "mahjong_ai/models/loss_log.json"
REWARD_LOG_PATH = "mahjong_ai/models/reward_log.json"

# 資料集定義：將 JSON 中每筆 obs/mask/action/reward 轉為 tensor
class MahjongDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data[idx]
        obs = torch.tensor(sample["obs"]).float()         # [C, 34]
        mask = torch.tensor(sample["mask"]).bool()        # [A]
        action = torch.tensor(sample["action"]).long()    # scalar
        reward = torch.tensor(sample["reward"]).float()   # scalar
        return obs, mask, action, reward

# 載入 JSON 資料並轉為 Dataset
def load_dataset(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return MahjongDataset(data)

# 呼叫 test_play.py，取得 avg_reward 結果與細節
def evaluate_model():
    print("\n[OK] 執行模型評估：test_play.py")
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable, "-m", "mahjong_ai.test_play"], text=True, env=env, cwd=cwd, errors="ignore")

    print("[Debug] returncode:", result.returncode)
    if result.returncode != 0:
        print("[!] test_play 失敗：", result.stderr)
        return None

    try:
        with open("mahjong_ai/models/test_result.json", "r", encoding="utf-8") as f:
            result_data = json.load(f)
        print("[Debug] result_data =", result_data)

        if not isinstance(result_data, dict):
            print("[!] 讀到的 JSON 不是 dict，而是：", type(result_data))
            return None

        if "avg_point" not in result_data:
            print("[!] 缺少 avg_point 欄位")
            return None

        avg_point = result_data["avg_point"]
        avg_reward = result_data["avg_reward"]
        if not isinstance(avg_point, (int, float)):
            print("[!] avg_reward 欄位格式錯誤：", avg_point)
            return None

        return avg_reward, avg_point, result_data

    except Exception as e:
        print("[!] 無法讀取測試結果檔案：", e)
        return None

# 嘗試讀取目前最好的 reward
def load_best_reward():
    try:
        with open("mahjong_ai/models/best_reward.txt", "r") as f:
            return float(f.read().strip())
    except:
        return -9999

# 如果 reward 比歷史最佳還好，就更新 best 模型與分數
def save_best_model(brain, dqn, reward):
    torch.save(brain.state_dict(), "mahjong_ai/models/best_brain.pth")
    torch.save(dqn.state_dict(), "mahjong_ai/models/best_dqn.pth")
    with open("mahjong_ai/models/best_reward.txt", "w") as f:
        f.write(str(reward))
    print(f" 發現更好的模型，已儲存 best_brain.pth 與 best_dqn.pth (reward={reward:.4f})")

# 附加訓練紀錄（loss/reward）進 JSON 紀錄檔
def append_json_log(path, record):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(record)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def compute_total_reward(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    total_reward = sum(sample["reward"] for sample in data)
    return total_reward

def compute_avg_reward(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    total = sum(sample["reward"] for sample in data)
    count = len(data)
    return total / count if count > 0 else -9999

# ====== 主訓練函數，包含模型初始化、訓練迴圈、測試與儲存 ======
def train(config):
    print(f"載入訓練資料: {config.json_path}")
    dataset = load_dataset(config.json_path)
    loader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True)

    # 初始化模型（Brain 決定 obs 特徵、DQN 決定 Q 值）
    brain = Brain(version=config.version, conv_channels=config.conv_channels, num_blocks=config.num_blocks).to(DEVICE)
    dqn = DQN(version=config.version).to(DEVICE)
    # 接續最佳模型訓練
    best_brain_path = "mahjong_ai/models/best_brain.pth"
    best_dqn_path = "mahjong_ai/models/best_dqn.pth"
    if os.path.exists(best_brain_path) and os.path.exists(best_dqn_path):
        print("載入最佳模型進行續訓...")
        brain.load_state_dict(torch.load(best_brain_path, map_location=DEVICE, weights_only=True))
        dqn.load_state_dict(torch.load(best_dqn_path, map_location=DEVICE, weights_only=True))
    else:
        print("找不到最佳模型，從頭開始訓練")

    # 建立 optimizer
    optimizer = torch.optim.Adam(list(brain.parameters()) + list(dqn.parameters()), lr=config.lr, weight_decay=config.weight_decay)

    for epoch in range(config.epochs):
        total_loss = 0.0
        for obs, mask, action, reward in loader:
            obs = obs.to(DEVICE)
            mask = mask.to(DEVICE)
            action = action.to(DEVICE)
            reward = reward.to(DEVICE)

            phi = brain(obs)
            q_values = dqn(phi, mask)
            q_selected = q_values.gather(1, action.unsqueeze(1)).squeeze(1)
            loss = F.mse_loss(q_selected, reward)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"[Epoch {epoch+1}] Loss: {avg_loss:.4f}")
        append_json_log(LOSS_LOG_PATH, {"epoch": epoch + 1, "loss": avg_loss})

    # 儲存最新模型
    os.makedirs("mahjong_ai/models", exist_ok=True)
    torch.save(brain.state_dict(), "mahjong_ai/models/latest_brain.pth")
    torch.save(dqn.state_dict(), "mahjong_ai/models/latest_dqn.pth")
    torch.save(brain.state_dict(), "mahjong_ai/models/latest.pth")

    # 評估新模型表現
    eval_reward, eval_point, full_result = evaluate_model()
    if eval_reward is not None:
        append_json_log(REWARD_LOG_PATH, {"epoch": config.epochs, **full_result})
        best_reward = compute_avg_reward(config.json_path)
        print(f" 模擬best_avg_reward：{best_reward:.2f}")
        if eval_reward > best_reward:
            save_best_model(brain, dqn, eval_reward)
        else:
            print(f" 模型未進步，維持最佳 reward={best_reward:.4f}")

    # === 加總這次所有 reward 並存檔 ===
    total_reward = compute_total_reward(config.json_path)
    print(f" 本次模擬 reward 總和：{total_reward:.2f}")

    append_json_log("mahjong_ai/models/reward_sum_log.json", {
        "epoch": config.epochs,
        "total_reward": total_reward
    })

# ====== 命令列引數解析：支援多參數調整 ======
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type=str, required=True, help='訓練資料 JSON 檔路徑')
    parser.add_argument('--batch_size', type=int, default=256, help='訓練批次大小')
    parser.add_argument('--epochs', type=int, default=10, help='訓練週期數')
    parser.add_argument('--lr', type=float, default=1e-4, help='學習率')
    parser.add_argument('--weight_decay', type=float, default=0.0, help='L2 正則化係數')
    parser.add_argument('--version', type=int, default=2, help='模型版本（與 obs encoder 對應）')
    parser.add_argument('--conv_channels', type=int, default=128, help='CNN 特徵圖通道數')
    parser.add_argument('--num_blocks', type=int, default=8, help='殘差區塊數')

    args = parser.parse_args()
    train(args)
