from mahjong_ai.core.tile import Tile
import subprocess
import json
import os
from collections import defaultdict, Counter
from mahjong_ai.core.player import Player



def tile_to_helper_str(tile: Tile) -> str:
    """
    Convert Tile to mahjong-helper string format.
    e.g. 5m, 1p, E
    """
    if tile.tile_type == 'man':
        return f"{tile.tile_value}m"
    elif tile.tile_type == 'pin':
        return f"{tile.tile_value}p"
    elif tile.tile_type == 'sou':
        return f"{tile.tile_value}s"
    elif tile.tile_type == 'honor':
        return f"{tile.tile_value}z"
    else:
        return '?'  # unknown type
    
def format_tiles_for_helper(tiles: list[Tile], melds: list = None) -> str:
    hand_grouped = defaultdict(list)
    meld_grouped = defaultdict(Counter)

    # 主手牌分組
    for tile in tiles:
        s = tile_to_helper_str(tile)
        if tile.is_aka_dora is True:
            # 赤寶牌改為 0 表示
            s = '0' + s[-1]
        hand_grouped[s[-1]].append(s[:-1])

    # 組合主牌（不合併排序，維持原順序分組）
    base_str = ' '.join(
        ''.join(hand_grouped[suit]) + suit for suit in 'mpsz' if hand_grouped[suit]
    )

    # 副露牌整理
    meld_strs = []
    if melds:
        for meld in melds:
            group = defaultdict(list)
            for tile in meld.tiles:
                s = tile_to_helper_str(tile)
                group[s[-1]].append(s[:-1])
            for suit in group:
                meld_strs.append(''.join(group[suit]) + suit)

    suffix_parts = []
    if meld_strs:
        suffix_parts.append('# ' + ' '.join(meld_strs))

    return f"{base_str} {' '.join(suffix_parts)}" if suffix_parts else base_str


def mingpai_mahjong_helper(hand_tiles: list[Tile], melds: list = None, drawn_tile: Tile = None, river_tiles: list[Tile] = []) -> str:
    input_str = format_tiles_for_helper(hand_tiles, melds)

    # 如果有新摸的牌，加入 + 表示
    if drawn_tile:
        drawn_str = tile_to_helper_str(drawn_tile)
        if drawn_tile.is_aka_dora is True:
            drawn_str = '0' + drawn_str[-1]
        input_str += f" + {drawn_str}"

    print(input_str)
    exe_path = r"C:\Pywork\Test2\mahjong-helper\mahjong-helper\mahjong-helper.exe"

    try:
        result = subprocess.run(
            [exe_path, input_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            encoding='utf-8'
        )
        print("[mahjong-helper] stdout:", result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("[mahjong-helper] Error:", e.stderr)
        return ""
    except Exception as e:
        print("[mahjong-helper] Unexpected error:", e)
        return ""
    


def call_mahjong_helper(hand_tiles: list[Tile], melds: list = None, river_tiles: list[Tile] = []) -> str:
    input_str = format_tiles_for_helper(hand_tiles, melds)
    print(input_str)
    exe_path = r"C:\Pywork\Test2\mahjong-helper\mahjong-helper\mahjong-helper.exe"

    try:
        result = subprocess.run(
            [exe_path, input_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            encoding='utf-8'
        )
        print("[mahjong-helper] stdout:", result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("[mahjong-helper] Error:", e.stderr)
        return ""
    except Exception as e:
        print("[mahjong-helper] Unexpected error:", e)
        return ""
    
def test_call_mahjong_helper(input_str: str, river_tiles: list[Tile] = []) -> str:

    exe_path = r"C:\Pywork\Test2\mahjong-helper\mahjong-helper\mahjong-helper.exe"

    try:
        result = subprocess.run(
            [exe_path, input_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            encoding='utf-8'
        )
        print("[mahjong-helper] stdout:", result.stdout)
        return result.stdout  # ✅ 回傳純 str
    except subprocess.CalledProcessError as e:
        print("[mahjong-helper] Error:", e.stderr)
        return ""
    except Exception as e:
        print("[mahjong-helper] Unexpected error:", e)
        return ""


import re
from mahjong_ai.core.tile import Tile

def choose_best_discard_from_output(output_text: str) -> str:
    """
    從 mahjong-helper 的輸出中選出第一個出現的丟牌。
    """
    lines = output_text.splitlines()
    for line in lines:
        if "切" in line:
            try:
                tile_chinese = re.search(r"切\s*(\S+)", line).group(1)
                return Tile.from_chinese_string(tile_chinese).to_helper_string()
            except Exception as e:
                print("[choose_best_discard_from_output] 解析錯誤：", e, "in line:", line)
                continue
    return ""

import re
from mahjong_ai.core.tile import Tile

def choose_discard_by_points(output_text: str) -> str:
    """
    根據 mahjong-helper 輸出選擇：
    - 最小向聽數的區塊
    - 該區塊中分數最高的切牌
    回傳 helper 格式（如 '5m'、'7z'）
    """
    block_priority = ['听牌', '一向听', '两向听', '三向听', '四向听', '五向听', '六向听', '七向听']
    current_block = None
    best_tile = ""
    best_score = -float("inf")
    found_block = None

    for line in output_text.splitlines():
        line = line.strip()

        # 若有“建议向听倒退”整段略過
        if "建议向听倒退" in line:
            break

        # 決定目前屬於哪一個向聽區段
        for b in block_priority:
            if b in line:
                current_block = b
                break

        # 只保留最優先的區段
        if found_block is not None and current_block != found_block:
            continue
        if found_block is None and current_block in block_priority:
            found_block = current_block

        if "切" not in line:
            continue

        try:
            # 抓 tile 名稱
            tile_match = re.search(r"切\s*(\S+)", line)
            score_match = re.search(r"\[(\d+\.\d+)\]", line)
            if not tile_match or not score_match:
                continue

            tile_chinese = tile_match.group(1).strip()
            score = float(score_match.group(1))

            if score > best_score:
                best_score = score
                best_tile = Tile.from_chinese_string(tile_chinese).to_helper_string()
        except Exception as e:
            print("[choose_discard_by_points] 解析錯誤：", e, "in line:", line)
            continue

    return best_tile

  
def choose_discard_by_speed(output_text: str) -> str:
    """
    根據 mahjong-helper 的輸出，找出速度最高的丟牌。
    """
    best_tile = ""
    best_speed = -float("inf")
    lines = output_text.splitlines()

    for line in lines:
        if "切" not in line or "速度" not in line:
            continue
        try:
            # 取得速度數值
            speed_match = re.search(r"\[(\d+\.\d+)\s*速度\]", line)
            if not speed_match:
                continue
            speed = float(speed_match.group(1))

            # 抓 tile
            tile_chinese = re.search(r"切\s*(\S+)", line).group(1)
            helper_tile = Tile.from_chinese_string(tile_chinese).to_helper_string()

            if speed > best_speed:
                best_speed = speed
                best_tile = helper_tile

        except Exception as e:
            print("[choose_discard_by_speed] 解析錯誤：", e, "in line:", line)
            continue

    return best_tile

import re
from mahjong_ai.core.tile import Tile

def choose_comprehensive_discard_from_output(output_text: str) -> str:
    """
    綜合選擇出牌策略：
    - 如果是聽牌（出現 "聽牌" 或 "和了"）→ 丟第一個出現的切牌
    - 如果是 “两向听” 或 “一向听” → 用速度最高的
    - 否則 → 用分數最高的
    """
    lines = output_text.splitlines()
    
    # 🔍 檢查是否為聽牌狀態
    ##⚙️⚙️⚙️⚙️⚙️⚙️有 bug⚙️⚙️⚙️⚙️⚙️⚙️
    # for line in lines:
    #     if "听牌" in line or "和了" in line:
    #         for l in lines:
    #             if "切" in l:
    #                 try:
    #                     tile_chinese = l.split("切", 1)[1].strip().split()[0]
    #                     return Tile.from_chinese_string(tile_chinese).to_helper_string()
    #                 except Exception as e:
    #                     print("[choose_discard_from_output] 聽牌解析錯誤：", e, "in line:", l)
    #                     continue
    #         return ""  # 找不到切牌也回傳空字串
    # ⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️
    
    best_tile = ""
    best_metric = -float("inf")
    in_two_shanten_block = False

    for line in lines:
        if "两向听" in line or "一向听" in line:
            in_two_shanten_block = True
        elif "三向听" in line or "四向听" in line:
            in_two_shanten_block = False

        if "切" not in line or "速度" not in line:
            continue

        try:
            tile_match = re.search(r"切\s*(\S+)", line)
            if not tile_match:
                continue
            tile_chinese = tile_match.group(1).strip()
            helper_tile = Tile.from_chinese_string(tile_chinese).to_helper_string()

            if in_two_shanten_block:
                print("t")  
                speed_match = re.search(r"\[(\d+\.\d+)\s*速度\]", line)
                if not speed_match:
                    continue
                metric = float(speed_match.group(1))
            else:
                score_match = re.search(r"\[(\d+\.\d+)\]", line)
                if not score_match:
                    continue
                metric = float(score_match.group(1))

            if metric > best_metric:
                best_metric = metric
                best_tile = helper_tile

        except Exception as e:
            print("[choose_discard_from_output] 解析錯誤：", e, "in line:", line)
            continue

    return best_tile
