import random

from mahjong_ai.core.table import Table
from mahjong_ai.core.draw_discard import draw_phase, discard_phase
from mahjong_ai.core.yaku_checker import detect_yakus
from mahjong_ai.core.scoring import calculate_hand_score, print_score_result
from  mahjong_ai.core.round_manager import deal_initial_hands

def simulate_until_win():
    """
    模擬直到有玩家胡牌（自摸），流局會重新開局直到胡為止。
    """
    table = Table()

    while True:
        if table.wall.is_empty():
            print("\n【流局】牌山打完，重新開始下一局...\n")
            table.round_number += 1
            table.wall = table.wall.__class__()  # 新建牌山
            for player in table.players:
                player.reset()
            deal_initial_hands(table)
            continue

        player = table.players[table.current_turn]
        tile = draw_phase(table)

        if tile:
            print(f"玩家{table.current_turn} 摸到 {tile}")

            if table.can_ron(player, tile):
                print(f"🏆 玩家{table.current_turn} 自摸胡牌！")

                yakus = detect_yakus(
                    player.hand.tiles, player.melds,
                    is_menzen=(len(player.melds) == 0),
                    is_tsumo=True,
                    is_riichi=player.declared_riichi,
                    is_ippatsu=player.ippatsu_possible,
                    is_first_turn=False
                )
                print("達成役種：", yakus)
                score_info = calculate_hand_score(
                    yakus, is_tsumo=True,
                    is_dealer=(table.current_turn == table.dealer_id)
                )
                print_score_result(score_info, is_tsumo=True, is_dealer=(table.current_turn == table.dealer_id))
                table.settle_win(table.current_turn, score_info, is_tsumo=True)
                break

        if player.hand.tiles:
            discard = random.choice(player.hand.tiles)
            discard_phase(table, discard)
            print(f"玩家 {table.last_discard_player_id} 打出 {discard}")
            table.handle_melds_after_discard(discard, table.last_discard_player_id)

    table.show_scores()


if __name__ == "__main__":
    simulate_until_win()
