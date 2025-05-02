from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/round_manager.py

from mahjong_ai.core.wall import Wall

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table  # 僅供型別檢查工具使用，不會在執行時引入

def start_new_round(table: Table) -> None:
    """
    每局開始時，重設場面
    """
    table.wall = Wall()
    for player in table.players:
        player.reset()
    table.dealer_id = table.dealer_id % 4
    table.current_turn = table.dealer_id

    deal_initial_hands(table)
    print(f"\n==== 【{table.round_wind}{table.round_number + 1}局】 親家是 玩家{table.dealer_id} ====")

def is_game_over(table: Table) -> bool:
    """
    判斷牌山是否打完
    """
    return len(table.wall.tiles) == 0

def is_game_end(table: Table) -> bool:
    """
    判斷整個東風場是否結束
    """
    return table.round_number >= 4

def end_round(table: Table, winner_id: int) -> None:
    """
    結束一局：判斷是否連莊或換親
    """
    if winner_id == table.dealer_id:
        table.dealer_continue_count += 1
        print(f"【連莊】玩家{table.dealer_id}續親，連莊{table.dealer_continue_count}次！")
    else:
        table.dealer_id = (table.dealer_id + 1) % 4
        table.round_number += 1
        table.dealer_continue_count = 0
        print(f"【換親】親家換到玩家{table.dealer_id}，局數進入 {table.round_wind}{table.round_number + 1}局")

    if not is_game_end(table):
        start_new_round(table)
    else:
        print("\n==== 【東場結束！整場結束】 ====")

def deal_initial_hands(table: Table) -> None:
    """
    起手發牌，每人摸13張。
    """
    for _ in range(13):
        for player in table.players:
            player.draw_tile_from_wall(table.wall)

def setup_initial_round(table: Table) -> None:
    """
    一開始初始化整個場面
    """
    table.round_wind = '東'
    table.round_number = 0
    table.dealer_id = 0
    table.dealer_continue_count = 0

    table.wall = Wall()
    deal_initial_hands(table)
    print(f"\n==== 【{table.round_wind}{table.round_number + 1}局】 親家是 玩家{table.dealer_id} ====")
