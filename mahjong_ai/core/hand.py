# mahjong_ai/core/hand.py

from mahjong_ai.core.tile import Tile

class Hand:
    def __init__(self):
        """
        初始化一個空手牌。
        """
        self.tiles = []

    def add_tile(self, tile: Tile) -> None:
        """
        加一張牌到手牌。
        """
        self.tiles.append(tile)
        self.sort_hand()

    def remove_tile(self, tile: Tile) -> bool:
        """
        從手牌中移除指定的牌。
        如果成功移除回傳True，否則回傳False。
        """
        for existing_tile in self.tiles:
            if existing_tile.is_same_tile(tile):
                self.tiles.remove(existing_tile)
                return True
        return False

    def sort_hand(self) -> None:
        """
        把手牌按照 花色優先、數字升冪 排序。
        """
        def tile_sort_key(tile: Tile):
            type_order = {'man': 0, 'pin': 1, 'sou': 2, 'honor': 3}
            return (type_order.get(tile.tile_type, 4), tile.tile_value)
        
        self.tiles.sort(key=tile_sort_key)

