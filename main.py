from mahjong_ai.core.tile import Tile
from mahjong_ai.core.player import Player
from mahjong_ai.core.meld import Meld
from mahjong_ai.core.Hepai import evaluate_win

def test_win_hand(label: str, hand_tiles: list[Tile], win_tile: Tile, is_tsumo=True, is_dealer=False):
    print(f"\n🀄 測試牌型：{label}")
    player = Player(player_id=0)
    player.hand.tiles = hand_tiles
    result = evaluate_win(
        hand=player.hand.tiles + [win_tile],
        melds=[],
        win_tile=win_tile,
        is_tsumo=is_tsumo,
        is_dealer=is_dealer
    )
    if not result["can_win"]:
        print("❌ 無法和牌")
        print("役種：", ", ".join(result["yaku"]))
        print("得分：", result["score"])
    else:
        print(f"✅ 可和牌！番數：{result['han']}，符數：{result['fu']}")
        print("役種：", ", ".join(result["yaku"]))
        print("得分：", result["score"])

def test_all_win_cases():
    test_win_hand("清一色", [Tile("man", 1), Tile("man", 1),
                            Tile("man", 2), Tile("man", 2),
                            Tile("man", 3), Tile("man", 3),
                            Tile("man", 4), Tile("man", 4),
                            Tile("man", 5), Tile("man", 5),
                            Tile("man", 6), Tile("man", 6),
                            Tile("man", 7)], Tile("man", 7))

if __name__ == "__main__":
    test_all_win_cases()
