專案簡介：
  本專案旨在建立一套具備日麻規則理解與出牌策略判斷能力的 AI 系統，並結合深度強化學習技術，讓 AI 能在自動對局中逐步優化自身決策品質。
  我們透過自己實作的模擬對局產生訓練資料，搭配外部策略建議工具 mahjong-helper 作為行為參考與 reward 計算依據，使 AI 能從零學習，逐步形成出牌與鳴牌的準則。
  
系統特色：
  完整模擬日本麻將四人對局流程
  AI 支援出牌、吃碰槓、PASS、立直等行為
  自動化收集 obs / mask / action / reward 資料
  深度強化學習架構（CNN + DQN）進行策略學習
  外部工具 mahjong-helper 解析決策，回饋行為分數
  可透過 run_all.py 一鍵啟動多輪訓練與測試流程
  訓練日誌與模型結果皆儲存於 JSON / pth 檔

專案結構說明：
mahjong_ai/
├── table/                 # 牌桌模組（tile, player, round, meld, hand...）/n
├── data/                  # 模擬數據存放
├── models/                # 模型及數據存放
├── model/                 # 深度學習模型定義（Brain, DQN, AuxNet）
├── utils/                 # 連接mahjong-helper模組
├── simulate_selfplay.py   # 模擬多場對局、產生訓練資料
├── train.py               # 模型訓練主程式（支援 CLI 參數）
├── test_play.py           # 模型測試，回傳 avg_reward / win_rate / avg_rank
├── run_all.py             # 一鍵模擬 → 訓練 → 測試整合腳本
├── buffer.py              # ReplayBuffer 管理訓練資料

模型架構簡介：
  參考Mortal
  Brain：深度卷積網路，將 942x34 的觀察向量轉為 1024 維特徵向量，使用 ResNet 結構進行特徵提取。
  DQN：決策網路，接收 Brain 特徵後輸出每個動作的 Q 值，透過 mask 過濾非法動作。

Reward 設計邏輯：
  出牌與鳴牌行為皆由 mahjong-helper 給予建議結果評分。
  若 AI 出牌與 helper 預測相符（前 3 名切牌），給予正分 (+1.0)
  錯誤鳴牌行為、誤吃誤碰、PASS 該鳴時未鳴等，會給予負分（-0.2 ~ -1.0）

訓練流程說明：
  simulate_selfplay.py 自動模擬 N 場對局，記錄每步 obs, mask, action, reward
  資料儲存在 mahjong_ai/data/selfplay_round_XXXX.json
  train.py 使用上述資料訓練 CNN + DQN 網路
  訓練完成後由 test_play.py 自動測試模型效果
  若表現優於歷史最佳，會覆蓋儲存為 best_brain.pth
