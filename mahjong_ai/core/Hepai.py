from __future__ import annotations
from typing import TYPE_CHECKING
# Mahjong 和牌邏輯整合模組（完整包裝）

# TODO : 解決例外錯誤： negative shift count
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.shanten import Shanten
from mahjong.meld import Meld as MjMeld

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table

from mahjong_ai.core.tile import Tile
from mahjong_ai.core.meld import Meld, MeldType
from mahjong_ai.core.hand import Hand
from mahjong_ai.core.player import Player

# === 和牌流程判定 ===

# 手牌已有14張
def can_ron(table: "Table", player: Player, win_tile: Tile) -> bool:
    if player.furiten:
        return False
    return can_declare_win(player.hand.tiles, player.melds, win_tile)
# 手牌有13張
def can_ron_13(table: "Table", player: Player, win_tile: Tile) -> bool:
    if player.furiten:
        return False
    temp_tiles = player.hand.tiles + [win_tile]
    return can_declare_win(temp_tiles, player.melds, win_tile)
# 手牌已有14張
def can_tsumo(player: Player, drawn_tile: Tile) -> bool:
    return can_declare_win(player.hand.tiles, player.melds, drawn_tile)
# 手牌有13張
def is_tenpai(tiles: list[Tile]) -> bool:
    tiles_34 = convert_tiles_to_34(tiles)
    return Shanten().calculate_shanten(tiles_34) == 0


# === 和牌結算（主入口） ===

def settle_win(table: "Table") -> dict:

    result = evaluate_win(table)

    if not result["can_win"]:
        return {"error": "無法和牌"}

    # 加總得點（主體分）
    point_gain = result["score"]["main"]
    table.winner.points += point_gain

    # 場棒與供託
    table.round.pay_honba_bonus(table.winner)
    table.winner.points += table.round.kyotaku
    table.round.kyotaku = 0

    # 分數計算
    if table.winner.is_tsumo:
        # 自摸情況
        cost = result["score"]
        for p in table.players:
            if p == table.winner:
                continue
            if p.is_dealer:
                p.points -= cost["dealer"]  # 莊家付較多
            else:
                p.points -= cost["non_dealer"]  # 子家付較少
    else:
        # 榮和（放銃）
        loser: Player = table.players[table.last_discard_player_id]
        cost = result["score"]
        loser.points -= cost["main"]  # 放銃者付全部
        bonus = table.round.honba * 300
        loser.points -= bonus

    return result

# === 和牌核心分析 ===

def can_declare_win(hand: list[Tile], melds: list[Meld], win_tile: Tile) -> bool:
    try:
        tiles_136 = convert_tiles_to_136(hand)
        win_tile_136 = convert_tile_to_136(win_tile)
        result = HandCalculator().estimate_hand_value(
            tiles_136, win_tile_136,
            config=HandConfig(),
            melds=convert_melds_to_mahjong(melds)
        )
        if result.error:
            print(f" 和牌計算錯誤：{result.error}")
        return result.error is None
    except Exception as e:
        print(" 例外錯誤：", e)
        return False

def evaluate_win(table: Table) -> dict:
    winner = table.winner
    tiles_136 = convert_tiles_to_136(winner.hand.tiles)
    win_tile_136 = convert_tile_to_136(winner.win_tile)
    dora_tiles = table.wall.open_dora_wall + table.wall.uradora_wall
    dora_tiles_136 = convert_tiles_to_136(dora_tiles)

    config = HandConfig(
        is_tsumo = winner.is_tsumo,
        is_riichi = winner.is_riichi,
        player_wind = winner.seat_wind,
        round_wind = winner.round_wind,
        is_chankan = winner.is_chankan,
        is_daburu_riichi = winner.is_daburu_riichi,
        is_chiihou = winner.is_chiihou,
        is_haitei = winner.is_haitei,
        is_houtei = winner.is_houtei,
        is_ippatsu = winner.is_ippatsu,
        is_nagashi_mangan = winner.is_nagashi_mangan,
        is_renhou = winner.is_renhou,
        is_rinshan = winner.is_rinshan,
        is_tenhou = winner.is_tenhou,
    )
    result = HandCalculator().estimate_hand_value(
        tiles_136, win_tile_136,
        dora_indicators=dora_tiles_136,
        config=config,
        melds = convert_melds_to_mahjong(winner.melds)
    )

    if result.error:
        print(f" 和牌計算錯誤：{result.error}")
        return {"can_win": False, "han": 0, "fu": 0, "yaku": [], "score": {}}
    return {
        "can_win": True,
        "han": result.han,
        "fu": result.fu,
        "yaku": [y.name for y in result.yaku],
        "score": result.cost
    }

# === Tile / Meld 資料轉換 ===

def convert_tiles_to_136(tiles: list[Tile]) -> list[int]:
    """
    將 Tile 物件轉為支援赤寶牌的 string_to_136_array 格式（r 或 0 表示紅5）
    """
    def encode_tile(t: Tile) -> str:
        if t.tile_value == 5 and t.is_aka_dora:
            return 'r'
        return str(t.tile_value)

    man = ''.join(encode_tile(t) for t in tiles if t.tile_type == 'man')
    pin = ''.join(encode_tile(t) for t in tiles if t.tile_type == 'pin')
    sou = ''.join(encode_tile(t) for t in tiles if t.tile_type == 'sou')
    honors = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'honor')

    return TilesConverter.string_to_136_array(
        man=man, pin=pin, sou=sou, honors=honors, has_aka_dora=True
    )


def convert_tiles_to_34(tiles: list[Tile]) -> list[int]:
    man = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'man')
    pin = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'pin')
    sou = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'sou')
    honors = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'honor')
    return TilesConverter.string_to_34_array(man=man, pin=pin, sou=sou, honors=honors)

def convert_tile_to_136(tile: Tile) -> int:
    return convert_tiles_to_136([tile])[0]

MELD_TYPE_MAP = {
    "CHII": MjMeld.CHI,
    "PON": MjMeld.PON,
    "KAN": MjMeld.KAN,
    "CHANKAN": MjMeld.CHANKAN,
    "NUKI": MjMeld.NUKI,
}

def convert_melds_to_mahjong(melds: list[Meld]) -> list[MjMeld]:
    converted = []
    for m in melds:
        tile_136 = convert_tiles_to_136(m.tiles)
        meld_type = MELD_TYPE_MAP.get(m.meld_type.name, MjMeld.PON)
        converted.append(MjMeld(meld_type=meld_type, tiles=tile_136, opened=True))
    return converted

# === 特殊役牌資訊 ===
# 一發(立直後一巡內和牌)
def can_ippatsu(table: Table):
    player = table.winner
    if player.is_riichi and table.turn - player.riichi_turn <= 4:
        player.is_ippatsu = True
# 天和
def can_tenhou(table: Table):
    player = table.winner
    if table.turn == 1 and player.is_tsumo:
        player.is_tenhou = True
# 人和
def can_renhou(table: Table):
    player = table.winner
    if table.turn <= player.player_id and not table.is_mingpai:
        player.is_renhou = True
# 地和
def can_chiihou(table: Table):
    player = table.winner
    if table.turn == player.player_id + 1 and player.is_tsumo:
        player.is_chiihou = True

def can_nagashi_mangan(table: Table) -> Player:
    """
    判斷是否成立流局滿貫（Nagashi Mangan）：
    - 所有丟出的牌皆為么九牌
    - 且未被其他人副露（吃、碰、槓）
    """
    for player in table.players:
        player_id = player.player_id
        valid = True

        # 1. 檢查所有丟出的牌是否為么九
        for river_tile in player.river.discarded_tiles:
            if not river_tile.tile.is_terminal_or_honor():
                valid = False
                break

        if not valid:
            continue  # 跳到下一位玩家

        # 2. 檢查是否有其他人副露他的牌
        for p in table.players:
            if p.player_id == player_id:
                continue
            for meld in p.melds:
                if meld.from_player_id == player_id:
                    valid = False
                    break
            if not valid:
                break

        if valid:
            player.is_nagashi_mangan = True
            return player
    return None