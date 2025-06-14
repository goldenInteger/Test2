from mahjong_ai.table.wall import Wall
from mahjong_ai.table.player import Player
from mahjong_ai.table.tile import Tile
from mahjong_ai.table import Chupai, Mingpai, riichi, Hepai, Liuju
from mahjong_ai.table.round import Round
from mahjong_ai.buffer import ReplayBuffer
import random
# TODO: 出牌邏輯

class Table:
    def __init__(self):
        self.round = Round(total_rounds=4)  # 東風戰
        self.players = [Player(i) for i in range(4)]
        self.wall = Wall()
        self.is_mingpai = False # 是否鳴牌過了
        self.is_liuju = False
        self.current_turn = 0 #換誰摸打
        self.turn = 0 # 摸打次數
        self.skip_draw = False #跳過抽牌
        self.skip_discard = False #跳過出牌
        self.last_discard_player_id = None #上一位丟牌的玩家
        self.winner: Player = None # 勝者
        self.rinshan_draw = False # 抽嶺上牌
        self.round_over = False # 遊戲是否結束
        self.round.start_round(self)
        self.buffer = None
        self.remaining = self.wall.remaining_count()

    def run_game_loop(self, buffer=None):
        self.buffer = buffer
        print(" 開始整場對局")
        main_player_id = random.randint(0, 3)
        self.players[main_player_id].is_ai = True
        while not self.round.is_game_end():
            self.round.start_round(self)
            while not self.round_over:
                self.step()
            self.round.handle_round_end(self)
        print("\n==== 遊戲結束 ====")
        for p in range(4):
            if self.players[p].is_ai:
                print(f"\n{p}isAI")
            print(f"\n{p} : {self.players[p].points}")

    def step(self):
        player = self.players[self.current_turn]
        # 特殊流局
         # 九種九牌
        if self.turn < 4 and not self.is_mingpai:
            if Liuju.is_kyuushu_kyuuhai(player):
                if Mingpai.ask_player_action(self, player, "liuju", None):
                    self.is_liuju = True
                    self.round_over = True
                    return
        # 四家立直
        if Liuju.is_suucha_riichi(self.players):
            self.is_liuju = True
            self.round_over = True
            return
        # 正確流程摸打(紀錄一巡用)
        if not self.skip_discard and not self.skip_draw and not self.rinshan_draw:
            self.turn = self.turn + 1
        print(f"玩家{player.player_id}手牌：", [str(tile) for tile in player.hand.tiles])
        print(f"玩家{player.player_id}副露：", [str(tile) for tile in player.melds])
        # 摸牌
        draw_tile = Chupai.draw_phase(self, player)
        # 提前結束
        if self.skip_discard:
            self.skip_discard = False
            return
        if self.round_over:
            return
        # TODO : 之後這裡要加出牌邏輯
        discard_tile: Tile

        # 立直
        if not player.is_riichi:
            if riichi.can_declare_riichi(self, player):
                riichi_options = riichi.get_riichi_discard_options(player)
                chosen_option = Mingpai.ask_player_action(self, player, "riichi", None, riichi_options)
                if chosen_option:
                    riichi.declare_riichi(self, player, chosen_option)
                    discard_tile = chosen_option
                else:
                    discard_tile = player.discard(self)
            else:
                discard_tile = player.discard(self)
        else:
            discard_tile = draw_tile   # 已立直，自動打摸牌

        # 丟牌
        Chupai.discard_phase(self, discard_tile)
        # 四風連打
        if self.turn == 4 and not self.is_mingpai:
            if Liuju.is_sufon_renda(self.players):
                self.is_liuju = True
                self.round_over = True
                return
        # 若無任何副露，輪到下一位
        if not self.skip_draw and not self.rinshan_draw:
            self.current_turn = (self.current_turn + 1) % 4