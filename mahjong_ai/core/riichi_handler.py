from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/riichi_handler.py

from mahjong_ai.core.player import Player
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.scoring import can_Hepai

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table  # 僅供型別檢查工具使用，不會在執行時引入

def can_declare_riichi(table: Table, player: Player) -> bool:
    """
    判斷是否可以宣告立直
    - 不可副露
    - 必須聽牌
    """
    if player.melds:
        return False
    return is_tenpai(table, player)

def declare_riichi(table: Table, player_id: int) -> None:
    """
    宣告立直行為，扣1000點並放置立直棒
    """
    player = table.players[player_id]
    player.points -= 1000
    table.riichi_sticks += 1
    player.declared_riichi = True
    player.ippatsu_possible = True
    print(f" 玩家{player_id} 宣告立直！扣1000分，目前桌上有{table.riichi_sticks}支立直棒")

def is_tenpai(table: Table, player: Player) -> bool:
    """
    判斷玩家是否為聽牌狀態：
    嘗試每一張可能的 tile 加進去後是否變成和牌型。
    """
    hand = player.hand.tiles
    melds = player.melds

    if len(hand) != 13:
        return False  # 聽牌狀態必須是 13 張，才等一張成和

    for tp in ['man', 'pin', 'sou']:
        for val in range(1, 10):
            test_tile = Tile(tp, val)
            test_hand = hand + [test_tile]
            if can_Hepai(test_hand, melds):
                return True

    for honor_val in range(1, 8):
        test_tile = Tile('honor', honor_val)
        test_hand = hand + [test_tile]
        if can_Hepai(test_hand, melds):
            return True

    return False

