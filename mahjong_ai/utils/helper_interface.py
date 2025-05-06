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
    """
    Call mahjong-helper with current hand and river state.
    Returns a dict of parsed result.
    """
    input_str = format_tiles_for_helper(hand_tiles)  
    print(input_str)

    exe_path = r"C:\Pywork\Test2\mahjong-helper\mahjong-helper\mahjong-helper.exe"
    print([exe_path, '-agari', input_str])

    try:
        # Use absolute path to avoid file not found error
        result = subprocess.run(
            [exe_path, '-agari', input_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            encoding='utf-8'
        )
        print("[mahjong-helper] stdout:", result.stdout)
        # print("[mahjong-helper] stderr:", result.stderr)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("[mahjong-helper] Error:", e.stderr)
        return ""
    except Exception as e:
        print("[mahjong-helper] Unexpected error:", e)
        return ""

def choose_best_discard_from_output(output: str) -> str:
    for line in output.splitlines():
        if "切" in line:
            try:
                tile = line.split("切")[1].split()[0].strip()
                return tile
            except Exception as e:
                print(f"[choose_best_discard_from_output] Parse error: {line} -> {e}")
                continue
    return ""


