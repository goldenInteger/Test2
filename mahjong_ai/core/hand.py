# mahjong_ai/core/hand.py

from mahjong_ai.core.tile import Tile

class Hand:
    def __init__(self):
        """
        初始化一個空手牌列表。
        """
        self.tiles: list[Tile] = []

    def add_tile(self, tile: Tile) -> None:
        """
        把一張牌加入手牌中，並自動排序。
        一般在摸牌或起始牌時使用。
        """
        self.tiles.append(tile)
        self.sort_hand()

    def remove_tile(self, tile: Tile) -> bool:
        """
        移除一張手牌中與指定 tile 相同的牌（僅移除一張）
        回傳 True 表示成功移除，False 表示未找到。
        """
        for existing_tile in self.tiles:
            if existing_tile.is_same_tile(tile) and existing_tile.is_aka_dora == tile.is_aka_dora:
                self.tiles.remove(existing_tile)
                return True
        return False

    def sort_hand(self) -> None:
        """
        將手牌依照花色與數值排序：
        萬 < 筒 < 索 < 字，數字升冪
        """
        def tile_sort_key(tile: Tile):
            type_order = {'man': 0, 'pin': 1, 'sou': 2, 'honor': 3}
            return (type_order.get(tile.tile_type, 4), tile.tile_value)
        
        self.tiles.sort(key=tile_sort_key)

    def to_helper_list(self) -> list[str]:
        """
        轉換整副手牌為簡易字串格式列表，例如：['1m', '2m', '9z']
        """
        return [tile.to_helper_string() for tile in self.tiles]

    def to_counts_34(self) -> list[int]:
        """
        轉換成 mahjong 套件需要的 34 張 tile 數量列表。
        例如：[2, 1, 0, ..., 0] 表示有兩張 1m，一張 2m，其餘為 0。
        """
        counts = [0] * 34
        for tile in self.tiles:
            counts[tile.to_34_id()] += 1
        return counts

    def __str__(self):
        """
        以簡易格式輸出手牌，例如：'1m 1m 2m 3p 4z'
        """
        return ' '.join(self.to_helper_list())

    def get_tile_objects(self) -> list[Tile]:
        """
        取得實際的 Tile 物件列表（通常用於進一步邏輯分析）。
        """
        return self.tiles.copy()
