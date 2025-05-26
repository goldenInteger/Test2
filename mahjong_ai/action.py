# ai/ai_decide.py
import torch
from mahjong_ai.model.model import Brain, DQN, AuxNet
from mahjong_ai.table.encode_obs import encode_obs_v2
# from ai.reward import evaluate_action_reward

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

brain = Brain(version=2, conv_channels=128, num_blocks=8).to(DEVICE).eval()
dqn = DQN(version=2).to(DEVICE).eval()
aux = AuxNet((4,)).to(DEVICE).eval()  # 若你推理階段不需要，可不用算

def ai_decide_action(table, buffer, action_types: set[str]) -> int:
    # 1. 編碼 obs/mask
    obs, mask = encode_obs_v2(table, action_types)
    obs_tensor = torch.tensor(obs).unsqueeze(0).float().to(DEVICE)   # [1, C, 34]
    mask_tensor = torch.tensor(mask).unsqueeze(0).bool().to(DEVICE)  # [1, A]

    with torch.no_grad():
        phi = brain(obs_tensor)  # [1, 1024]
        q = dqn(phi, mask_tensor)  # [1, A]
        action = torch.argmax(q, dim=-1).item()

        # 可選：預測 rank，只記錄不使用
        # pred_rank = torch.argmax(aux(phi), dim=-1).item()

    reward =  44 #evaluate_action_reward(table, action)

    buffer.push({
        "obs": obs.tolist(),       # [942, 34] → list of list
        "mask": mask.tolist(),     # [46] → list
        "action": int(action),     # 確保不是 np.int64
        "reward": float(reward),   # 確保不是 np.float32
    })


    return action
