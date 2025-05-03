from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/meld_handler.py

from typing import List, Tuple
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.meld import Meld, MeldType
from mahjong_ai.core.player import Player
from mahjong_ai.core.Hepai import can_ron, settle_win

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table

def can_kakan(player: Player, tile: Tile) -> bool:
    for meld in player.melds:
        if meld.meld_type == MeldType.PON and meld.tiles[0].is_same_tile(tile):
            if sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) >= 1:
                return True
    return False

def can_pon(player: Player, tile: Tile) -> bool:
    return sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) >= 2

def can_chi(player: Player, tile: Tile) -> bool:
    if tile.tile_type not in ['man', 'pin', 'sou']:
        return False
    nums = [t.tile_value for t in player.hand.tiles if t.tile_type == tile.tile_type]
    n = tile.tile_value
    return ((n - 2 in nums and n - 1 in nums) or
            (n - 1 in nums and n + 1 in nums) or
            (n + 1 in nums and n + 2 in nums))

def check_others_can_meld(table: Table, discarded_tile: Tile, from_player_id: int) -> List[Tuple[int, str]]:
    possible_actions = []
    for offset in range(1, 4):
        pid = (from_player_id + offset) % 4
        player = table.players[pid]
        if can_pon(player, discarded_tile):
            possible_actions.append((pid, 'PON'))
        if offset == 1 and can_chi(player, discarded_tile):
            possible_actions.append((pid, 'CHI'))
    return possible_actions

def handle_melds_after_discard(table: Table, discarded_tile: Tile, from_player_id: int) -> bool:
    actions = check_others_can_meld(table, discarded_tile, from_player_id)
    for pid, action in actions:
        if action == 'PON':
            print(f"玩家 {pid} 進行了【碰】 {discarded_tile}")
            make_pon(table, table.players[pid], discarded_tile, from_player_id)
            table.current_turn = pid
            table.skip_draw = True
            return True
    for pid, action in actions:
        if action == 'CHI':
            print(f"玩家 {pid} 進行了【吃】 {discarded_tile}")
            make_chi(table, table.players[pid], discarded_tile, from_player_id)
            table.current_turn = pid
            table.skip_draw = True
            return True
    return False

def make_pon(table: Table, player: Player, tile: Tile, from_player_id: int) -> None:
    to_use = [t for t in player.hand.tiles if t.is_same_tile(tile)][:2]
    for t in to_use:
        player.hand.remove_tile(t)
    meld = Meld([tile] + to_use, MeldType.PON, from_player_id)
    player.melds.append(meld)

def make_chi(table: Table, player: Player, tile: Tile, from_player_id: int) -> None:
    if tile.tile_type not in ['man', 'pin', 'sou']:
        return
    n = tile.tile_value
    vals = [t.tile_value for t in player.hand.tiles if t.tile_type == tile.tile_type]
    sets = []
    if n - 2 in vals and n - 1 in vals:
        sets.append([n-2, n-1, n])
    if n - 1 in vals and n + 1 in vals:
        sets.append([n-1, n, n+1])
    if n + 1 in vals and n + 2 in vals:
        sets.append([n, n+1, n+2])
    if not sets:
        return
    chosen = sets[0]
    used = []
    for v in chosen:
        if v == n: continue
        for t in player.hand.tiles:
            if t.tile_type == tile.tile_type and t.tile_value == v:
                used.append(t)
                break
    for t in used:
        player.hand.remove_tile(t)
    meld = Meld([Tile(tile.tile_type, v) for v in chosen], MeldType.CHI, from_player_id)
    player.melds.append(meld)

def try_kakan(table: Table, player_id: int, tile: Tile) -> bool:
    player = table.players[player_id]
    if not can_kakan(player, tile):
        return False

    print(f"玩家 {player_id} 嘗試加槓 {tile}")
    table.gang_from = player_id  # 用於搶槓判定

    for i in range(1, 4):
        oid = (player_id + i) % 4
        opp = table.players[oid]
        if can_ron(table, opp, tile):
            print(f"玩家 {oid} 【搶槓】成功！")
            result = settle_win(table, opp, tile, is_tsumo=False)
            print("番數：", result["han"], "符數：", result["fu"], "役種：", result["yaku"])
            print("得分：", result["score"])
            table.round.handle_round_end(opp.player_id)
            return True

    print(f"玩家 {player_id} 成功加槓！進行嶺上摸牌。")
    table.rinshan_draw = True
    return False
