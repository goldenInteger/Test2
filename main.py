import sys
import os
sys.path.append(os.path.abspath("."))  # 確保 mahjong_ai 可以被匯入
from mahjong_ai.core.player import Player
from mahjong_ai.core.table import Table
from mahjong_ai.utils.helper_interface import call_mahjong_helper, choose_best_discard_from_output
from mahjong_ai.core.tile import Tile


def run_full_game():
    table = Table()

    while not table.round.is_game_end():
        table.step()
    # for i in range(10):
    #     table.step()

    print("\n--- 所有玩家手牌 ---")
    
    


if __name__ == "__main__":
    run_full_game()
