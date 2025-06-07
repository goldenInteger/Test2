from mahjong_ai.table.table import Table
from mahjong_ai.table.tile import Tile
from mahjong_ai.table.meld import Meld, MeldType
from mahjong_ai.action import ai_decide_action

def setup_virtual_table() -> Table:
    """
    建立並回傳一個可用來推論的虛擬 Table 物件。
    你可在這邊直接設定任意場況。
    """
    table = Table()
    ai_player = table.players[3]
    ai_player.is_ai = True

    # === AI 手牌（13 張）
    hand_ids = [2 ,4, 5, 12, 13, 18, 21, 32, 32 ,32,3,11,4]  # 一二三萬 + 白白發中
    ai_player.hand.tiles = [Tile.from_34_id(tid) for tid in hand_ids]

    # === 副露（碰發）← Player 2
    ai_player.melds = [
    ]

    # === 自家牌河
    ai_discards = [28,9,30,26,7,27]
    ai_player.river.discarded_tiles.clear()
    for tid in ai_discards:
        ai_player.river.add_discard(Tile.from_34_id(tid))

    # === 他家模擬捨牌
    other_discards = {
        0: [19,33,33,32,33,14,29,21],
        1: [10,12,29,19,31,26,28,28],
        2: [28,8,18,1,29,31,6],
    }
    for pid, tids in other_discards.items():
        table.players[pid].river.discarded_tiles.clear()
        for tid in tids:
            table.players[pid].river.add_discard(Tile.from_34_id(tid))

    # === 分數與風位設定
    ai_player.points = 25000
    ai_player.seat_wind = 3
    ai_player.furiten = False
    ai_player.is_riichi = False

    # === 場況設定
    table.round.dealer_id = 0
    table.round.honba = 1
    table.round.kyotaku = 0
    table.wall.open_dora_wall = [Tile.from_34_id(16)] 
    table.remaining = 41
    table.current_turn = 2
    table.last_discard_player_id = 2
    return table

def explain_action(action: int):
    """
    輸出動作對應的語義說明。
    """
    if 0 <= action <= 33:
        print(f"→ AI 建議打出：{Tile.from_34_id(action)}")
    elif action == 34:
        print("→ AI 建議宣告立直")
    elif action == 42:
        print("→ AI 建議和牌")
    elif action == 44:
        print("→ AI 選擇 PASS")
    else:
        print("→ 其他動作代碼：", action)

def main():
    print("=== 模擬虛擬場況並使用模型推論 ===")
    table = setup_virtual_table()

    action_types = {"chi_low"}  # 若模擬吃/碰/槓再加入對應 type
    action = ai_decide_action(table, tile=Tile.from_34_id(6), buffer=None, action_types=action_types)

    print(f"\n[AI 選擇的動作編號]: {action}")
    explain_action(action)

if __name__ == "__main__":
    main()