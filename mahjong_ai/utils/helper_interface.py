from mahjong_ai.core.tile import Tile
import subprocess
import json
import os
from collections import defaultdict



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
    
def format_tiles_for_helper(tiles: list[Tile]) -> str:
    grouped = defaultdict(list)
    for tile in tiles:
        s = tile_to_helper_str(tile)
        grouped[s[-1]].append(s[:-1])
    return ''.join(''.join(sorted(grouped[suit])) + suit for suit in 'mpsz' if grouped[suit])


def call_mahjong_helper(hand_tiles: list[Tile], river_tiles: list[Tile] = []) -> str:
    input_str = format_tiles_for_helper(hand_tiles)  
    print(input_str)

    exe_path = r"C:\Pywork\Test2\mahjong-helper\mahjong-helper\mahjong-helper.exe"
    print([exe_path, '-agari', input_str])

    try:
        result = subprocess.run(
            [exe_path, '-agari', input_str],
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
def test_call_mahjong_helper(input_str: str, river_tiles: list[Tile] = []) -> str:

    exe_path = r"C:\Pywork\Test2\mahjong-helper\mahjong-helper\mahjong-helper.exe"
    print([exe_path, '-agari', input_str])

    try:
        result = subprocess.run(
            [exe_path, '-agari', input_str],
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

# def choose_comprehensive_discard_from_output(output_text: str) -> str:
#     """
#     綜合選擇出牌策略：
#     - 如果是聽牌（出現 "聽牌" 或 "和了"）→ 丟第一個出現的切牌
#     - 如果是 “两向听” 或 “一向听” → 用速度最高的
#     - 否則 → 用分數最高的
#     """
#     lines = output_text.splitlines()
    
#     # 🔍 檢查是否為聽牌狀態
#     ##⚙️⚙️⚙️⚙️⚙️⚙️有 bug⚙️⚙️⚙️⚙️⚙️⚙️
#     # for line in lines:
#     #     if "听牌" in line or "和了" in line:
#     #         for l in lines:
#     #             if "切" in l:
#     #                 try:
#     #                     tile_chinese = l.split("切", 1)[1].strip().split()[0]
#     #                     return Tile.from_chinese_string(tile_chinese).to_helper_string()
#     #                 except Exception as e:
#     #                     print("[choose_discard_from_output] 聽牌解析錯誤：", e, "in line:", l)
#     #                     continue
#     #         return ""  # 找不到切牌也回傳空字串
#     # ⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️⚙️
    
#     best_tile = ""
#     best_metric = -float("inf")
#     in_two_shanten_block = False

#     for line in lines:
#         if "两向听" in line or "一向听" in line:
#             in_two_shanten_block = True
#         elif "三向听" in line or "四向听" in line:
#             in_two_shanten_block = False

#         if "切" not in line or "速度" not in line:
#             continue

#         try:
#             tile_match = re.search(r"切\s*(\S+)", line)
#             if not tile_match:
#                 continue
#             tile_chinese = tile_match.group(1).strip()
#             helper_tile = Tile.from_chinese_string(tile_chinese).to_helper_string()

#             if in_two_shanten_block:
#                 print("t")  
#                 speed_match = re.search(r"\[(\d+\.\d+)\s*速度\]", line)
#                 if not speed_match:
#                     continue
#                 metric = float(speed_match.group(1))
#             else:
#                 score_match = re.search(r"\[(\d+\.\d+)\]", line)
#                 if not score_match:
#                     continue
#                 metric = float(score_match.group(1))

#             if metric > best_metric:
#                 best_metric = metric
#                 best_tile = helper_tile

#         except Exception as e:
#             print("[choose_discard_from_output] 解析錯誤：", e, "in line:", line)
#             continue

#     return best_tile
