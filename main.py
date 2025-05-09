from mahjong_ai.core.table import Table

while True:
    table = Table()
    table.run_game_loop()

    # 檢查是否有玩家分數 >= 某個門檻（例如 30000）
    for player in table.players:
        if player.points >= 35000:
            print(f"🎉 玩家 {player.player_id} 達成目標分數 {player.points}！")
            exit()  # 或 break 也可，結束迴圈
