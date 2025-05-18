from __future__ import annotations
from typing import TYPE_CHECKING
# mahjong_ai/core/meld_handler.py

# TODO: 

from typing import List, Tuple
from mahjong_ai.table.tile import Tile
from mahjong_ai.table.meld import Meld, MeldType
from mahjong_ai.table.player import Player
from mahjong_ai.table.Hepai import can_ron, can_ron_13

if TYPE_CHECKING:
    from mahjong_ai.table.table import Table

# === 玩家行為詢問介面 ===
def ask_player_action(player: Player, action_type: str, tile: Tile, options: list = None) -> bool | list:
    """
    詢問玩家是否要執行某個行動。
    若 options 存在（如 Chi 有多組可吃），則應返回玩家選擇的組合。
    """
    """"
    if not hasattr(player, 'is_human') or not hasattr(player, 'strategy'):
        return False
    if player.is_human:
        print(f"🟡 玩家 {player.player_id} 可選擇 {action_type} → 自動略過（尚未接 UI）")
        return options[0] if options else False
    else:
        return player.strategy.should_call(action_type, tile, options)
    """
    if (action_type == "pon") :
        return player.pon(tile)
    if (action_type == "chi") :
        return player.chi(tile)
    if (action_type == "daiminkan") :
        return player.kan(tile)
    
    print(action_type)
    if options == None:
        return True
    else:
        return options[0]

# === 副露決策流程（吃碰槓和） ===
def check_others_can_meld(table: Table, discarded_tile: Tile, from_player_id: int) -> List[Tuple[int, str]]:
    """
    檢查這張牌是否有人要吃／碰／槓／榮和，依照優先順序處理
    """
    # 和牌
    for offset in range(1, 4):
        pid = (from_player_id + offset) % 4
        player = table.players[pid]
        # 榮和（搶先）
        if can_ron_13(table, player, discarded_tile):
            if ask_player_action(player, "ron", discarded_tile):

                player.hand.add_tile(discarded_tile)

                #別家利用立直時打出的牌胡牌，立直就不成立，不用支付立直棒
                if table.players[from_player_id].riichi_turn == table.turn:
                    table.players[from_player_id].riichi_turn = -1
                    table.players[from_player_id].is_riichi = False
                    table.players[from_player_id].points += 1000
                    table.round.kyotaku -= 1000

                # 河底撈魚
                if table.wall.is_empty():
                    player.is_houtei = True
                player.win_tile = discarded_tile
                table.winner = player
                table.round_over = True
                return [(player.player_id, "ron")]
            #振聽
            else:
                # 立直振聽
                if player.is_riichi:
                    player.furiten = True
                # 同巡振聽
                player.furiten_temp = table.turn

    # 碰、大明槓（碰與槓同優先）
    for offset in range(1, 4):
        pid = (from_player_id + offset) % 4
        player = table.players[pid]

        if not player.is_riichi and can_daiminkan(player, discarded_tile):
            if ask_player_action(player, "daiminkan", discarded_tile):
                make_daiminkan(table, player, discarded_tile, from_player_id)
                return [(player.player_id, "daiminkan")]

        if not player.is_riichi and can_pon(player, discarded_tile):
            if ask_player_action(player, "pon", discarded_tile):
                make_pon(table, player, discarded_tile, from_player_id)
                return [(player.player_id, "pon")]

    # 吃（只有下家可吃）
    pid = (from_player_id + 1) % 4
    player = table.players[pid]
    chi_sets = can_chi_sets(player, discarded_tile)
    if not player.is_riichi and chi_sets:
        if (ask_player_action(player, "chi", discarded_tile, chi_sets)):
            chosen_set = ask_player_action(player, "chi", discarded_tile, chi_sets)
            if chosen_set:
                make_chi(table, player, discarded_tile, from_player_id, chosen_set)
                return [(player.player_id, "chi")]
    return []

# === 搶槓判定 ===
def try_chankan(table: Table, tile: Tile, from_player_id: int) -> bool:
    for offset in range(1, 4):
        pid = (from_player_id + offset) % 4
        player = table.players[pid]
        if can_ron_13(table, player, tile):
            if ask_player_action(player, "chankan", tile):
                player.hand.add_tile(tile)
                table.winner = player
                table.last_discard_player_id = from_player_id
                player.is_chankan = True
                table.round_over = True
                return True
    return False


# === 可行動檢查 ===
def can_pon(player: Player, tile: Tile) -> bool:
    return sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) >= 2

def can_chi_sets(player: Player, tile: Tile) -> list[list[int]]:
    if tile.tile_type not in ['man', 'pin', 'sou']:
        return []
    n = tile.tile_value
    vals = [t.tile_value for t in player.hand.tiles if t.tile_type == tile.tile_type]
    sets = []
    if n - 2 in vals and n - 1 in vals:
        sets.append([n - 2, n - 1, n])
    if n - 1 in vals and n + 1 in vals:
        sets.append([n - 1, n, n + 1])
    if n + 1 in vals and n + 2 in vals:
        sets.append([n, n + 1, n + 2])
    return sets

def can_kakan(player: Player, tile: Tile) -> bool:
    """
    player 是否可以加槓這張 tile
    """
    for meld in player.melds:
        # 有這張 tile 的碰
        if meld.meld_type == MeldType.PON and meld.tiles[0].is_same_tile(tile):
            if sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) >= 1:
                return True
    return False

def can_ankan(player: Player) -> Tile | None:
    """
    回傳可暗槓的牌（四張相同牌）或 None
    """
    tile_counts = {}
    for tile in player.hand.tiles:
        key = (tile.tile_type, tile.tile_value)
        tile_counts[key] = tile_counts.get(key, 0) + 1
    for (t_type, t_val), count in tile_counts.items():
        if count == 4:
            return Tile(t_type, t_val)
    return None

def can_daiminkan(player: Player, tile: Tile) -> bool:
    """
    判斷是否可以大明槓（手牌中有 3 張來碰外來第 4 張）
    """
    return sum(1 for t in player.hand.tiles if t.is_same_tile(tile)) >= 3

# === 實際鳴牌動作 ===
def make_pon(table: Table, player: Player, tile: Tile, from_player_id: int) -> None:
    to_use = [t for t in player.hand.tiles if t.is_same_tile(tile)][:2]
    for t in to_use:
        player.hand.remove_tile(t)
    meld = Meld([tile] + to_use, MeldType.PON, from_player_id)
    player.melds.append(meld)
    # 換人出牌
    table.current_turn = player.player_id
    # 省略抽牌
    table.skip_draw = True
    if not table.is_mingpai:
        table.is_mingpai = True

def make_chi(table: Table, player: Player, tile: Tile, from_player_id: int, chosen: list[int]) -> None:
    """
    使用指定順子組合 chosen 進行吃牌
    """
    used = []
    for v in chosen:
        if v == tile.tile_value:
            continue
        for t in player.hand.tiles:
            if t.tile_type == tile.tile_type and t.tile_value == v:
                used.append(t)
                break
    for t in used:
        player.hand.remove_tile(t)
    meld = Meld([Tile(tile.tile_type, v) for v in chosen], MeldType.CHII, from_player_id)
    player.melds.append(meld)
    table.current_turn = player.player_id
    table.skip_draw = True
    player.last_chi_meld = meld
    if not table.is_mingpai:
        table.is_mingpai = True

def make_kakan(table: Table, player: Player, tile: Tile) -> None:
    """
    將碰轉為加槓，移除手牌並加入第四張到原 meld
    """
    if try_chankan(table, tile, from_player_id=player.player_id):
        return  # 搶槓成功 → 本人無法加槓
    for meld in player.melds:
        if meld.meld_type == MeldType.PON and meld.tiles[0].is_same_tile(tile):
            player.hand.remove_tile(next(t for t in player.hand.tiles if t.is_same_tile(tile)))
            meld.tiles.append(tile)
            meld.meld_type = MeldType.KAKAN
            table.rinshan_draw = True
            break

def make_ankan(table: Table, player: Player, tile: Tile) -> None:
    """
    暗槓（從手牌移除 4 張、加入副露）
    """
    removed = 0
    for tile_ in list(player.hand.tiles):
        if tile_.is_same_tile(tile):
            player.hand.remove_tile(tile_)
            removed += 1
        if removed == 4:
            break
    meld = Meld([tile] * 4, MeldType.ANKAN, from_player_id=player.player_id)
    player.melds.append(meld)
    table.rinshan_draw = True

def make_daiminkan(table: Table, player: Player, tile: Tile, from_player_id: int) -> None:
    """
    大明槓（從手牌移除三張，加入 1 張來源牌建立槓）
    """
    removed = 0
    for tile_ in list(player.hand.tiles):
        if tile_.is_same_tile(tile):
            player.hand.remove_tile(tile_)
            removed += 1
        if removed == 3:
            break
    meld = Meld([tile] * 4, MeldType.DAIMINKAN, from_player_id=from_player_id)
    player.melds.append(meld)
    table.rinshan_draw = True
    table.current_turn = player.player_id
    table.skip_draw = False
    if not table.is_mingpai:
        table.is_mingpai = True
