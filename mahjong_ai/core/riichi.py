from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/riichi.py

from mahjong_ai.core.player import Player
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.Hepai import is_tenpai, settle_win

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table

def can_declare_riichi(table: Table, player: Player) -> bool:
    """
    判斷玩家是否符合立直條件：
    - 尚未立直
    - 沒有振聽
    - 分數 >= 1000
    - 聽牌狀態
    """
    if player.riichi_declared:
        print(f"玩家 {player.player_id} 已經立直")
        return False
    if player.furiten:
        print(f"玩家 {player.player_id} 為振聽狀態，不能立直")
        return False
    if player.points < 1000:
        print(f"玩家 {player.player_id} 分數不足，無法立直")
        return False
    if not is_tenpai(player):
        print(f"玩家 {player.player_id} 尚未聽牌")
        return False
    return True

def declare_riichi(table: Table, player: Player, discard_tile: Tile) -> bool:
    """
    宣告立直流程：
    - 檢查條件
    - 扣分
    - 加入供託棒
    - 標記立直狀態與立直宣言牌
    """
    if not can_declare_riichi(table, player):
        return False

    player.riichi_declared = True
    player.pending_riichi_tile = discard_tile
    player.points -= 1000

    table.add_riichi_kyotaku()
    print(f"玩家 {player.player_id} 宣告【立直】，並打出：{discard_tile}")
    return True

def evaluate_riichi_win(table: Table, player: Player, win_tile: Tile, is_tsumo: bool) -> dict:
    """
    胡牌後結算番與得分，委派給 settle_win。
    """
    return settle_win(table, player, win_tile, is_tsumo=is_tsumo)
