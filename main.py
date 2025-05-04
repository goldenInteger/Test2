from mahjong_ai.core.tile import Tile
from mahjong_ai.core.player import Player
from mahjong_ai.core.meld import Meld, MeldType
from mahjong_ai.core import meld_handler


def test_kakan():
    # 建立玩家與加槓對象
    player = Player(player_id=0)
    tile = Tile("man", 3)  # 準備要加槓的牌
    player.furiten = False
    player.riichi_declared = False


    # 其他 3 位假玩家
    dummy1 = Player(player_id=1)
    dummy2 = Player(player_id=2)
    dummy3 = Player(player_id=3)


    # 模擬已經碰了三張三萬（來自 Player 1）
    pon_meld = Meld([tile] * 3, MeldType.PON, from_player_id=1)
    player.melds.append(pon_meld)

    # 手牌補上 10 張其他牌 + 1 張三萬（總共13張手牌）
    player.hand.tiles = [
        Tile("man", 1), Tile("man", 2),
        Tile("man", 4), Tile("man", 5),
        Tile("pin", 1), Tile("pin", 2),
        Tile("sou", 1), Tile("sou", 2),
        Tile("sou", 3), Tile("sou", 4),
        tile  # 第13張為要加槓的 tile
    ]

    # 模擬場面
    class DummyRound:
        def __init__(self):
            self.dealer_id = 0
            self.kyotaku = 0

    class DummyTable:
        def __init__(self):
            self.round = DummyRound()
            self.players = [player]
            self.rinshan_draw = False
            # table.players 必須有 4 位
            self.players = [player, dummy1, dummy2, dummy3]

        def check_rinshan_ron(self, player, tile):
            print(f"玩家 {player.player_id} 執行嶺上開花檢查（模擬中）")
            self.rinshan_draw = True  # 模擬抽到嶺上牌

        def pay_honba_bonus(self, player): pass

    table = DummyTable()
    print("🧪 檢查加槓條件:")
    for meld in player.melds:
        print("副露類型：", meld.meld_type)
        print("副露是否為3張一樣：", [str(t) for t in meld.tiles])
        print("是否為 PON：", meld.meld_type == MeldType.PON)
        print("每張是否都相同：", all(t.is_same_tile(tile) for t in meld.tiles))

    print("手牌：", [str(t) for t in player.hand.tiles])
    print("手牌中是否有加槓目標：", any(t.is_same_tile(tile) for t in player.hand.tiles))

    # 嘗試加槓
    success = meld_handler.try_kakan(table, 0, tile)

    # 驗證結果
    if success:
        print("✅ 加槓成功")
        for meld in player.melds:
            print(f"副露種類: {meld.meld_type}, 牌: {[str(t) for t in meld.tiles]}")
        print(f"是否進行嶺上開花：{table.rinshan_draw}")
    else:
        print("❌ 加槓失敗")


# 執行
if __name__ == "__main__":
    test_kakan()
