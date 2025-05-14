from mahjong_ai.utils.helper_interface import test_call_mahjong_helper, mingpai_mahjong_helper
from mahjong_ai.utils.helper_interface import choose_best_discard_from_output
from mahjong_ai.core.tile import Tile

# 建立模擬手牌：123m 456p 789s 東南西
hand_tiles = [
    Tile('man', 5), Tile('man', 2), Tile('man', 3),
    Tile('pin', 4), Tile('pin', 5), Tile('pin', 6),
    Tile('sou', 7), Tile('sou', 8), Tile('sou', 9),
    Tile('honor', 2), Tile('honor', 2), Tile('honor', 2),
    Tile('man', 5)
]
meld_tiles = []
# 4455667m 57p 55668s
# 模擬河牌（目前沒用到分析但可以先放）
river = [
    Tile('man', 7), Tile('pin', 9)
]

# 呼叫 helper
text_output = mingpai_mahjong_helper(hand_tiles, meld_tiles, Tile('man', 1))
best_discard = choose_best_discard_from_output(text_output)
print(best_discard)
# print(t.tile_type, t.tile_value)

