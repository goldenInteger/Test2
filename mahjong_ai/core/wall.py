# mahjong_ai/core/wall.py

import random
from mahjong_ai.core.tile import Tile

class Wall:
    def __init__(self):
        """
        建立完整的136張麻將牌並洗牌
        """
        self.tiles = self._create_full_wall()
        self.shuffle_tiles()

        print(f"牌山總張數{len(self.tiles)}")

    def _create_full_wall(self) -> list:
        """
        創建完整的136張麻將牌
        """
        tiles = []

        # 萬子
        for number in range(1, 10):
            for _ in range(4):
                tiles.append(Tile(tile_type='man', tile_value=number))

        # 筒子
        for number in range(1, 10):
            for _ in range(4):
                tiles.append(Tile(tile_type='pin', tile_value=number))

        # 索子
        for number in range(1, 10):
            for _ in range(4):
                tiles.append(Tile(tile_type='sou', tile_value=number))

        # 字牌
        for number in range(1, 8):
            for _ in range(4):
                tiles.append(Tile(tile_type='honor', tile_value=number))

        return tiles

    def shuffle_tiles(self) -> None:
        """
        隨機打亂牌堆
        """
        random.shuffle(self.tiles)

    def draw_tile(self) -> Tile:
        """
        從牌堆最上面摸一張牌
        """
        if self.is_empty():
            return None
        return self.tiles.pop(0)

    def is_empty(self) -> bool:
        """
        判斷牌堆是否已經空了
        """
        return len(self.tiles) == 0
