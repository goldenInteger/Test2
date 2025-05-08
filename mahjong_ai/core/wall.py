# mahjong_ai/core/wall.py
from __future__ import annotations
from typing import TYPE_CHECKING

import random
from mahjong_ai.core.tile import Tile
from typing import List, Optional

if TYPE_CHECKING:
    from mahjong_ai.core.table import Player
class Wall:
    def __init__(self):
        self.first_rinshan_player: Player = None
        """
        初始化牌山：產生136張牌並進行洗牌
        """
        self.tiles: List[Tile] = self._create_full_wall()
        self.shuffle_tiles()
        
        """
        建立王牌區（dead wall）14 張：含 5 組寶牌、嶺上牌
        """
        self.dora_wall: list[Tile] = [self.tiles.pop() for _ in range(5)]
        self.uradora_wall: list[Tile] = [self.tiles.pop() for _ in range(5)]
        self.rinshan_wall: list[Tile] = [self.tiles.pop() for _ in range(4)]

        self.open_dora_wall: list[Tile] = self.draw_dora_indicators()

    def _create_full_wall(self) -> List[Tile]:
        """
        建立完整136張牌的列表（4張x每種牌）
        萬、筒、索：1-9 各4張
        字牌：東南西北白發中（1-7）各4張
        """
        tiles = []

        # 萬子（1m~9m）
        for number in range(1, 10):
            for i in range(4):
                is_aka = (number == 5 and i == 0)  # 紅5萬
                tiles.append(Tile(tile_type='man', tile_value=number, is_aka_dora=is_aka))

        # 筒子（1p~9p）
        for number in range(1, 10):
            for i in range(4):
                is_aka = (number == 5 and i == 0)  # 紅5筒
                tiles.append(Tile(tile_type='pin', tile_value=number, is_aka_dora=is_aka))

        # 索子（1s~9s）
        for number in range(1, 10):
            for i in range(4):
                is_aka = (number == 5 and i == 0)  # 紅5索
                tiles.append(Tile(tile_type='sou', tile_value=number, is_aka_dora=is_aka))

        # 字牌（東南西北白發中）
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

    def draw_dora_indicators(self) -> Tile:
        """
        取得表寶牌表示牌
        """
        return self.dora_wall.pop(0)

    def draw_rinshan_tile(self, player: Player) -> Tile | None:
        """
        從王牌尾部抽一張嶺上牌（加槓補牌）
        """
        if len(self.rinshan_wall) == 4:
            self.first_rinshan_player = player
        # 四槓散了
        if len(self.rinshan_wall) == 1:
            if(player.player_id != self.first_rinshan_player.player_id):
                return None
        if len(self.rinshan_wall) == 0:
            return None
        return self.rinshan_wall.pop(0)

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
