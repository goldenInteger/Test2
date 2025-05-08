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

        self.furiten = False             # 玩家是否振聽
        self.furiten_temp = -1
        self.win_tile: Tile = None       # 完成和牌的牌

        self.seat_wind = player_id       # 座風（0=東, 1=南, 2=西, 3=北）
        self.round_wind = 0              # 場風（通常由 Table 控制）
        self.last_chi_meld: Meld | None = None


        self.is_tsumo = False	        # 是否為自摸和牌
        self.is_riichi = False	        # 是否立直
        self.is_ippatsu	= False	        # 是否一發
        self.is_rinshan	= False	        # 是否嶺上開花
        self.is_chankan	= False	        # 是否搶槓
        self.is_haitei = False	        # 是否海底撈月
        self.is_houtei = False	        # 是否河底撈魚
        self.is_daburu_riichi = False   # 是否雙立直
        self.is_nagashi_mangan = False  # 流局滿貫
        self.is_tenhou = False          # 天和
        self.is_renhou = False          # 人和
        self.is_chiihou = False         # 地和

    def reset(self):
        """
        重設此玩家的狀態，通常用於新局開始時。
        """
        self.hand = Hand()
        self.river = River()
        self.melds = []
        self.points = 25000
        self.furiten = False
        self.furiten_temp = -1
        self.riichi_turn = -1

        self.seat_wind = 0
        self.round_wind = 0
        self.last_chi_meld = None
        self.win_tile = None

        self.is_tsumo = False	
        self.is_riichi = False	
        self.is_ippatsu	= False	
        self.is_rinshan	= False	
        self.is_chankan	= False	
        self.is_haitei = False	
        self.is_houtei = False
        self.is_daburu_riichi = False 
        self.is_nagashi_mangan = False 
        self.is_tenhou = False  
        self.is_renhou = False  
        self.is_chiihou = False 

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

    def add_meld(self, meld: Meld) -> None:
        """
        加入一組副露（吃/碰/槓）到自己的紀錄中。
        """
        self.melds.append(meld)
