# mahjong_ai/core/tile.py

class Tile:
    def __init__(self, tile_type: str, tile_value: int, is_aka_dora: bool = False):
        """
        建立一張麻將牌。
        - tile_type: 'man' (萬子), 'pin' (筒子), 'sou' (索子), 'honor' (字牌)
        - tile_value: 1-9 (萬筒索) 或 1-7 (字牌：東南西北白發中)
        """
        self.tile_type = tile_type
        self.tile_value = tile_value
        self.is_aka_dora = is_aka_dora

    def __str__(self):
        """
        以中文格式輸出，例如 "1萬"、"9筒"、"白"
        """
        if self.tile_type == 'man':
            if self.is_aka_dora:
                return f"紅{self.tile_value}萬"
            return f"{self.tile_value}萬"
        elif self.tile_type == 'pin':
            if self.is_aka_dora:
                return f"紅{self.tile_value}筒"
            return f"{self.tile_value}筒"
        elif self.tile_type == 'sou':
            if self.is_aka_dora:
                return f"紅{self.tile_value}索"
            return f"{self.tile_value}索"
        elif self.tile_type == 'honor':
            honor_names = {
                1: '東', 2: '南', 3: '西', 4: '北', 5: '白', 6: '發', 7: '中'
            }
            return honor_names.get(self.tile_value, '?')
        else:
            return f"未知({self.tile_type}{self.tile_value})"

    def to_helper_string(self):
        """
        轉換為簡易表示法，例如 "1m", "5p", "7z"（z=字牌）
        """
        if self.tile_type == 'man':
            return f"{self.tile_value}m"
        elif self.tile_type == 'pin':
            return f"{self.tile_value}p"
        elif self.tile_type == 'sou':
            return f"{self.tile_value}s"
        elif self.tile_type == 'honor':
            return f"{self.tile_value}z"
        else:
            return "?"

    def get_tile_description(self) -> str:
        """
        取得詳細描述，例如 "5man", "2honor"
        """
        return f"{self.tile_value}{self.tile_type}"

    def is_same_tile(self, other_tile: "Tile") -> bool:
        """
        判斷兩張牌是否牌面相同（不考慮是哪一張複本）
        """
        return self.tile_type == other_tile.tile_type and self.tile_value == other_tile.tile_value
    
    def is_wind(self) -> bool:
        """判斷是否為東南西北風牌"""
        return self.tile_type == "z" and self.tile_value in [1, 2, 3, 4]  # 1=東, 2=南, 3=西, 4=北

    def is_terminal_or_honor(self) -> bool:
        """判斷是否為么九牌（1, 9, 字牌）"""
        return (self.tile_type in ["m", "p", "s"] and self.tile_value in [1, 9]) or self.tile_type == "z"

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.tile_type == other.tile_type and self.tile_value == other.tile_value

    def __hash__(self):
        return hash((self.tile_type, self.tile_value))

    # -------------------------
    # mahjong 套件整合功能區塊
    # -------------------------

    def to_34_id(self) -> int:
        """
        將此 tile 轉換為 mahjong 套件使用的 0–33 格式。
        """
        if self.tile_type == 'man':
            return self.tile_value - 1
        elif self.tile_type == 'pin':
            return 9 + self.tile_value - 1
        elif self.tile_type == 'sou':
            return 18 + self.tile_value - 1
        elif self.tile_type == 'honor':
            return 27 + self.tile_value - 1
        raise ValueError("Unknown tile type")

    @classmethod
    def from_34_id(cls, tile_id: int):
        """
        從 0–33 格式反推成 Tile。
        """
        if tile_id < 9:
            return cls('man', tile_id + 1)
        elif tile_id < 18:
            return cls('pin', tile_id - 9 + 1)
        elif tile_id < 27:
            return cls('sou', tile_id - 18 + 1)
        elif tile_id < 34:
            return cls('honor', tile_id - 27 + 1)
        raise ValueError("Invalid tile_id")

    def get_all_136_ids(self) -> list[int]:
        """
        回傳此牌對應的 136 編號（每種 tile 有 4 張，編號連續）
        例如 5m → [16, 17, 18, 19]
        """
        base = self.to_34_id() * 4
        return [base + i for i in range(4)]

    @classmethod
    def from_helper_string(cls, s: str):
        """
        從 helper 格式（如 '7z', '3p'）建立 Tile。
        """
        if len(s) != 2:
            raise ValueError("Invalid helper string")
        value, suit = int(s[0]), s[1]
        if suit == 'm':
            return cls('man', value)
        elif suit == 'p':
            return cls('pin', value)
        elif suit == 's':
            return cls('sou', value)
        elif suit == 'z':
            return cls('honor', value)
        raise ValueError("Invalid suit")
