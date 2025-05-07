# mahjong_ai/core/player.py

from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.tile import TilesConverter
from mahjong_ai.core.hand import Hand
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.wall import Wall
from mahjong_ai.core.river import River
from mahjong_ai.core.meld import Meld
from mahjong.agari import Agari

class Player:
    def __init__(self, player_id: int):
        """
        初始化一位玩家。
        - player_id: 玩家編號（0~3）
        """
        self.player_id = player_id
        self.hand = Hand()               # 手牌
        self.river = River()             # 捨牌區
        self.melds: list[Meld] = []      # 副露紀錄
        self.points = 25000              # 初始分數

        self.riichi_declared = False     # 是否已立直
        self.ippatsu_possible = False    # 是否還處於一發可能狀態
        self.furiten = False             # 玩家是否振聽

        self.seat_wind = 0               # 座風（0=東, 1=南, 2=西, 3=北）
        self.round_wind = 0              # 場風（通常由 Table 控制）

    def reset(self):
        """
        重設此玩家的狀態，通常用於新局開始時。
        """
        self.hand = Hand()
        self.river = River()
        self.melds = []
        self.points = 25000
        self.riichi_declared = False
        self.ippatsu_possible = False
        self.furiten = False
        self.seat_wind = 0
        self.round_wind = 0

    def draw_tile_from_wall(self, wall: Wall) -> Tile:
        """
        從牌堆摸一張牌並加入手牌。
        """
        tile = wall.draw_tile()
        if tile:
            self.hand.add_tile(tile)
        return tile

    def draw_rinshan_tile(self, wall: Wall) -> Tile:
        """
        槓後從牌堆尾端抽嶺上牌。
        """
        tile = wall.draw_rinshan_tile()
        if tile:
            self.hand.add_tile(tile)
        return tile

    def discard_tile_from_hand(self, tile: Tile) -> bool:
        """
        將一張牌從手牌中打出並加入河牌區。
        回傳是否成功（是否存在該牌）。
        並觸發振聽更新。
        """
        success = self.hand.remove_tile(tile)
        if success:
            self.river.add_discard(tile)
            self.update_furiten()
        return success

    def update_furiten(self):
        """
        若打過的牌出現在任何一種可能胡牌的情境中，則進入振聽。
        """
        agari = Agari()
        tiles = self.hand.to_counts_34()
        for i in range(34):
            tiles[i] += 1
            if agari.is_agari(tiles):
                for t in self.river.discarded_tiles:
                    if t.tile.to_34_id() == i:
                        self.furiten = True
                        return
            tiles[i] -= 1
        self.furiten = False

    def declare_riichi(self) -> bool:
        """
        嘗試宣告立直（條件簡化版）：
        - 未立直
        - 分數足夠
        - 為聽牌狀態
        成功則扣1000點並啟用一發狀態。
        """
        if self.riichi_declared or self.points < 1000:
            return False
        from mahjong.shanten import Shanten
        tiles_34 = self.hand.to_counts_34()
        shanten = Shanten().calculate_shanten(tiles_34)
        if shanten == 0:
            self.riichi_declared = True
            self.points -= 1000
            self.ippatsu_possible = True
            return True
        return False

    def add_meld(self, meld: Meld) -> None:
        """
        加入一組副露（吃/碰/槓）到自己的紀錄中。
        """
        self.melds.append(meld)

    def receive_tile(self, tile: Tile) -> None:
        """
        把一張牌直接加入手牌，通常用於副露後獲得的牌。
        """
        self.hand.add_tile(tile)

    def can_win(self) -> bool:
        """
        使用 mahjong 套件判斷目前手牌是否可胡。
        副露支援中（以 melds 計算），不考慮和了形式（如自摸/榮和）。
        """
        agari = Agari()
        tiles_34 = self.hand.to_counts_34()
        # 傳入副露 tiles（每副 meld 都拆開）
        melds_34 = []
        for meld in self.melds:
            meld_ids = [tile.to_34_id() for tile in meld.tiles]
            melds_34.append(meld_ids)
        return agari.is_agari(tiles_34, melds_34)

    def get_win_result(self, win_tile: Tile, is_tsumo: bool = True) -> dict:
        """
        使用 mahjong 套件完整計算胡牌結果。
        - win_tile: 和牌那張
        - is_tsumo: 是否為自摸（否則為榮和）

        回傳 dict，包含番種名稱、番數、得點等資訊。
        """
        calculator = HandCalculator()
        tiles_136 = [tile.get_all_136_ids()[0] for tile in self.hand.get_tile_objects()]
        win_tile_id = win_tile.get_all_136_ids()[0]
        melds = []
        config = HandConfig(
            is_tsumo=is_tsumo,
            is_riichi=self.riichi_declared,
            player_wind=self.seat_wind,
            round_wind=self.round_wind,
            has_dora=False,
        )
        result = calculator.estimate_hand_value(
            TilesConverter.to_34_array(tiles_136),
            win_tile_id=win_tile_id,
            melds=melds,
            config=config
        )
        if result.error:
            return {"error": result.error.as_string()}
        return {
            "han": result.han,
            "fu": result.fu,
            "cost": result.cost.__dict__,
            "yaku": [(y.name, y.han) for y in result.yaku],
            "fu_details": result.fu_details
        }
    def show_hand(self):
        """
        印出玩家手牌的中文表示。
        """
        tiles_str = ' '.join(str(tile) for tile in self.hand.tiles)
        print(f"玩家 {self.player_id} 的手牌：{tiles_str}")