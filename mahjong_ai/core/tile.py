# mahjong_ai/core/tile.py

class Tile:
    def __init__(self, tile_type: str, tile_value: int):
        """
        tile_type: 'man' (萬子), 'pin' (筒子), 'sou' (索子), 'honor' (字牌)
        tile_value: 1-9 (萬筒索) 或 1-7 (字牌：東南西北白發中)
        """
        self.tile_type = tile_type
        self.tile_value = tile_value

    def __str__(self):
        if self.tile_type == 'man':
            return f"{self.tile_value}萬"
        elif self.tile_type == 'pin':
            return f"{self.tile_value}筒"
        elif self.tile_type == 'sou':
            return f"{self.tile_value}索"
        elif self.tile_type == 'honor':
            honor_names = {
                1: '東', 2: '南', 3: '西', 4: '北', 5: '白', 6: '發', 7: '中'
            }
            return honor_names.get(self.tile_value, '?')
        else:
            return f"未知({self.tile_type}{self.tile_value})"
        
    def to_helper_string(self):
        if self.tile_type == 'man':
            return f"{self.tile_value}m"
        elif self.tile_type == 'pin':
            return f"{self.tile_value}p"
        elif self.tile_type == 'sou':
            return f"{self.tile_value}s"
        elif self.tile_type == 'honor':
            return f"{self.tile_value}z"  # 東=1z，南=2z，... 中=7z
        else:
            return "?"

    def get_tile_description(self) -> str:
        """
        返回這張牌的描述文字，例如 "5man" 或 "2pin"。
        """
        return f"{self.tile_value}{self.tile_type}"

    def is_same_tile(self, other_tile) -> bool:
        """
        判斷兩張牌是否完全相同。
        """
        return self.tile_type == other_tile.tile_type and self.tile_value == other_tile.tile_value

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.tile_type == other.tile_type and self.tile_value == other.tile_value

    def __hash__(self):
        return hash((self.tile_type, self.tile_value))
