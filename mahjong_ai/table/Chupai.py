from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/draw_discard.py
from mahjong_ai.table.Mingpai import check_others_can_meld, can_ankan, can_kakan, make_ankan, make_kakan, ask_player_action, try_chankan
from mahjong_ai.table import riichi
from mahjong_ai.table.Hepai import can_tsumo, can_ron, settle_win
from mahjong_ai.table.tile import Tile
from mahjong_ai.table.player import Player
if TYPE_CHECKING:
    from mahjong_ai.table.table import Table


def draw_phase(table: Table, player: Player) -> Tile:
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
    # 同巡振聽取消
    if player.furiten_temp != -1 and table.turn - player.furiten_temp >= 4:
        player.furiten_temp = -1

    # 嶺上開花判定（加槓後補牌）
    if table.rinshan_draw:
        tile = player.draw_rinshan_tile(table.wall)
        if tile == None:
            table.is_liuju = True
            table.round_over = True
            print("\n四槓散了 !")
            return
        #翻寶牌
        Bao_tile = table.wall.draw_dora_indicators()
        table.wall.open_dora_wall.append(Bao_tile)
        print(f"玩家 {player.player_id} 加槓後嶺上摸牌：{tile}")
    else:
        # 摸牌
        tile = player.draw_tile_from_wall(table.wall)
        print(f"玩家 {player.player_id} 摸牌：{tile}")
    # 流局
    if tile is None:
        print("【流局】牌堆已空！")
        table.is_liuju = True
        table.round_over = True
        return
    # 自摸
    if can_tsumo(player, tile):
        if ask_player_action(table, player, "tsumo", tile):
            player.win_tile = tile
            table.winner = player
            player.is_tsumo = True
            table.round_over = True
            # 一發
            if player.is_riichi and table.turn - player.riichi_turn <= 4:
                player.is_ippatsu
            # 海底摸月
            if table.wall.is_empty():
                player.is_haitei = True
            # 嶺上開花
            if table.rinshan_draw:
                player.is_rinshan = True
            return
    
    table.rinshan_draw = False
    # 暗槓
    ankan_tile = can_ankan(player)
    if ankan_tile != None:
        if ask_player_action(table, player, "ankan", ankan_tile):
            make_ankan(table, player, ankan_tile)
            table.skip_discard = True
            table.current_turn = player.player_id
            return
    # 加槓
    if can_kakan(player, tile):
        if not player.is_riichi and ask_player_action(table, player, "kakan", tile):
            if try_chankan(table, tile, from_player_id=player.player_id):
                return  # 搶槓成功 → 本人無法加槓
            make_kakan(table, player, tile)
            table.skip_discard = True
            table.current_turn = player.player_id
            return
    
    return tile

    


def discard_phase(table: Table, tile: Tile) -> None:
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
    table.last_discard_player_id = player.player_id

    check_others_can_meld(table, tile, player.player_id)