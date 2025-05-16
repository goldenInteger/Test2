from mahjong_ai.utils.helper_interface import test_call_mahjong_helper, mingpai_mahjong_helper, pon_mingpai_top_two_lines, chi_mingpai_top_two_lines
from mahjong_ai.utils.helper_interface import choose_best_discard_from_output
from mahjong_ai.core.tile import Tile

# 建立模擬手牌：123m 456p 789s 東南西
hand_tiles = [
    Tile('man', 3), Tile('man', 4), Tile('man', 5),
    Tile('man', 6), Tile('sou', 3), Tile('sou', 4),
    Tile('sou', 5), Tile('sou', 7), Tile('sou', 8),
    Tile('sou', 9), Tile('man', 2), Tile('man', 2), Tile('man', 2)
]
meld_tiles = []
# 4455667m 57p 55668s
# 模擬河牌（目前沒用到分析但可以先放）
river = [
    Tile('man', 7), Tile('pin', 9)
]

# 呼叫 helpe$
text_output = mingpai_mahjong_helper(hand_tiles, meld_tiles, Tile('man', 2))
# best_discard = chi_mingpai_top_two_lines(text_output, Tile('man', 1))
best_discard = pon_mingpai_top_two_lines(text_output)
print(best_discard)
# print(t.tile_type, t.tile_value)

