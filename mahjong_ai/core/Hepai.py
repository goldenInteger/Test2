from __future__ import annotations
from typing import TYPE_CHECKING
# ✅ Mahjong 和牌邏輯整合模組（完整包裝）

from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.shanten import Shanten
from mahjong.meld import Meld as MjMeld

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table

from mahjong_ai.core.tile import Tile
from mahjong_ai.core.meld import Meld, MeldType
from mahjong_ai.core.player import Player

# === 和牌流程判定 ===

def can_ron(table: "Table", player: Player, win_tile: Tile) -> bool:
    if player.furiten:
        return False
    return can_declare_win(player.hand.tiles, player.melds, win_tile)

def can_tsumo(player: Player, drawn_tile: Tile) -> bool:
    temp_hand = player.hand.tiles + [drawn_tile]
    return can_declare_win(temp_hand, player.melds, drawn_tile)

def is_tenpai(player: Player) -> bool:
    tiles_34 = convert_tiles_to_34(player.hand.tiles)
    return Shanten().calculate_shanten(tiles_34) == 0

# === 和牌結算（主入口） ===

def settle_win(table: "Table", winner: Player, win_tile: Tile, is_tsumo: bool) -> dict:
    hand_tiles = winner.hand.tiles if is_tsumo else winner.hand.tiles
    is_dealer = winner.player_id == table.round.dealer_id

    result = evaluate_win(
        hand_tiles,
        winner.melds,
        win_tile,
        is_tsumo,
        is_dealer
    )

    if not result["can_win"]:
        return {"error": "無法和牌"}

    # 加總得點（主體分）
    point_gain = result["score"]["main"]
    winner.points += point_gain

    # 場棒與供託
    table.pay_honba_bonus(winner)
    winner.points += table.round.kyotaku
    table.round.kyotaku = 0

    # 扣其他玩家點數（簡化版：非中獎者平均付）
    if is_tsumo:
        payments = result["score"]["additional"]
        for i, p in enumerate(table.players):
            if p != winner:
                p.points -= payments
    else:
        loser = table.players[table.last_discard_player_id]
        payments = result["score"]["main"]
        loser.points -= payments

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
            print(f"🔴 和牌計算錯誤：{result.error}")
        return result.error is None
    except Exception as e:
        print("🔴 例外錯誤：", e)
        return False



def evaluate_win(hand: list[Tile], melds: list[Meld], win_tile: Tile, is_tsumo: bool, is_dealer: bool) -> dict:
    tiles_136 = convert_tiles_to_136(hand)
    win_tile_136 = convert_tile_to_136(win_tile)
    config = HandConfig(
        is_tsumo=is_tsumo,
        is_riichi=False,
        player_wind=0 if is_dealer else 1,
        round_wind=0
    )
    result = HandCalculator().estimate_hand_value(tiles_136, win_tile_136, config=config, melds=convert_melds_to_mahjong(melds))
    if result.error:
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
    man = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'man')
    pin = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'pin')
    sou = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'sou')
    honors = ''.join(str(t.tile_value) for t in tiles if t.tile_type == 'honor')
    return TilesConverter.string_to_136_array(man=man, pin=pin, sou=sou, honors=honors)

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