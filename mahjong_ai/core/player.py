# mahjong_ai/core/player.py

from mahjong_ai.core.hand import Hand
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.wall import Wall
from mahjong_ai.core.river import River
from mahjong_ai.core.scoring import can_Hepai

class Player:
    def __init__(self, player_id: int):
        """
        初始化玩家，給一個編號（0-3）
        """
        self.player_id = player_id
        self.hand = Hand()
        self.river = River()
        self.melds = [] 
        self.points = 25000  # ✅ 初始分數25000
        self.declared_riichi = False  # 是否已經立直
        self.ippatsu_possible = False  # 是否一發可能


    def reset(self):
        self.hand = Hand()
        self.river = River()
        self.melds = []
        self.points = 25000  
        self.declared_riichi = False  
        self.ippatsu_possible = False  


    def draw_tile_from_wall(self, wall: Wall) -> Tile:
        """
        從牌堆摸一張牌，加進自己的手牌。
        """
        tile = wall.draw_tile()
        if tile:
            self.hand.add_tile(tile)
        return tile

    def discard_tile_from_hand(self, tile: Tile) -> bool:
        """
        打出一張牌：從手牌移除 + 加入河牌區。
        """
        success = self.hand.remove_tile(tile)
        if success:
            self.river.add_discard(tile)
        return success