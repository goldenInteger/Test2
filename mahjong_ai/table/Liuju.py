from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mahjong_ai.table.table import Table

from mahjong_ai.table.tile import Tile
from mahjong_ai.table.player import Player
from mahjong_ai.table.Hepai import is_tenpai
from mahjong_ai.table.wall import Wall


def check_tenpai_bonus(players: list[Player]) -> list[int]:
    """
    流局時的聽牌與未聽牌點數加減，並回傳聽牌者的 player_id。
    """
    tenpai_players = [p for p in players if is_tenpai(p.hand.tiles)]
    noten_players = [p for p in players if not is_tenpai(p.hand.tiles)]

    print(f" 聽牌者: {[p.player_id for p in tenpai_players]}")
    print(f" 未聽牌者: {[p.player_id for p in noten_players]}")

    if len(tenpai_players) == 0 or len(noten_players) == 0:
        print(" 無點數移動：全聽或全不聽")
        return [p.player_id for p in tenpai_players]

    if len(tenpai_players) == 1:
        transfer = 3000
        penalty = 1000
    elif len(tenpai_players) == 2:
        transfer = 1500
        penalty = 1500
    elif len(tenpai_players) == 3:
        transfer = 1000
        penalty = 3000
    else:
        # Just in case more than 3 (should not happen in 4-player mahjong)
        transfer = 0
        penalty = 0

    for p in tenpai_players:
        p.points += transfer
    for p in noten_players:
        p.points -= penalty

    return [p.player_id for p in tenpai_players]


def is_kyuushu_kyuuhai(player: Player) -> bool:
    """
    判斷是否九種九牌（起手十三張中有 >=9 種么九）
    """
    count = 0
    for t in player.hand.tiles:
        if t.is_terminal_or_honor():
            count += 1
    return count >= 9


def is_sufon_renda(players: list[Player]) -> bool:
    """
    判斷是否為四風連打：每人第一張打出的牌皆為風牌
    """
    first_discards = [p.river.get_discarded_tiles()[0].tile for p in players]
    if len(first_discards) != 4:
        return False
    # 檢查都是風牌
    for t in first_discards:
        if not t.is_wind():
            return False
    # 檢查是同一張風牌
    first_tile = first_discards[0]
    for t in first_discards:
        if t.tile_type != first_tile.tile_type or t.tile_value != first_tile.tile_value:
            return False
    return True

def is_suucha_riichi(players: list[Player]) -> bool:
    """
    四家立直（所有人皆立直）
    """
    return all(p.is_riichi for p in players)

def is_suukantsu_draw(wall: Wall) -> bool:
    return len(wall.rinshan_wall) == 0  
