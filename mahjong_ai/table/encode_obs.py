from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
import numpy as np
from mahjong.shanten import Shanten
from mahjong.agari import Agari

if TYPE_CHECKING:
    from mahjong_ai.table.table import Table

# =======================
# Utils: 計算向聽數與聽牌
# =======================
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

# =======================
# 主函數: encode_obs_v2
# =======================
def encode_obs_v2(table: Table, action_types: set[str]) -> Tuple[np.ndarray, np.ndarray]:
    obs = np.zeros((942, 34), dtype=np.float32)
    mask = np.zeros((46,), dtype=bool)
    seat = next(i for i, p in enumerate(table.players) if p.is_ai)

    # === Constants for obs row base ===
    ROW_HAND = 0
    ROW_SELF_RIVER = 10
    ROW_OTHERS_RIVER = 100
    ROW_SELF_MELDS = 200
    ROW_OTHERS_MELDS = 220
    ROW_POINTS = 300
    ROW_SEAT_WIND = 310
    ROW_DEALER = 315
    ROW_SITUATION = 320
    ROW_DORA = 330
    ROW_STATUS = 340
    ROW_WAITS = 900
    ROW_SHANTEN = 930

    # === 1. 手牌 ===
    hand_34 = [0] * 34
    for tile in table.players[seat].hand.tiles:
        tid = tile.to_34_id()
        obs[ROW_HAND][tid] += 1.0
        hand_34[tid] += 1

    # === 2. 向聽與聽牌 ===
    shanten, waits = get_shanten_and_waits(hand_34)
    for tid in waits:
        obs[ROW_WAITS][tid] = 1.0
    if -1 <= shanten <= 5:
        obs[ROW_SHANTEN + shanten][0] = 1.0

    # === 3. 自家牌河（最多18張） ===
    for i, discard in enumerate(table.players[seat].river.discarded_tiles[-18:]):
        tid = discard.tile.to_34_id()
        obs[ROW_SELF_RIVER + i][tid] = 1.0

    # === 4. 他家牌河（3家） ===
    for other_seat in range(4):
        if other_seat == seat:
            continue
        offset = other_seat - 1 if other_seat > seat else other_seat
        for i, discard in enumerate(table.players[other_seat].river.discarded_tiles[-18:]):
            tid = discard.tile.to_34_id()
            obs[ROW_OTHERS_RIVER + offset * 18 + i][tid] = 1.0

    # === 5. 副露資訊 ===
    for i, meld in enumerate(table.players[seat].melds[:4]):
        for tile in meld.tiles:
            tid = tile.to_34_id()
            obs[ROW_SELF_MELDS + i][tid] = 1.0

    for other_seat in range(4):
        if other_seat == seat:
            continue
        offset = other_seat - 1 if other_seat > seat else other_seat
        for i, meld in enumerate(table.players[other_seat].melds[:4]):
            for tile in meld.tiles:
                tid = tile.to_34_id()
                obs[ROW_OTHERS_MELDS + offset * 4 + i][tid] = 1.0

    # === 6. 分數、風位、場況 ===
    for i in range(4):
        obs[ROW_POINTS + i][0] = min(table.players[i].points, 50000) / 50000.0
    obs[ROW_SEAT_WIND + table.players[seat].seat_wind][0] = 1.0
    obs[ROW_DEALER + table.round.dealer_id][0] = 1.0

    obs[ROW_SITUATION][0] = table.round.honba / 10.0
    obs[ROW_SITUATION + 1][0] = table.round.kyotaku / 10.0
    obs[ROW_SITUATION + 2][0] = table.remaining / 70.0

    # === 7. 寶牌 ===
    for i, tile in enumerate(table.wall.open_dora_wall[:5]):
        tid = tile.to_34_id()
        obs[ROW_DORA + i][tid] = 1.0

    # === 8. 狀態：振聽 / 立直 ===
    if table.players[seat].furiten:
        obs[ROW_STATUS][0] = 1.0
    if table.players[seat].is_riichi:
        obs[ROW_STATUS + 1][0] = 1.0

    # === 9. 動作 mask ===
    hand_counts = table.players[seat].hand.to_counts_34()
    legal_discards = [i for i, count in enumerate(hand_counts) if count > 0]
    legal_actions = {
        "discard": legal_discards if "discard" in action_types else [],
        "riichi": "riichi" in action_types,
        "chi_low": "chi_low" in action_types,
        "chi_mid": "chi_mid" in action_types,
        "chi_high": "chi_high" in action_types,
        "pon": "pon" in action_types,
        "daiminkan": "daiminkan" in action_types,
        "ankan": "ankan" in action_types,
        "kakan": "kakan" in action_types,
        "agari": "agari" in action_types,
        "ryukyoku": "ryukyoku" in action_types,
    }

    mask[:] = False
    for tid in legal_actions.get("discard", []):
        mask[tid] = True
    if legal_actions["riichi"]:
        mask[34] = True
    if legal_actions["chi_low"]:
        mask[35] = True
    if legal_actions["chi_mid"]:
        mask[36] = True
    if legal_actions["chi_high"]:
        mask[37] = True
    if legal_actions["pon"]:
        mask[38] = True
    if legal_actions["daiminkan"]:
        mask[39] = True
    if legal_actions["ankan"]:
        mask[40] = True
    if legal_actions["kakan"]:
        mask[41] = True
    if legal_actions["agari"]:
        mask[42] = True
    if legal_actions["ryukyoku"]:
        mask[43] = True
    can_discard = len(legal_actions["discard"]) > 0
    mask[44] = not can_discard  # 正確方式：無牌可丟 → 允許 PASS，否則禁止
    mask[45] = False

    return obs, mask
