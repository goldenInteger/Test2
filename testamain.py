from mahjong_ai.utils.helper_interface import test_call_mahjong_helper
from mahjong_ai.utils.helper_interface import choose_comprehensive_discard_from_output
from mahjong_ai.core.tile import Tile

# 建立模擬手牌：123m 456p 789s 東南西
hand_tiles = [
    Tile('man', 1), Tile('man', 2), Tile('man', 3),
    Tile('pin', 4), Tile('pin', 5), Tile('pin', 6),
    Tile('sou', 7), Tile('sou', 8), Tile('sou', 9),
    Tile('honor', 1), Tile('honor', 2), Tile('honor', 3),
    Tile('man', 5), Tile('honor', 1)
]
# 4455667m 57p 55668s
# 模擬河牌（目前沒用到分析但可以先放）
river = [
    Tile('man', 7), Tile('pin', 9)
]

# 呼叫 helper
text_output = test_call_mahjong_helper("4455667m57p55668s")
best_discard = choose_comprehensive_discard_from_output(text_output)
print(best_discard)
# print(t.tile_type, t.tile_value)

