from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/round.py

from mahjong_ai.core.wall import Wall

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table  # 僅供型別檢查工具使用，不會在執行時引入

class Round:
    WINDS = ['東', '南', '西', '北']

    def __init__(self, total_rounds: int = 4):
        self.round_index = 0             # 目前局數 0=東一
        self.dealer_id = 0               # 親家 ID
        self.dealer_continue_count = 0   # 連莊次數
        self.honba = 0                   # 場棒（每次連莊 +1，對應 +300 / +1500 等）
        self.kyotaku = 0                 # 供託棒（立直時 +1000 點）
        self.total_rounds = total_rounds

    @property
    def round_number(self) -> int:
        return self.round_index + 1

    @property
    def round_wind(self) -> str:
        return self.WINDS[self.round_index // 4]

    def get_display_string(self) -> str:
        return f"{self.round_wind}{self.round_number}局（親家：玩家{self.dealer_id}）｜場棒：{self.honba} 本｜供託：{self.kyotaku} 點"

    def start_round(self, table: Table):
        """
        一局開始：
        - 重設所有玩家
        - 建立新牌山
        - 每人發13張牌
        - 設定 current_turn 為親家
        """
        table.wall = Wall()
        for player in table.players:
            player.reset()

        for _ in range(13):
            for player in table.players:
                player.draw_tile_from_wall(table.wall)

        table.current_turn = self.dealer_id
        print(f"\n==== 【{self.get_display_string()}】 ====")

    def handle_round_end(self, winner_id: int):
        """
        局結束後的處理：
        - 親家胡 → 連莊 +1（honba +1）
        - 否則換親，進入下一局，honba 歸零
        - kyotaku 照常累積（由胡牌者領取）
        """
        if winner_id == self.dealer_id:
            self.dealer_continue_count += 1
            self.honba += 1
            print(f"【連莊】玩家{self.dealer_id}續親（連莊 {self.dealer_continue_count}）")
        else:
            self.round_index += 1
            self.dealer_id = (self.dealer_id + 1) % 4
            self.dealer_continue_count = 0
            self.honba = 0
            print(f"【換親】親家 → 玩家{self.dealer_id}，進入 {self.get_display_string()}")

    def is_game_end(self) -> bool:
        return self.round_index >= self.total_rounds
