from mahjong_ai.core.player import Player
from mahjong_ai.core.player import Player
from mahjong_ai.core.tile import Tile
from mahjong_ai.core import Hepai

# 建立測試玩家
player = Player(player_id=0)

# 手牌13張（不含最後一張）
tiles = [
    Tile("man", 1), Tile("man", 2), Tile("man", 3),
    Tile("pin", 1), Tile("pin", 2), Tile("pin", 3),
    Tile("sou", 1), Tile("sou", 2), Tile("sou", 3),
    Tile("sou", 4), Tile("sou", 5), Tile("sou", 6),
    Tile("sou", 6)
]
player.hand.tiles = tiles  # 不要額外加 tile

# 模擬摸牌
drawn_tile = Tile("sou", 6)

# 檢查
print("手牌張數：", len(player.hand.tiles))  # 應該是 13
if Hepai.can_tsumo(player, drawn_tile):
    print("✅ 測試成功：這副牌可以自摸和牌！")
else:
    print("❌ 測試失敗：這副牌無法自摸（應該可以）")
