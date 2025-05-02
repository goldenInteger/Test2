from __future__ import annotations
from typing import TYPE_CHECKING

from typing import List, Dict
from collections import Counter
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.meld import Meld

if TYPE_CHECKING:
    from mahjong_ai.core.table import Table  # 僅供型別檢查工具使用，不會在執行時引入

# 定義番數表
HAN_TABLE: Dict[str, int] = {
    "門前清榮和": 1,
    "門前清自摸": 1,
    "立直": 1,
    "一發": 1,
    "平和": 1,
    "斷么九": 1,
    "對對和": 2,
    "三暗刻": 2,
    "小三元": 2,
    "混一色": 3,
    "清一色": 6,
    "一氣通貫": 2,
    "三色同順": 2,
    "三色同刻": 2,
    "混全帶么九": 2,
    "純全帶么九": 3,
    "七對子": 2,
    "二盃口": 3,
    "三槓子": 2,
    "雙立直": 2,
    "一盃口": 1,
    "嶺上開花": 1,
    "國士無雙": 13,
    "大三元": 13,
    "字一色": 13,
    "小四喜": 13,
    "大四喜": 13,
    "四暗刻": 13
}

def can_Hepai(hand_tiles: List[Tile], melds: List[Meld]) -> bool:
    """
    判斷手牌（含副露）是否為一個合法的和牌型。
    """
    total_tiles = hand_tiles.copy()
    for meld in melds:
        total_tiles.extend(meld.tiles)

    if len(total_tiles) % 3 != 2:
        return False  # 麻將和牌的基本張數是 3n+2

    return (
        is_kokushi(total_tiles) or
        is_chiitoitsu(total_tiles) or
        is_standard_hand(total_tiles)
    )

def is_kokushi(tiles: List[Tile]) -> bool:
    """
    判斷是否是國士無雙
    """
    required = [
        (1, 'man'), (9, 'man'),
        (1, 'pin'), (9, 'pin'),
        (1, 'sou'), (9, 'sou'),
        (1, 'honor'), (2, 'honor'), (3, 'honor'),
        (4, 'honor'), (5, 'honor'), (6, 'honor'), (7, 'honor')
    ]
    tile_counter = Counter((t.tile_value, t.tile_type) for t in tiles)
    have_all = all(tile in tile_counter for tile in required)
    has_pair = any(count >= 2 for count in tile_counter.values())
    return have_all and has_pair

def is_chiitoitsu(tiles: List[Tile]) -> bool:
    """
    判斷是否是七對子
    """
    if len(tiles) != 14:
        return False
    tile_counter = Counter((t.tile_value, t.tile_type) for t in tiles)
    return all(count == 2 for count in tile_counter.values())

def is_standard_hand(tiles: List[Tile]) -> bool:
    """
    判斷是否是基本的四組一對（標準型）
    """
    counts = Counter((t.tile_value, t.tile_type) for t in tiles)
    return try_standard_hand(counts)

def try_standard_hand(counts: Counter) -> bool:
    """
    嘗試所有可能的對子，再交給 remove_sets() 去剝除剩下的 4 組面子
    """
    for t, count in counts.items():
        if count >= 2:
            new_counts = counts.copy()
            new_counts[t] -= 2  # 當成雀頭
            if remove_sets(new_counts):
                return True
    return False


def remove_sets(counts: Counter) -> bool:
    """
    從牌堆中嘗試遞迴移除所有刻子或順子。
    嘗試所有可能拆法（DFS），若能剝光則回傳 True。
    """
    # Base case：已經沒東西了，代表成功組完
    if sum(counts.values()) == 0:
        return True

    # 對每一種 tile 嘗試
    for tile in sorted(counts):
        if counts[tile] == 0:
            continue

        # 嘗試刻子
        if counts[tile] >= 3:
            new_counts = counts.copy()
            new_counts[tile] -= 3
            if remove_sets(new_counts):
                return True

        # 嘗試順子（僅對萬/筒/索有效）
        val, typ = tile
        if typ in ['man', 'pin', 'sou']:
            next1 = (val + 1, typ)
            next2 = (val + 2, typ)
            if counts.get(next1, 0) > 0 and counts.get(next2, 0) > 0:
                new_counts = counts.copy()
                new_counts[tile] -= 1
                new_counts[next1] -= 1
                new_counts[next2] -= 1
                if remove_sets(new_counts):
                    return True

    return False  # 沒有任何一種拆法成功



def calculate_hand_score(yakus: List[str], is_tsumo: bool, is_dealer: bool) -> Dict:
    """
    根據役種列表，計算總番數與得分。
    回傳 dict 包含 total_han 與分數細節。
    """
    total_han = sum(HAN_TABLE.get(yaku, 0) for yaku in yakus)

    if total_han == 0:
        return {"total_han": 0, "score": 0}

    # ✅ 役滿特殊處理
    if any(yaku in ["國士無雙", "大三元", "字一色", "小四喜", "大四喜", "四暗刻"] for yaku in yakus):
        if is_tsumo:
            if is_dealer:
                return {"total_han": "役滿", "payment_each": 16000}
            else:
                return {"total_han": "役滿", "payment_to_dealer": 16000, "payment_to_others": 8000}
        else:
            return {"total_han": "役滿", "score": 48000 if is_dealer else 32000}

    base_points = (2 ** (total_han + 2)) * 100

    if is_tsumo:
        if is_dealer:
            return {"total_han": total_han, "payment_each": base_points * 2}
        else:
            return {
                "total_han": total_han,
                "payment_to_dealer": base_points * 2,
                "payment_to_others": base_points
            }
    else:
        score = base_points * (6 if is_dealer else 4)
        return {"total_han": total_han, "score": score}

def print_score_result(score_info: Dict, is_tsumo: bool, is_dealer: bool) -> None:
    """
    把得分結果漂亮印出來（終端用）
    """
    if score_info["total_han"] == 0:
        print("不能和牌。")
        return

    if score_info["total_han"] == "役滿":
        print("役滿！")
        if is_tsumo:
            if is_dealer:
                print(f"親家自摸，每家支付 16000 點")
            else:
                print(f"子家自摸：親家支付16000點，其他子家各支付8000點")
        else:
            if is_dealer:
                print(f"親家榮和：得分 48000 點")
            else:
                print(f"子家榮和：得分 32000 點")
        return

    if is_tsumo:
        if is_dealer:
            print(f"親家自摸：每家支付 {score_info['payment_each']} 點")
        else:
            print(f"子家自摸：親支付 {score_info['payment_to_dealer']} 點，其他子家各支付 {score_info['payment_to_others']} 點")
    else:
        print(f"榮和：得分 {score_info['score']} 點")
def show_scores(table: "Table") -> None:
    """
    印出目前四位玩家的分數（含親家標示）
    """
    print("\n==== 本局結束後分數 ====")
    for player in table.players:
        tag = "(親)" if player.player_id == table.dealer_id else ""
        print(f"玩家 {player.player_id}{tag}：{player.points} 點")
    print("==========================\n")

def show_final_result(table: "Table") -> None:
    """
    打完東風場後，印出最終總成績
    """
    print("\n==== 最終總成績 ====")
    ranking = sorted(table.players, key=lambda p: p.points, reverse=True)
    for rank, player in enumerate(ranking, 1):
        tag = "(親)" if player.player_id == table.dealer_id else ""
        print(f"{rank}位：玩家 {player.player_id}{tag} 分數：{player.points} 點")
    print("==========================\n")

def print_ryukyoku_tenpai_status(table: "Table") -> None:
    """
    印出每位玩家在流局時是否聽牌
    """
    print("★ 流局聽牌狀態：")
    for i, player in enumerate(table.players):
        status = "Yes" if table.is_tenpai(player) else "No"
        print(f"玩家 {i}：聽牌 {status}")
