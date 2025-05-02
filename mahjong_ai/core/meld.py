# mahjong_ai/core/meld.py

from enum import Enum
from mahjong_ai.core.tile import Tile

class MeldType(Enum):
    CHI = "Chi"  # 吃
    PON = "Pon"  # 碰
    KAN = "Kan"  # 槓（先不區分明槓暗槓）

class Meld:
    def __init__(self, tiles: list, meld_type: MeldType, from_player_id: int):
        """
        tiles: 副露的牌列表（通常是3張，槓是4張）
        meld_type: 副露類型（吃/碰/槓）
        from_player_id: 哪個玩家打出的牌讓自己副露的
        """
        self.tiles = tiles
        self.meld_type = meld_type
        self.from_player_id = from_player_id

    def __str__(self):
        tile_str = ' '.join(str(t) for t in self.tiles)
        return f"[{self.meld_type.value}] {tile_str} ← Player {self.from_player_id}"
