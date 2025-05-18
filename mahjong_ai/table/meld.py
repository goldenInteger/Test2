# mahjong_ai/core/meld.py
from enum import Enum
from mahjong_ai.table.tile import Tile

class MeldType(Enum):
    CHII = "Chi"            # 吃
    PON = "Pon"             # 碰
    KAN = "Kan"             # 不再使用（改為下列明確分類）
    CHANKAN = "Chankan"     # 搶槓
    NUKI = "Nuki"           # 北抜き（三麻）

    KAKAN = "Kakan"         # 加槓（從碰變成槓）
    ANKAN = "Ankan"         # 暗槓（自己4張）
    DAIMINKAN = "Daiminkan" # 大明槓（對手打出第4張）


class Meld:
    def __init__(self, tiles: list[Tile], meld_type: MeldType, from_player_id: int):
        self.tiles = tiles                          # 副露牌組
        self.meld_type = meld_type                  # MeldType 列舉
        self.from_player_id = from_player_id        # 來源玩家 ID（暗槓用 -1）

    def __str__(self):
        tiles_str = " ".join(str(t) for t in self.tiles)
        return f"[{self.meld_type.name}] {tiles_str} ← Player {self.from_player_id}"

    def to_helper_string(self) -> str:
        """轉為簡化儲存字串格式"""
        return f"{self.meld_type.name}-" + "-".join(t.to_helper_string() for t in self.tiles)

    def is_open(self) -> bool:
        """是否為明副露（吃、碰、明槓）"""
        return self.from_player_id != -1

    def to_dict(self) -> dict:
        """轉為 JSON 可序列化格式（方便 replay 或儲存）"""
        return {
            "type": self.meld_type.name,
            "tiles": [t.to_helper_string() for t in self.tiles],
            "from": self.from_player_id
        }
