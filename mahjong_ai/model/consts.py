# consts.py

MAX_VERSION = 4

# 動作空間大小：
# 37 張牌可打（打牌 + 加槓選擇）
# + 1 立直
# + 3 吃
# + 1 碰
# + 1 加槓決定
# + 1 和牌
# + 1 流局
# + 1 PASS
ACTION_SPACE = 37 + 1 + 3 + 1 + 1 + 1 + 1 + 1  # = 46

GRP_SIZE = 7

def obs_shape(version: int) -> tuple[int, int]:
    match version:
        case 1:
            return (938, 34)
        case 2:
            return (942, 34)
        case 3:
            return (934, 34)
        case 4:
            return (1012, 34)
        case _:
            raise ValueError(f"Unsupported version: {version}")

def oracle_obs_shape(version: int) -> tuple[int, int]:
    match version:
        case 1:
            return (211, 34)
        case 2 | 3 | 4:
            return (217, 34)
        case _:
            raise ValueError(f"Unsupported version: {version}")