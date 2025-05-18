from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/riichi.py

from mahjong_ai.table.player import Player
from mahjong_ai.table.tile import Tile
from mahjong_ai.table.Hepai import is_tenpai, settle_win

if TYPE_CHECKING:
    from mahjong_ai.table.table import Table

def get_riichi_discard_options(player: Player) -> list[Tile]:
    """
    回傳能丟掉來達成立直（聽牌）的手牌列表
    """
    hand_tiles = player.hand.tiles
    options = []
    for i, tile in enumerate(hand_tiles):
        temp_hand = hand_tiles[:i] + hand_tiles[i+1:]
        if is_tenpai(temp_hand):
            options.append(tile)
    return options

def can_declare_riichi(table: Table, player: Player) -> bool:
    """
    判斷玩家是否符合立直條件：
    - 尚未立直
    - 沒有振聽
    - 分數 >= 1000
    - 聽牌狀態
    """
    for m in player.melds:
        if m.meld_type != "ANKAN":
            print(f"玩家 {player.player_id} 非門清")
            return False  # 有副露且不是暗槓
    if player.is_riichi:
        print(f"玩家 {player.player_id} 已經立直")
        return False
    if player.furiten or player.furiten_temp != -1:
        print(f"玩家 {player.player_id} 為振聽狀態，不能立直")
        return False
    if player.points < 1000:
        print(f"玩家 {player.player_id} 分數不足，無法立直")
        return False
    options = get_riichi_discard_options(player)
    if not options:
        print(f"玩家 {player.player_id} 尚未聽牌")
        return False
    return True

def declare_riichi(table: Table, player: Player, discard_tile: Tile) :
    """
    宣告立直流程：
    - 檢查條件
    - 扣分
    - 加入供託棒
    - 標記立直狀態與立直宣言牌
    """
    #雙立直
    if table.turn == player.player_id + 1 and not table.is_mingpai:
        player.is_daburu_riichi = True
    
    player.riichi_turn = table.turn
    player.is_riichi = True
    player.points -= 1000

    table.round.add_riichi_kyotaku()
    print(f"玩家 {player.player_id} 宣告【立直】，並打出：{discard_tile}")
