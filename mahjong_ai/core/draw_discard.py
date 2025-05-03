# mahjong_ai/core/draw_discard.py
from mahjong_ai.core.Hepai import can_tsumo, can_ron, settle_win


def draw_phase(table) -> None:
    """
    處理摸牌階段：
    - 支援副露後跳過摸牌
    - 處理流局
    - 處理自摸和牌
    - 處理嶺上牌摸牌（來自加槓）
    """
    if table.skip_draw:
        table.skip_draw = False
        return

    player = table.players[table.current_turn]

    # 嶺上開花判定（加槓後補牌）
    if table.rinshan_draw:
        tile = player.draw_rinshan_tile(table.wall)
        table.rinshan_draw = False
        print(f"玩家 {player.player_id} 加槓後嶺上摸牌：{tile}")
    else:
        tile = player.draw_tile_from_wall(table.wall)
        print(f"玩家 {player.player_id} 摸牌：{tile}")

    if tile is None:
        print("【流局】牌堆已空！")
        table.round.handle_round_end(-1)
        return

    if can_tsumo(player, tile):
        print(f"玩家 {player.player_id} 【自摸】成功！")
        result = settle_win(table, player, tile, is_tsumo=True)
        print("番數：", result["han"], "符數：", result["fu"], "役種：", result["yaku"])
        print("得分：", result["score"])
        table.round.handle_round_end(player.player_id)
        return


def discard_phase(table, tile) -> None:
    """
    處理打牌階段：
    - 加入河牌
    - 設定 last_discard_player
    - 檢查是否有其他玩家榮胡（含搶槓）
    """
    player = table.players[table.current_turn]
    if not player.discard_tile_from_hand(tile):
        print(f"錯誤：玩家 {player.player_id} 無法打出 {tile}")
        return

    print(f"玩家 {player.player_id} 打出：{tile}")
    table.last_discard_tile = tile
    table.last_discard_player_id = player.player_id

    # 檢查是否有人榮和（含搶槓）
    for i, other in enumerate(table.players):
        if i != player.player_id:
            if can_ron(table, other, tile):
                reason = "搶槓" if table.gang_from == player.player_id else "榮和"
                print(f"玩家 {other.player_id} 【{reason}】成功！")
                result = settle_win(table, other, tile, is_tsumo=False)
                print("番數：", result["han"], "符數：", result["fu"], "役種：", result["yaku"])
                print("得分：", result["score"])
                table.round.handle_round_end(other.player_id)
                return