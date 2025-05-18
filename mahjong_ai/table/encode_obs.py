from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from typing import Tuple
if TYPE_CHECKING:
    from mahjong_ai.table.table import Table
from mahjong.shanten import Shanten
from mahjong.agari import Agari

# tile_to_34 會需要你提供的 Tile 類型實作
# 這邊假設你有 tile.to_34_id() 或 tile.suit / tile.value 等資訊

def get_shanten_and_waits(tiles_34: list[int]) -> Tuple[int, list[int]]:
    shanten_calc = Shanten()
    agari = Agari()

    shanten = shanten_calc.calculate_shanten(tiles_34)
    waits = []
    for tid in range(34):
        tiles_34[tid] += 1
        if agari.is_agari(tiles_34):
            waits.append(tid)
        tiles_34[tid] -= 1
    return shanten, waits

def encode_obs_v2(table: Table, seat: int, legal_actions: dict) -> Tuple[np.ndarray, np.ndarray]:
    obs = np.zeros((942, 34), dtype=np.float32)
    mask = np.zeros((46,), dtype=bool)

    # === 範例 ===
    # 1. 手牌
    hand_34 = [0] * 34
    for tile in table.players[seat].hand.tiles:
        tid = tile.to_34_id()
        obs[0][tid] += 1.0
        hand_34[tid] += 1

    # 加入 shanten & waits
    shanten, waits = get_shanten_and_waits(hand_34)
    for tid in waits:
        obs[900][tid] = 1.0
    if -1 <= shanten <= 5:
        obs[901 + shanten][0] = 1.0

    # 2. 自家牌河（最多18張）
    for i, discard in enumerate(table.players[seat].river.discarded_tiles[-18:]):
        tid = discard.tile.to_34_id()
        obs[10 + i][tid] = 1.0

    # 3. 他家牌河
    for other_seat in range(4):
        if other_seat == seat:
            continue
        for i, discard in enumerate(table.players[other_seat].river.discarded_tiles[-18:]):
            tid = discard.tile.to_34_id()
            row = 100 + (other_seat - (1 if other_seat > seat else 0)) * 18 + i
            obs[row][tid] = 1.0

    # 4. 副露（簡化，每家最多4副露 * 每副最多3張）
    for i, meld in enumerate(table.players[seat].melds[:4]):
        for tile in meld.tiles:
            tid = tile.to_34_id()
            obs[200 + i][tid] = 1.0

    for other_seat in range(4):
        if other_seat == seat:
            continue
        for i, meld in enumerate(table.players[other_seat].melds[:4]):
            for tile in meld.tiles:
                tid = tile.to_34_id()
                row = 220 + (other_seat - (1 if other_seat > seat else 0)) * 4 + i
                obs[row][tid] = 1.0

    # 5. 分數
    for i in range(4):
        p = table.players[i].points
        obs[300 + i][0] = min(p, 50000) / 50000.0

    # 6. 風位
    obs[310 + table.players[seat].seat_wind][0] = 1.0  # 自風
    obs[315 + table.round.dealer_id][0] = 1.0          # 莊家

    # 7. 場況
    obs[320][0] = table.round.honba / 10.0
    obs[321][0] = table.round.kyotaku / 10.0
    obs[322][0] = table.wall.remaining_count() / 70.0

    # 8. 寶牌
    for i, tile in enumerate(table.wall.open_dora_wall[:5]):
        tid = tile.to_34_id()
        obs[330 + i][tid] = 1.0

    # 9. 振聽與立直
    if table.players[seat].furiten:
        obs[340][0] = 1.0
    if table.players[seat].is_riichi:
        obs[341][0] = 1.0

    # === ACTION MASK ===
    for tid in legal_actions.get("discard", []):
        mask[tid] = True
    if legal_actions.get("riichi"):
        mask[34] = True
    if legal_actions.get("chi_low"):
        mask[35] = True
    if legal_actions.get("chi_mid"):
        mask[36] = True
    if legal_actions.get("chi_high"):
        mask[37] = True
    if legal_actions.get("pon"):
        mask[38] = True
    if legal_actions.get("daiminkan"):
        mask[39] = True
    if legal_actions.get("ankan"):
        for tid in legal_actions["ankan"]:
            mask[40] = True
    if legal_actions.get("kakan"):
        for tid in legal_actions["kakan"]:
            mask[40] = True
    if legal_actions.get("agari"):
        mask[41] = True
    if legal_actions.get("ryukyoku"):
        mask[42] = True
    # mask[43]~[45] 可保留 pass 類行為

    return obs, mask
