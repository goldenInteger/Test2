def choose_comprehensive_discard_from_output(output_text: str) -> str:
    """
    從 mahjong-helper 的輸出中選擇最適合的出牌。
    - 如果是“两向听” → 選擇速度最快的
    - 否則 → 選擇分數最高的
    回傳 helper tile 格式（如 '5m'、'7z'）
    """
    best_tile = ""
    best_metric = -float("inf")
    lines = output_text.splitlines()

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
                # 用速度選
                speed_match = re.search(r"\[(\d+\.\d+)\s*速度\]", line)
                if not speed_match:
                    continue
                speed = float(speed_match.group(1))
                metric = speed
            else:
                # 用分數選
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
