from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/meld_handler.py

from typing import List, Tuple
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.meld import Meld, MeldType
from mahjong_ai.core.player import Player
from mahjong_ai.core.scoring import can_Hepai, calculate_hand_score, print_score_result
from mahjong_ai.core.yaku_checker import detect_yakus

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table  # 僅供型別檢查工具使用，不會在執行時引入

def can_kakan(player: Player, tile: Tile) -> bool:
    # ✅ 必須已經碰過這張牌，且手上還有1張一樣的
    for meld in player.melds:
        if meld.meld_type == MeldType.PON and meld.tiles[0].is_same_tile(tile):
            if sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) >= 1:
                return True
    return False

def can_pon(player: Player, tile: Tile) -> bool:
    # 判斷玩家是否可以碰（手牌裡至少有兩張一樣）
    return sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) >= 2

def can_chi(player: Player, tile: Tile) -> bool:
    # 判斷玩家是否可以吃（只有下家能吃，且要順子）
    if tile.tile_type not in ['man', 'pin', 'sou']:
        return False
    nums = [t.tile_value for t in player.hand.tiles if t.tile_type == tile.tile_type]
    n = tile.tile_value
    return ((n - 2 in nums and n - 1 in nums) or
            (n - 1 in nums and n + 1 in nums) or
            (n + 1 in nums and n + 2 in nums))

def check_others_can_meld(table: Table, discarded_tile: Tile, from_player_id: int) -> List[Tuple[int, str]]:
    # 檢查其他玩家是否可以吃或碰這張打出的牌。
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
    # 打出牌後處理吃碰行為
    actions = check_others_can_meld(table, discarded_tile, from_player_id)

    for pid, action in actions:
        if action == 'PON':
            print(f"玩家 {pid} 進行了【碰】 {discarded_tile}")
            make_pon(table, table.players[pid], discarded_tile, from_player_id)
            table.current_turn = pid
            table.skip_draw = True
            for p in table.players:
                if p.declared_riichi:
                    p.ippatsu_possible = False
            return True

    for pid, action in actions:
        if action == 'CHI':
            print(f"玩家 {pid} 進行了【吃】 {discarded_tile}")
            make_chi(table, table.players[pid], discarded_tile, from_player_id)
            table.current_turn = pid
            table.skip_draw = True
            for p in table.players:
                if p.declared_riichi:
                    p.ippatsu_possible = False
            return True

    return False

def make_pon(table: Table, player: Player, tile: Tile, from_player_id: int) -> None:
    # 讓玩家完成一個碰
    to_use = [t for t in player.hand.tiles if t.is_same_tile(tile)][:2]
    for t in to_use:
        player.hand.remove_tile(t)
    meld = Meld([tile] + to_use, MeldType.PON, from_player_id)
    player.melds.append(meld)

def make_chi(table: Table, player: Player, tile: Tile, from_player_id: int) -> None:
    # 讓玩家完成一個吃
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
    # 嘗試加槓，並檢查是否有人搶槓。
    print(f"玩家 {player_id} 嘗試加槓 {tile}")

    for i in range(1, 4):
        oid = (player_id + i) % 4
        opp = table.players[oid]
        test = opp.hand.tiles.copy() + [tile]
        if can_Hepai(test, opp.melds):
            yakus = detect_yakus(
                test, opp.melds,
                is_menzen=len(opp.melds)==0,
                is_tsumo=False, is_riichi=False,
                is_ippatsu=False, is_first_turn=False
            )
            if yakus:
                print(f" 搶槓成功！玩家 {oid} 搶槓胡牌！")
                score = calculate_hand_score(yakus, False, oid==0)
                print_score_result(score, False, oid==0)
                table.round_manager.end_round(oid)
                return True

    print(f" 沒有人能搶槓，玩家 {player_id} 成功加槓！")
    rinshan_tile = draw_rinshan_tile(table)
    print(f"玩家 {player_id} 嶺上摸到了 {rinshan_tile}")
    player = table.players[player_id]
    player.hand.add_tile(rinshan_tile)

    if can_Hepai(player.hand.tiles, player.melds):
        yakus = detect_yakus(
            player.hand.tiles, player.melds,
            is_menzen=(len(player.melds) == 0),
            is_tsumo=True, is_riichi=False,
            is_ippatsu=False, is_first_turn=False
        )
        if yakus:
            yakus.append("嶺上開花")
            print(" 玩家加槓後嶺上開花自摸成功！達成役種：", yakus)
            score = calculate_hand_score(yakus, True, player_id == 0)
            print_score_result(score, True, player_id == 0)
            table.round_manager.end_round(player_id)
            return True

    print(f"玩家 {player_id} 嶺上摸牌後無法自摸，請出牌。")
    return False

def draw_rinshan_tile(table: Table) -> Tile:
    # 從嶺上摸一張牌（槓補牌）
    return table.wall.tiles.pop() if table.wall.tiles else None
