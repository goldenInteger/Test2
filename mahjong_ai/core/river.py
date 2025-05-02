# mahjong_ai/core/river.py

from mahjong_ai.core.tile import Tile

class River:
    def __init__(self):
        """
        初始化河牌區（捨牌區）
        """
        self.discarded_tiles = []

    def add_discard(self, tile: Tile):
        """
        增加一張被打出去的牌
        """
        self.discarded_tiles.append(tile)

    def get_discarded_tiles(self):
        """
        取得目前所有打過的牌（依序）
        """
        return self.discarded_tiles

    def __str__(self):
        """
        回傳河牌區的字串格式
        """
        return ' '.join(str(tile) for tile in self.discarded_tiles)
