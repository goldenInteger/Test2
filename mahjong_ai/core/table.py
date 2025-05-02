from mahjong_ai.core.wall import Wall
from mahjong_ai.core.player import Player
from mahjong_ai.core.tile import Tile
from mahjong_ai.core import meld_handler, round_manager, draw_discard, riichi_handler, win_handler, scoring

class Table:
    def __init__(self):
        self.wall = Wall()
        self.players = [Player(player_id=i) for i in range(4)]
        self.current_turn = 0  # 現在輪到的玩家(0~3)
        self.skip_draw = False  # 吃碰後這一輪不摸牌
        self.riichi_sticks = 0  # 立直棒數量
        self.last_discard_player_id = None

        self.round_wind: str = ""       # 場風（東、南等）
        self.round_number: int = 0      # 局數（0=東一）
        self.dealer_id: int = 0         # 親家玩家 ID
        self.dealer_continue_count: int = 0  # 連莊次數


        round_manager.setup_initial_round(self)

    def draw_phase(self) -> Tile | None:
        return draw_discard.draw_phase(self)

    def discard_phase(self, tile: Tile) -> bool:
        return draw_discard.discard_phase(self, tile)

    def can_pon(self, player: Player, tile: Tile) -> bool:
        return meld_handler.can_pon(player, tile)

    def can_chi(self, player: Player, tile: Tile) -> bool:
        return meld_handler.can_chi(player, tile)

    def handle_melds_after_discard(self, discarded_tile: Tile, from_player_id: int) -> bool:
        return meld_handler.handle_melds_after_discard(self, discarded_tile, from_player_id)

    def try_kakan(self, player_id: int, tile: Tile) -> bool:
        return meld_handler.try_kakan(self, player_id, tile)

    def can_declare_riichi(self, player: Player) -> bool:
        return riichi_handler.can_declare_riichi(self, player)

    def declare_riichi(self, player_id: int) -> None:
        return riichi_handler.declare_riichi(self, player_id)

    def is_tenpai(self, player: Player) -> bool:
        return riichi_handler.is_tenpai(self, player)

    def can_ron(self, player: Player, winning_tile: Tile) -> bool:
        return win_handler.can_ron(self, player, winning_tile)

    def settle_win(self, winner_id: int, score_info: dict, is_tsumo: bool) -> None:
        return win_handler.settle_win(self, winner_id, score_info, is_tsumo)

    def handle_ryukyoku(self) -> None:
        return win_handler.handle_ryukyoku(self)

    def show_scores(self) -> None:
        return scoring.show_scores(self)

    def show_final_result(self) -> None:
        return scoring.show_final_result(self)

    def print_ryukyoku_tenpai_status(self) -> None:
        return scoring.print_ryukyoku_tenpai_status(self)
