# buffer.py - ReplayBuffer 類別，儲存 obs/action/reward 訓練資料

import json
import os
import random

class ReplayBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = []

    def push(self, data):
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append(data)

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def save_to_json(self, filename: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.buffer, f, ensure_ascii=False, indent=2)

    def clear(self):
        self.buffer = []