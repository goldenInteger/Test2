# mahjong_ai/core/river.py

from mahjong_ai.core.tile import Tile

class DiscardedTile:
    def __init__(self, tile: Tile, is_riichi: bool = False, is_called: bool = False):
        """
        表示一張被打出的捨牌，包含額外資訊：
        - tile: 實際的牌
        - is_riichi: 是否為立直後第一張捨牌（通常需畫橫）
        - is_called: 是否已被其他玩家副露（如吃碰槓）
        """
        self.tile = tile
        self.is_riichi = is_riichi
        self.is_called = is_called

    def __str__(self):
        """
        返回字串表示：例如 "5萬*" 表示立直捨牌，"3筒^" 表示已被副露。
        """
        mark = ""
        if self.is_riichi:
            mark += "*"
        if self.is_called:
            mark += "^"
        return f"{str(self.tile)}{mark}"


class River:
    def __init__(self):
        """
        初始化河牌區（捨牌區），用來記錄某位玩家所有被打出的牌。
        每張牌可以帶有特殊狀態（立直、副露）。
        """
        self.discarded_tiles: list[DiscardedTile] = []

    def add_discard(self, tile: Tile, is_riichi: bool = False):
        """
        新增一張捨牌到河牌區。
        - tile: 被打出的牌
        - is_riichi: 若為立直後第一張捨牌，標記為 True
        """
        self.discarded_tiles.append(DiscardedTile(tile, is_riichi=is_riichi))

    def call_tile(self, index: int):
        """
        將指定位置的捨牌標記為已被副露（吃/碰/槓）。
        - index: 被副露的捨牌在列表中的位置
        """
        if 0 <= index < len(self.discarded_tiles):
            self.discarded_tiles[index].is_called = True

    def get_discarded_tiles(self) -> list[DiscardedTile]:
        """
        取得目前所有打出的牌（含狀態）。
        """
        return self.discarded_tiles

    def last_tile(self) -> Tile:
        """
        取得最後一張打出的實體牌（不含狀態資訊）。
        若目前為空則回傳 None。
        """
        if not self.discarded_tiles:
            return None
        return self.discarded_tiles[-1].tile

    def has_tile(self, target_tile: Tile) -> bool:
        """
        檢查是否曾打出過指定的 tile（只比對牌面，不含狀態）。
        """
        return any(dt.tile.is_same_tile(target_tile) for dt in self.discarded_tiles)

    def __str__(self):
        """
        回傳河牌區的完整字串顯示（含立直與副露標記）。
        例如：1萬 9筒* 7索 6萬^
        """
        return ' '.join(str(dt) for dt in self.discarded_tiles)
