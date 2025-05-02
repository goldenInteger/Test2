from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/draw_discard.py

from mahjong_ai.core.tile import Tile

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table  # 僅供型別檢查工具使用，不會在執行時引入

def draw_phase(table: Table) -> Tile | None:
    """
    玩家進入摸牌階段。
    若上一輪吃碰槓，則跳過這輪摸牌。
    """
    if table.skip_draw:
        table.skip_draw = False
        return None

    player = table.players[table.current_turn]
    return player.draw_tile_from_wall(table.wall)

def discard_phase(table: Table, tile: Tile) -> bool:
    """
    玩家進入出牌階段。
    丟出指定 tile 後輪到下一位玩家。
    """
    table.last_discard_player_id = table.current_turn
    player = table.players[table.current_turn]
    result = player.discard_tile_from_hand(tile)
    table.current_turn = (table.current_turn + 1) % 4
    return result
