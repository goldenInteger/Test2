from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/win_handler.py

from typing import Dict
from mahjong_ai.core.player import Player
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.scoring import can_Hepai, calculate_hand_score, print_score_result
from mahjong_ai.core.yaku_checker import detect_yakus

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table  # 僅供型別檢查工具使用，不會在執行時引入

def can_ron(table: Table, player: Player, winning_tile: Tile) -> bool:
    """
    判斷玩家是否可以榮和（含振聽檢查）
    """
    if player.declared_riichi and any(t.is_same_tile(winning_tile) for t in player.passed_tiles):
        print(f"⚠️ 玩家 {player.player_id} 無法榮和 {winning_tile}，因為該牌振聽")
        return False

    temp_hand = player.hand.tiles.copy()
    temp_hand.append(winning_tile)
    return can_Hepai(temp_hand, player.melds)

def settle_win(table: Table, winner_id: int, score_info: Dict, is_tsumo: bool) -> None:
    """
    處理胡牌後的點數計算與立直棒收取
    """
    winner = table.players[winner_id]

    if is_tsumo:
        if "payment_each" in score_info:
            payment = score_info["payment_each"]
            for i, p in enumerate(table.players):
                if i != winner_id:
                    p.points -= payment
                    winner.points += payment
        elif "payment_to_dealer" in score_info:
            for i, p in enumerate(table.players):
                if i == table.dealer_id:
                    p.points -= score_info["payment_to_dealer"]
                    winner.points += score_info["payment_to_dealer"]
                elif i != winner_id:
                    p.points -= score_info["payment_to_others"]
                    winner.points += score_info["payment_to_others"]
    else:
        # 放槍（榮和）
        loser = table.players[table.last_discard_player_id]
        payment = score_info["score"]
        loser.points -= payment
        winner.points += payment

    # 胡牌者收立直棒
    if table.riichi_sticks > 0:
        bonus = table.riichi_sticks * 1000
        winner.points += bonus
        print(f" 玩家{winner_id} 收取立直棒 {table.riichi_sticks}支，加{bonus}點")
        table.riichi_sticks = 0

def handle_ryukyoku(table: Table) -> None:
    """
    處理流局（未和牌），分配流局罰符
    """
    tenpai_players = []
    noten_players = []

    for p in table.players:
        if table.is_tenpai(p):
            tenpai_players.append(p)
        else:
            noten_players.append(p)

    if not tenpai_players or not noten_players:
        print("=== 全員聽牌或全員未聽牌，無流局罰符 ===")
        return

    total_penalty = 3000
    per_tenpai = total_penalty // len(tenpai_players)
    per_noten = total_penalty // len(noten_players)

    for p in noten_players:
        p.points -= per_noten
    for p in tenpai_players:
        p.points += per_tenpai

    print(f"=== 流局滿貫結算 ===")
    print(f"聽牌者 +{per_tenpai}，未聽者 -{per_noten}")
