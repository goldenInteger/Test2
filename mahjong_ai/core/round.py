from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/round.py

from mahjong_ai.core.wall import Wall
from mahjong_ai.core.player import Player
from mahjong_ai.core import Hepai, Liuju

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table  # 僅供型別檢查工具使用，不會在執行時引入

class Round:
    WINDS = ['東', '南', '西', '北']

    def __init__(self, total_rounds: int):
        self.round_index = 0             # 目前局數 0=東一
        self.dealer_id = 0               # 親家 ID
        self.dealer_continue_count = 0   # 連莊次數
        self.honba = 0                   # 場棒（每次連莊 +1，對應 +300 / +1500 等）
        self.kyotaku = 0                 # 供託棒（立直時 +1000 點）
        self.total_rounds = total_rounds

    def add_riichi_kyotaku(self):
        self.kyotaku += 1000

    def pay_honba_bonus(self, winner: Player):
        bonus = self.honba * 300
        winner.points += bonus

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
        table.current_turn = 0 #換誰摸打
        table.turn = 0 # 摸打次數
        table.skip_draw = False #跳過抽牌
        table.skip_discard = False #跳過出牌
        table.last_discard_player_id = None #上一位丟牌的玩家
        table.rinshan_draw = False #抽嶺上牌
        table.round_over = False #遊戲是否結束
        table.is_mingpai = False
        table.is_liuju = False
        table.winner = None
        table.wall = Wall()
        for player in table.players:
            player.reset()

        for _ in range(13):
            for player in table.players:
                player.draw_tile_from_wall(table.wall)

        table.current_turn = self.dealer_id
        print(f"\n==== 【{self.get_display_string()}】 ====")

    def handle_round_end(self, table: Table):
        """
        局結束後的處理：
        - 親家胡 → 連莊 +1（honba +1）
        - 否則換親，進入下一局，honba 歸零
        - kyotaku 照常累積（由胡牌者領取）
        """
        winner_id: int
        # 流局
        if table.is_liuju:
            table.winner = Hepai.can_nagashi_mangan(table)
            # 無法流局滿貫
            if Hepai.can_nagashi_mangan(table) == None:
                Liuju.check_tenpai_bonus(table.players)
                winner_id = -1
            # 可以流局滿貫
            else:
                winner_id = table.winner.player_id
                Hepai.settle_win(table)
        # 沒流局
        else:
            winner_id = table.winner.player_id
            Hepai.can_chiihou(table)
            Hepai.can_ippatsu(table)
            Hepai.can_renhou(table)
            Hepai.can_tenhou(table)
            Hepai.settle_win(table)
        # 連莊
        if winner_id == self.dealer_id:
            self.dealer_continue_count += 1
            self.honba += 1
            print(f"【連莊】玩家{self.dealer_id}續親（連莊 {self.dealer_continue_count}）")
        else:
            self.round_index += 1
            self.dealer_id = (self.dealer_id + 1) % 4
            # 換座風
            for p in range(4):
                table.players[(self.dealer_id + p) % 4].seat_wind = p
            self.dealer_continue_count = 0
            self.honba = 0
            print(f"【換親】親家 → 玩家{self.dealer_id}，進入 {self.get_display_string()}")

    def is_game_end(self) -> bool:
        # 東風戰（只打東1～東4）
        if self.total_rounds == 4:
            return self.round_index >= 4
        # 半莊戰（打東1～南4，共8局）
        elif self.total_rounds == 8:
            return self.round_index >= 8
        # 全莊戰（打東南西北1～4，共16局）
        elif self.total_rounds == 16:
            return self.round_index >= 16
        # 安全預設
        return self.round_index >= self.total_rounds

