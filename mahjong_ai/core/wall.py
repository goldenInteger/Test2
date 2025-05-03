# mahjong_ai/core/wall.py

import random
from mahjong_ai.core.tile import Tile
from typing import List, Optional

class Wall:
    def __init__(self):
        """
        初始化牌山：產生136張牌並進行洗牌
        """
        self.tiles: List[Tile] = self._create_full_wall()
        self.shuffle_tiles()
        print(f"牌山總張數 {len(self.tiles)}")

    def _create_full_wall(self) -> List[Tile]:
        """
        建立完整136張牌的列表（4張x每種牌）
        萬、筒、索：1-9 各4張
        字牌：東南西北白發中（1-7）各4張
        """
        tiles = []

        # 萬子 1m ~ 9m
        for number in range(1, 10):
            for _ in range(4):
                tiles.append(Tile(tile_type='man', tile_value=number))

        # 筒子 1p ~ 9p
        for number in range(1, 10):
            for _ in range(4):
                tiles.append(Tile(tile_type='pin', tile_value=number))

        # 索子 1s ~ 9s
        for number in range(1, 10):
            for _ in range(4):
                tiles.append(Tile(tile_type='sou', tile_value=number))

        # 字牌 1z ~ 7z（東南西北白發中）
        for number in range(1, 8):
            for _ in range(4):
                tiles.append(Tile(tile_type='honor', tile_value=number))

        return tiles

    def shuffle_tiles(self) -> None:
        """
        隨機打亂牌堆（使用 random.shuffle）
        """
        random.shuffle(self.tiles)

    def draw_tile(self) -> Optional[Tile]:
        """
        從牌堆最上方摸一張牌。
        若牌堆已空，回傳 None。
        """
        if self.is_empty():
            return None
        return self.tiles.pop(0)

    def draw_haitei_tile(self) -> Optional[Tile]:
        """
        摸海底（最後一張）牌，通常用於海底摸月（Haitei）判定。
        """
        if self.is_empty():
            return None
        return self.tiles.pop(-1)

    def draw_rinshan_tile(self) -> Optional[Tile]:
        """
        槓牌後的補牌（嶺上開花用）
        """
        if self.is_empty():
            return None
        return self.tiles.pop(-1)

    def is_empty(self) -> bool:
        """
        判斷牌堆是否為空
        """
        return len(self.tiles) == 0

    def remaining_count(self) -> int:
        """
        回傳目前牌堆剩餘張數
        """
        return len(self.tiles)
