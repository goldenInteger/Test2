from __future__ import annotations
from typing import TYPE_CHECKING
# ai/ai_decide.py
import torch
from mahjong_ai.table.tile import Tile
from mahjong_ai.model.model import Brain, DQN, AuxNet
from mahjong_ai.table.encode_obs import encode_obs_v2
import os
# from ai.reward import evaluate_action_reward

if TYPE_CHECKING:
    from mahjong_ai.table.table import Table  # 僅供型別檢查工具使用，不會在執行時引入
    from mahjong_ai.table.player import Player

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

brain = Brain(version=2, conv_channels=128, num_blocks=8).to(DEVICE).eval()
dqn = DQN(version=2).to(DEVICE).eval()
aux = AuxNet((4,)).to(DEVICE).eval()  # 若你推理階段不需要，可不用算
model_path = "mahjong_ai/models"
if os.path.exists(f"{model_path}/best_brain.pth"):
    brain.load_state_dict(torch.load(f"{model_path}/best_brain.pth", map_location=DEVICE, weights_only=True))
    dqn.load_state_dict(torch.load(f"{model_path}/best_dqn.pth", map_location=DEVICE, weights_only=True))
    print("[!] 使用 best 模型")
elif os.path.exists(f"{model_path}/latest_brain.pth"):
    brain.load_state_dict(torch.load(f"{model_path}/latest_brain.pth", map_location=DEVICE, weights_only=True))
    dqn.load_state_dict(torch.load(f"{model_path}/latest_dqn.pth", map_location=DEVICE, weights_only=True))
    print(" 使用 latest 模型")
else:
    print("[!] 沒有找到任何模型，請先執行訓練 train.py")

def ai_decide_action(table, tile , buffer, action_types: set[str]) -> int:
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

    reward =  evaluate_action_reward(table, action, tile)

    if buffer is not None:
        buffer.push({
            "obs": obs.tolist(),       # [942, 34] → list of list
            "mask": mask.tolist(),     # [46] → list
            "action": int(action),     # 確保不是 np.int64
            "reward": float(reward),   # 確保不是 np.float32
        })

    return action


from mahjong_ai.utils.helper_interface import (
    call_mahjong_helper, choose_first_3_discards_from_output,
    mingpai_mahjong_helper, chi_mingpai_top_two_lines, pon_mingpai_top_two_lines
)

def evaluate_action_reward(table: Table, action: int, tile: Tile | None) -> float:
    from mahjong_ai.table.Mingpai import can_chi_sets, can_pon, can_daiminkan
    player = table.players[table.current_turn]
    print(f"\n{action}")
    # 打牌 (0~33)
    if 0 <= action <= 33:
        discard_tile = Tile.from_34_id(action)
        output = call_mahjong_helper(player.hand.tiles, player.melds)
        top_discards = choose_first_3_discards_from_output(output)
        if discard_tile.to_helper_string() in top_discards:
            return 1.0
        else:
            return -0.2

    # 立直
    elif action == 34:
        if player.is_riichi:
            return 1.5
        return -0.5

    # 吃牌 (35–37)
    elif 35 <= action <= 37:
        if not tile:
            return -1.0
        if (player.hasyaku or player.do_has_yaku()) :
            output = mingpai_mahjong_helper(player.hand.tiles, player.melds, tile)
            result = chi_mingpai_top_two_lines(output, tile)
            return 1.0 if result else -1.0
        
        return -2.0

    # 碰牌
    elif action == 38:
        if not tile:
            return -1.0

        
        if sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) < 2:
                return -1.0

        # 如果是字牌才檢查風牌限制
        if tile.tile_type == 'honor':
            # 東=1, 南=2, 西=3, 北=4, 白=5, 發=6, 中=7
            valid_values = []

            # 自風 & 場風（東=0, 南=1, 西=2, 北=3）
            wind_map = {0: 1, 1: 2, 2: 3, 3: 4}
            valid_values.append(wind_map.get(player.seat_wind))
            valid_values.append(wind_map.get(player.round_wind))

            # 中白發永遠可碰（5,6,7）
            valid_values += [5, 6, 7]

            if tile.tile_value not in valid_values:
                return -1.0
        
            player.hasyaku = True

        if ((player.hasyaku or player.do_has_yaku())) :
            output = mingpai_mahjong_helper(player.hand.tiles, player.melds, tile)
            result = pon_mingpai_top_two_lines(output)
            return 1.0 if result else -1.0
        
        return -2.0
        

    # 槓牌
    elif action == 40:
        if not tile:
            return -1.0
        if ((player.hasyaku or player.do_has_yaku())) :
            return 0.5
        return -0.3

    
    elif action == 39 or action == 41:
        return 0.5

    # 和牌
    elif action == 42:
        if table.round_result and table.round_result.winner == player.player_id:
            return 10.0
        return -1.0

    # 流局
    elif action == 43:
        return 0.0
    # PASS
    elif action == 44:
        if tile:
            # --- 檢查是否能吃（僅限下家）
            chi_allowed = (table.last_discard_player_id + 1) % 4 == table.current_turn
            if chi_allowed and can_chi_sets(player, tile):
                if (player.hasyaku or player.do_has_yaku()) :
                    output = mingpai_mahjong_helper(player.hand.tiles, player.melds, tile)
                    result = chi_mingpai_top_two_lines(output, tile)
                    return -0.3 if result else 1.0
                return 1.0

            # --- 檢查是否能碰
            if can_pon(player, tile):
                if sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) < 2:
                    return -1.0

                # 如果是字牌才檢查風牌限制
                if tile.tile_type == 'honor':
                    # 東=1, 南=2, 西=3, 北=4, 白=5, 發=6, 中=7
                    valid_values = []

                    # 自風 & 場風（東=0, 南=1, 西=2, 北=3）
                    wind_map = {0: 1, 1: 2, 2: 3, 3: 4}
                    valid_values.append(wind_map.get(player.seat_wind))
                    valid_values.append(wind_map.get(player.round_wind))

                    # 中白發永遠可碰（5,6,7）
                    valid_values += [5, 6, 7]

                    if tile.tile_value not in valid_values:
                        return -1.0
                
                    player.hasyaku = True

                if ((player.hasyaku or player.do_has_yaku())) :
                    output = mingpai_mahjong_helper(player.hand.tiles, player.melds, tile)
                    result = pon_mingpai_top_two_lines(output)
                    return -0.3 if result else 1.0
                
                return 0.5
                
            # if can_daiminkan(player, tile):
            #     if ((player.hasyaku or player.do_has_yaku())) :
 
                
            return 1.0  # 不能吃／不能碰 → PASS 是合理的
        else:
            return 0.1  # 沒有 tile 無法判斷，保守給中性分


    return 0.0




    

