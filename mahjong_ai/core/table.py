# mahjong_ai/core/table.py
from mahjong_ai.core.wall import Wall
from mahjong_ai.core.player import Player
from mahjong_ai.core.tile import Tile
from mahjong_ai.core import meld_handler, riichi, round, draw_discard, Hepai
from mahjong_ai.core.round import Round

class Table:
    def __init__(self):
        self.round = Round(total_rounds=4)  # 東風戰
        self.players = [Player(i) for i in range(4)]
        self.wall = None
        self.current_turn = 0
        self.skip_draw = False  # 吃碰後跳過摸牌
        self.last_discard_player_id = None
        self.last_discard_tile: Tile | None = None
        self.rinshan_draw = False    # 嶺上摸牌觸發用
        self.gang_from = None        # 記錄加槓發起者，用於搶槓判定
        self.round.start_round(self)

    def handle_end_of_round(self, winner_id: int):
        self.round.handle_round_end(winner_id)
        if self.round.is_game_end():
            print("\n==== 遊戲結束 ====")
        else:
            self.round.start_round(self)

    def add_riichi_kyotaku(self):
        self.round.kyotaku += 1000

    def pay_honba_bonus(self, winner: Player):
        bonus = self.round.honba * 300
        winner.points += bonus

    def get_round_info(self):
        return self.round.get_display_string()

    def step(self):
        player = self.players[self.current_turn]

        print(f"玩家 {player.player_id} 摸牌中")
        tile = player.draw_tile_from_wall(self.wall)

        if tile is None:
            print("牌山已空，流局。")
            self.handle_end_of_round(-1)
            return

        print(f"玩家 {player.player_id} 摸到：{tile}")

        # 自摸判定
        if Hepai.can_tsumo(player, tile):
            print(f"玩家 {player.player_id} 自摸！")
            result = Hepai.settle_win(self, player, tile, is_tsumo=True)
            print(f"番型：{result.get('yaku', [])}｜得分：{result.get('score')}\n")
            self.handle_end_of_round(player.player_id)
            return

        # 嘗試立直（打第一張）
        if riichi.can_declare_riichi(self, player):
            for t in player.hand.tiles:
                if riichi.declare_riichi(self, player, t):
                    player.discard_tile_from_hand(t)
                    self.last_discard_tile = t
                    self.last_discard_player_id = player.player_id
                    print(f"玩家 {player.player_id} 立直打出：{t}")
                    self.check_ron(t, player.player_id)
                    self.current_turn = (self.current_turn + 1) % 4
                    return

        # 否則打出第一張
        discard = player.hand.tiles[0]
        player.discard_tile_from_hand(discard)
        self.last_discard_tile = discard
        self.last_discard_player_id = player.player_id
        print(f"玩家 {player.player_id} 打出：{discard}")

        self.check_ron(discard, player.player_id)
        self.current_turn = (self.current_turn + 1) % 4

    def check_ron(self, tile: Tile, from_pid: int):
        for i, p in enumerate(self.players):
            if i == from_pid:
                continue
            if not p.furiten and Hepai.can_ron(self, p, tile):
                print(f"玩家 {i} 榮和！ ← {tile}")
                result = Hepai.settle_win(self, p, tile, is_tsumo=False)
                print(f"番型：{result.get('yaku', [])}｜得分：{result.get('score')}\n")
                self.handle_end_of_round(i)
                return
