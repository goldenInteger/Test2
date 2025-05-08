from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table

from mahjong_ai.core.tile import Tile
from mahjong_ai.core.player import Player
from mahjong_ai.core.Hepai import is_tenpai
from mahjong_ai.core.wall import Wall


def check_tenpai_bonus(players: list[Player]) -> None:
    """
    流局時的聽牌與未聽牌點數加減
    """
    tenpai_players = [p for p in players if is_tenpai(p)]
    noten_players = [p for p in players if not is_tenpai(p)]

    print(f" 聽牌者: {[p.player_id for p in tenpai_players]}")
    print(f" 未聽牌者: {[p.player_id for p in noten_players]}")

    if len(tenpai_players) == 0 or len(noten_players) == 0:
        print(" 無點數移動：全聽或全不聽")
        return
    if len(tenpai_players) == 1:
        transfer = 3000
        penalty = 1000
    if len(tenpai_players) == 2:
        transfer = 1500
        penalty = 1500
    if len(tenpai_players) == 3:
        transfer = 1000
        penalty = 3000

    for p in tenpai_players:
        p.points += transfer
    for p in noten_players:
        p.points -= penalty

def is_kyuushu_kyuuhai(player: Player) -> bool:
    """
    判斷是否九種九牌（起手十三張中有 >=9 種么九）
    """
    # 尚未打牌
    if len(player.river.get_discarded_tiles()) > 0:
        return False
    # 尚未鳴牌
    if len(player.melds) > 0:
        return False

    yaochu_set = set()
    for t in player.hand.tiles:
        if t.is_terminal_or_honor():
            yaochu_set.add((t.tile_type, t.tile_value))
    return len(yaochu_set) >= 9


def is_sufon_renda(players: list[Player]) -> bool:
    """
    判斷是否為四風連打：每人第一張打出的牌皆為風牌
    """
    try:
        first_discards = [
            p.river.get_discarded_tiles()[0].tile
            for p in players
            if len(p.river.get_discarded_tiles()) >= 1
        ]
        if len(first_discards) != 4:
            return False
        # 檢查都是風牌
        if not all(t.is_wind() for t in first_discards):
            return False
        # 檢查是同一張風牌
        first_tile = first_discards[0]
        if not all(t.tile_type == first_tile.tile_type and t.tile_value == first_tile.tile_value for t in first_discards):
            return False
        # 檢查無人鳴牌
        if any(len(p.melds) > 0 for p in players):
            return False
        return True
    except:
        return False

def is_suucha_riichi(players: list[Player]) -> bool:
    """
    四家立直（所有人皆立直）
    """
    return all(p.riichi_declared for p in players)

def is_suukantsu_draw(wall: Wall) -> bool:
    return len(wall.rinshan_wall) == 0  
