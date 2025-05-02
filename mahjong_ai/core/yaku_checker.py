# mahjong_ai/core/yaku_checker.py

from collections import Counter
from mahjong_ai.core.tile import Tile
from mahjong_ai.core.meld import Meld

# ==================================================
# 基礎役種判定
# ==================================================

def is_menzenchin_tsumo(is_menzen: bool, is_tsumo: bool) -> bool:
    """
    門前清自摸：門前狀態且自摸
    """
    return is_menzen and is_tsumo

def is_riichi(is_menzen: bool, is_riichi: bool) -> bool:
    """
    立直：門前狀態且宣告立直
    """
    return is_menzen and is_riichi

def is_ippatsu(is_menzen: bool, is_riichi: bool, is_ippatsu: bool) -> bool:
    """
    一發：門前狀態，立直後一巡內胡牌
    """
    return is_menzen and is_riichi and is_ippatsu

def is_tanyao(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否為斷么九（全部 2~8數字，不能有字牌）
    """
    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    for tile in tiles:
        if tile.tile_type == 'honor':
            return False
        if tile.tile_value == 1 or tile.tile_value == 9:
            return False

    return True

def is_pinfu(hand_tiles: list, melds: list) -> bool:
    """
    改良版判斷平和
    條件：
    - 門前清（沒有副露）
    - 手牌只由順子構成（無刻子、槓子）
    - 雀頭不能是字牌（役牌）
    - （未處理兩面聽，需要進一步配合聽牌情報）
    """
    if melds:
        return False  # 副露過不能平和

    tiles = hand_tiles.copy()
    counts = Counter((tile.tile_value, tile.tile_type) for tile in tiles)

    pair_candidates = []
    temp_counts = counts.copy()

    # 嘗試找一個作為雀頭
    for (val, typ), cnt in counts.items():
        if cnt >= 2:
            pair_candidates.append((val, typ))

    for pair in pair_candidates:
        temp_counts = counts.copy()
        temp_counts[pair] -= 2

        if check_all_shuntsu(temp_counts):
            # 檢查雀頭是不是字牌
            val, typ = pair
            if typ == 'honor':
                return False  # 雀頭是字牌，不符合平和
            return True  # 成功找到一種配置符合平和

    return False

def check_all_shuntsu(counts: Counter) -> bool:
    """
    嘗試將所有牌組成順子
    """
    if sum(counts.values()) == 0:
        return True

    for (val, typ), cnt in sorted(counts.items()):
        if cnt == 0:
            continue
        if typ not in ['man', 'pin', 'sou']:
            return False  # 字牌不能組成順子
        # 檢查是否有 (val, val+1, val+2)
        if counts[(val, typ)] > 0 and counts.get((val + 1, typ), 0) > 0 and counts.get((val + 2, typ), 0) > 0:
            counts[(val, typ)] -= 1
            counts[(val + 1, typ)] -= 1
            counts[(val + 2, typ)] -= 1
            return check_all_shuntsu(counts)
        else:
            return False  # 找不到順子，失敗

    return False

def is_toitoi(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否是對對和（全部是刻子或槓子）
    """
    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    counts = Counter((tile.tile_value, tile.tile_type) for tile in tiles)
    pair_count = 0

    for cnt in counts.values():
        if cnt == 2:
            pair_count += 1
        elif cnt != 3 and cnt != 4:
            return False  # 只允許對子、刻子、槓子

    return pair_count == 1  # 必須恰好一對雀頭


def is_sanankou(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否是三暗刻（不包括副露的碰）
    """
    # 簡化版：只看暗刻（自己湊成的三張）
    counts = Counter((tile.tile_value, tile.tile_type) for tile in hand_tiles)
    concealed_triplets = sum(1 for cnt in counts.values() if cnt == 3)

    return concealed_triplets >= 3

def is_shousangen(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否是小三元
    """
    dragons = [5, 6, 7]  # 白發中
    dragon_counts = {num: 0 for num in dragons}

    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    for tile in tiles:
        if tile.tile_type == 'honor' and tile.tile_value in dragons:
            dragon_counts[tile.tile_value] += 1

    pairs = sum(1 for v in dragon_counts.values() if v == 2)
    triplets = sum(1 for v in dragon_counts.values() if v >= 3)

    return triplets == 2 and pairs == 1


def is_honitsu(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否是混一色（只有一種數牌＋字牌）
    """
    colors = set()
    has_honor = False

    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    for tile in tiles:
        if tile.tile_type == 'honor':
            has_honor = True
        else:
            colors.add(tile.tile_type)

    return len(colors) == 1 and has_honor


def is_chinitsu(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否是清一色（只有一種花色，沒有字牌）
    """
    colors = set()

    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    for tile in tiles:
        if tile.tile_type == 'honor':
            return False
        colors.add(tile.tile_type)

    return len(colors) == 1

def is_ikkitsuukan(hand_tiles, melds):
    """
    判斷是否為一氣通貫
    同一花色 123 456 789 三組順子
    """
    suits = ['man', 'pin', 'sou']
    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)
    
    for suit in suits:
        numbers = [tile.tile_value for tile in tiles if tile.tile_type == suit]
        numbers.sort()
        return all(n in numbers for n in [1,2,3,4,5,6,7,8,9])
    return False

def is_sanshoku_doujun(hand_tiles, melds):
    """
    判斷是否為三色同順
    萬筒索各有同樣數字的順子
    """
    triplets = {i: set() for i in range(1, 8)}  # 1~7起頭
    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    for tile in tiles:
        if tile.tile_type in ['man', 'pin', 'sou']:
            triplets[tile.tile_value].add(tile.tile_type)

    for num, suits in triplets.items():
        if len(suits) == 3:
            return True
    return False

def is_chiitoitsu(hand_tiles, melds):
    """
    判斷是否為七對子
    """
    if melds:
        return False
    if len(hand_tiles) != 14:
        return False
    counts = Counter((tile.tile_value, tile.tile_type) for tile in hand_tiles)
    return all(cnt == 2 for cnt in counts.values())

def is_honchantai(hand_tiles, melds):
    """
    判斷是否為混全帶么九（每組都有么九牌，且可以有字）
    """
    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)
    
    for tile in tiles:
        if tile.tile_type in ['man', 'pin', 'sou'] and tile.tile_value not in [1,9]:
            return False
    return True

def is_junchantai(hand_tiles, melds):
    """
    判斷是否為純全帶么九（每組都有么九牌，且不能有字）
    """
    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)
    
    for tile in tiles:
        if tile.tile_type == 'honor' or tile.tile_value not in [1,9]:
            return False
    return True

def is_ryanpeikou(hand_tiles: list, melds: list) -> bool:
    """
    判斷二盃口（兩組一盃口）
    """
    if melds:
        return False

    counts = Counter()
    for tile in hand_tiles:
        counts[(tile.tile_value, tile.tile_type)] += 1

    peikou = 0
    for (val, typ) in counts:
        if typ in ['man', 'pin', 'sou']:
            if counts[(val, typ)] >= 2 and counts.get((val + 1, typ), 0) >= 2 and counts.get((val + 2, typ), 0) >= 2:
                peikou += 1
                counts[(val, typ)] -= 2
                counts[(val + 1, typ)] -= 2
                counts[(val + 2, typ)] -= 2

    return peikou >= 2


def is_sankantsu(hand_tiles, melds):
    """
    判斷是否為三槓子
    """
    kantsu_count = 0
    for meld in melds:
        if len(meld.tiles) == 4:
            kantsu_count += 1
    return kantsu_count >= 3

def is_double_riichi(is_menzen: bool, is_riichi: bool, is_first_turn: bool) -> bool:
    """
    判斷是否雙立直：開局第一巡，門清且立直
    """
    return is_menzen and is_riichi and is_first_turn

def is_iipeikou(hand_tiles: list, melds: list) -> bool:
    """
    判斷一盃口（同一花色，同一順子重複一次）
    """
    if melds:
        return False  # 副露過不能一盃口

    counts = Counter()
    for tile in hand_tiles:
        counts[(tile.tile_value, tile.tile_type)] += 1

    peikou = 0
    for (val, typ) in counts:
        if typ in ['man', 'pin', 'sou']:
            if counts[(val, typ)] >= 2 and counts.get((val + 1, typ), 0) >= 2 and counts.get((val + 2, typ), 0) >= 2:
                peikou += 1
                # 減掉已經組成的順子
                counts[(val, typ)] -= 2
                counts[(val + 1, typ)] -= 2
                counts[(val + 2, typ)] -= 2

    return peikou == 1

def is_sanshoku_doukou(hand_tiles: list, melds: list) -> bool:
    """
    判斷三色同刻（萬筒索，各一組相同數字的刻子）
    """
    counts = Counter()
    for tile in hand_tiles:
        counts[(tile.tile_value, tile.tile_type)] += 1
    for meld in melds:
        for tile in meld.tiles:
            counts[(tile.tile_value, tile.tile_type)] += 1

    for num in range(1, 10):
        types = []
        for typ in ['man', 'pin', 'sou']:
            if counts.get((num, typ), 0) >= 3:
                types.append(typ)
        if len(types) == 3:
            return True
    return False


# ==================================================
# 役滿判定
# ==================================================

def is_kokushi(tiles: list) -> bool:
    """
    判斷是否是國士無雙
    """
    required = [
        (1, 'man'), (9, 'man'),
        (1, 'pin'), (9, 'pin'),
        (1, 'sou'), (9, 'sou'),
        (1, 'honor'), (2, 'honor'), (3, 'honor'), (4, 'honor'),
        (5, 'honor'), (6, 'honor'), (7, 'honor')
    ]

    tile_counter = Counter((tile.tile_value, tile.tile_type) for tile in tiles)

    have_all = all(tile in tile_counter for tile in required)
    has_pair = any(count >= 2 for count in tile_counter.values())

    return have_all and has_pair

def is_daisangen(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否為大三元
    """
    dragons = [5, 6, 7]  # 白發中
    counts = Counter()

    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    for tile in tiles:
        if tile.tile_type == 'honor' and tile.tile_value in dragons:
            counts[tile.tile_value] += 1

    return all(count >= 3 for count in counts.values())


def is_tsuuiisou(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否為字一色（全部字牌）
    """
    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    return all(tile.tile_type == 'honor' for tile in tiles)


def is_shousuushii(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否為小四喜（三刻一對）
    """
    winds = [1, 2, 3, 4]
    counts = Counter()

    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    for tile in tiles:
        if tile.tile_type == 'honor' and tile.tile_value in winds:
            counts[tile.tile_value] += 1

    triplets = sum(1 for c in counts.values() if c >= 3)
    pairs = sum(1 for c in counts.values() if c == 2)

    return triplets == 3 and pairs == 1

def is_daisuushii(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否為大四喜（四刻）
    """
    winds = [1, 2, 3, 4]
    counts = Counter()

    tiles = hand_tiles.copy()
    for meld in melds:
        tiles.extend(meld.tiles)

    for tile in tiles:
        if tile.tile_type == 'honor' and tile.tile_value in winds:
            counts[tile.tile_value] += 1

    triplets = sum(1 for c in counts.values() if c >= 3)

    return triplets == 4


def is_suuankou(hand_tiles: list, melds: list) -> bool:
    """
    判斷是否為四暗刻
    """
    counts = Counter((tile.tile_value, tile.tile_type) for tile in hand_tiles)
    concealed_triplets = sum(1 for cnt in counts.values() if cnt == 3)

    return concealed_triplets >= 4


def detect_yakus(hand_tiles, melds, is_menzen, is_tsumo, is_riichi, is_ippatsu, is_first_turn) -> list:
    """
    綜合判斷目前手牌、副露與局面條件，列出所有達成的役種。
    """

    yakus = []

    # 整合手牌＋副露
    all_tiles = hand_tiles.copy()
    for meld in melds:
        all_tiles.extend(meld.tiles)

    # ✅ 役滿優先判斷
    if is_kokushi(all_tiles):
        return ["國士無雙"]
    if is_daisangen(hand_tiles, melds):
        return ["大三元"]
    if is_tsuuiisou(hand_tiles, melds):
        return ["字一色"]
    if is_shousuushii(hand_tiles, melds):
        return ["小四喜"]
    if is_daisuushii(hand_tiles, melds):
        return ["大四喜"]
    if is_suuankou(hand_tiles, melds):
        return ["四暗刻"]

    # ✅ 一般役判斷
    if is_menzenchin_tsumo(is_menzen, is_tsumo):
        yakus.append("門前清自摸")
    if is_riichi(is_menzen, is_riichi):
        yakus.append("立直")
    if is_ippatsu(is_menzen, is_riichi, is_ippatsu):
        yakus.append("一發")
    if is_menzen and is_pinfu(hand_tiles, melds):
        yakus.append("平和")
    if is_tanyao(hand_tiles, melds):
        yakus.append("斷么九")
    if is_toitoi(hand_tiles, melds):
        yakus.append("對對和")
    if is_sanankou(hand_tiles, melds):
        yakus.append("三暗刻")
    if is_shousangen(hand_tiles, melds):
        yakus.append("小三元")
    if is_honitsu(hand_tiles, melds):
        yakus.append("混一色")
    if is_chinitsu(hand_tiles, melds):
        yakus.append("清一色")
    if is_ikkitsuukan(hand_tiles, melds):
        yakus.append("一氣通貫")
    if is_sanshoku_doujun(hand_tiles, melds):
        yakus.append("三色同順")
    if is_chiitoitsu(hand_tiles, melds):
        yakus.append("七對子")
    if is_honchantai(hand_tiles, melds):
        yakus.append("混全帶么九")
    if is_junchantai(hand_tiles, melds):
        yakus.append("純全帶么九")
    if is_ryanpeikou(hand_tiles, melds):
        yakus.append("二盃口")
    if is_sankantsu(hand_tiles, melds):
        yakus.append("三槓子")
    if is_double_riichi(is_menzen, is_riichi, is_first_turn):
        yakus.append("雙立直")
    if is_iipeikou(hand_tiles, melds):
        yakus.append("一盃口")
    if is_sanshoku_doukou(hand_tiles, melds):
        yakus.append("三色同刻")


    return yakus

