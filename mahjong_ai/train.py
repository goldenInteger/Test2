# train.py - 擴充參數控制版本，支援完整可調設定與詳細註解

import json
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from mahjong_ai.model.model import Brain, DQN
import os
import argparse
import subprocess

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 訓練過程中 loss/reward 儲存路徑
LOSS_LOG_PATH = "models/loss_log.json"
REWARD_LOG_PATH = "models/reward_log.json"

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
    print("\n[✓] 執行模型評估：test_play.py")
    result = subprocess.run(["python", "test_play.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print("[!] test_play 失敗：", result.stderr)
        return None
    with open("models/test_result.json", "r", encoding="utf-8") as f:
        result_data = json.load(f)
    return result_data.get("avg_reward", -9999), result_data

# 嘗試讀取目前最好的 reward
def load_best_reward():
    try:
        with open("models/best_reward.txt", "r") as f:
            return float(f.read().strip())
    except:
        return -9999

# 如果 reward 比歷史最佳還好，就更新 best 模型與分數
def save_best_model(brain, dqn, reward):
    torch.save(brain.state_dict(), "models/best_brain.pth")
    torch.save(dqn.state_dict(), "models/best_dqn.pth")
    with open("models/best_reward.txt", "w") as f:
        f.write(str(reward))
    print(f"[✓] 發現更好的模型，已儲存 best_brain.pth 與 best_dqn.pth (reward={reward:.4f})")

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

# ====== 主訓練函數，包含模型初始化、訓練迴圈、測試與儲存 ======
def train(config):
    print(f"載入訓練資料: {config.json_path}")
    dataset = load_dataset(config.json_path)
    loader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True)

    # 初始化模型（Brain 決定 obs 特徵、DQN 決定 Q 值）
    brain = Brain(version=config.version, conv_channels=config.conv_channels, num_blocks=config.num_blocks).to(DEVICE)
    dqn = DQN(version=config.version).to(DEVICE)

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
    os.makedirs("models", exist_ok=True)
    torch.save(brain.state_dict(), "models/latest_brain.pth")
    torch.save(dqn.state_dict(), "models/latest_dqn.pth")
    torch.save(brain.state_dict(), "models/latest.pth")

    # 評估新模型表現
    eval_reward, full_result = evaluate_model()
    if eval_reward is not None:
        append_json_log(REWARD_LOG_PATH, {"epoch": config.epochs, **full_result})
        best_reward = load_best_reward()
        if eval_reward > best_reward:
            save_best_model(brain, dqn, eval_reward)
        else:
            print(f"[✓] 模型未進步，維持最佳 reward={best_reward:.4f}")

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
