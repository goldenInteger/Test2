import torch
from torch import nn, Tensor
from torch.nn import functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_sequence
from typing import *
from functools import partial
from itertools import permutations
from consts import obs_shape, oracle_obs_shape, ACTION_SPACE

class ChannelAttention(nn.Module):
    """
    告訴網路「哪些資訊比較重要」，像是在很多手牌資訊中自動挑出「這幾張牌好像很重要，要更重視它」
    """
    def __init__(self, channels, ratio=16, actv_builder=nn.ReLU, bias=True):
        super().__init__()
        """
        nn.Sequential：
        就像一個排隊的加工廠，把你設計好的層（像是卷積、激活函數）一個接一個地連起來。
        """
        self.shared_mlp = nn.Sequential(
            nn.Linear(channels, channels // ratio, bias=bias),  # 把原本的向量壓縮成比較小（例如 128 // 16 → 8）
            actv_builder(),                                     # 加一層激活函數，例如 ReLU 或 Mish，讓資料非線性化
            nn.Linear(channels // ratio, channels, bias=bias),  # 再把它還原回原本大小（例如 8 * 16 → 128）
        )
        """
        讓模型一開始更穩定，減少亂跑的機會。
        """
        if bias:
            for mod in self.modules():
                if isinstance(mod, nn.Linear):      # 如果發現它是 nn.Linear（線性層）
                    nn.init.constant_(mod.bias, 0)  # 就把它的 bias 全部初始化為 0
    """
    模型實際「運行」的時候會做什麼事情。
    """
    def forward(self, x: Tensor):
        avg_out = self.shared_mlp(x.mean(-1))   # 把每個牌的資訊「平均」，代表整體概況，並通過 shared MLP
        max_out = self.shared_mlp(x.amax(-1))   # 把每個牌的資訊「取最大值」，代表最強的信號，並通過 shared MLP
        weight = (avg_out + max_out).sigmoid()  # sigmoid()會把結果變成0～1之間的數字，當成「重要程度」
        x = weight.unsqueeze(-1) * x            # 這個數字會乘回原本的資料，代表「讓重要的資料變強、不重要的變弱」
        return x

class ResBlock(nn.Module):
    """
    殘差區塊
    """
    def __init__(
        self,
        channels,                   # 資料有幾個通道（像是有幾種特徵）
        *,                          
        norm_builder = nn.Identity, # 正規化，會改變數值，預設不做
        actv_builder = nn.ReLU,     # 激活函數
        pre_actv = False,           # 先激活否
    ):
        """
        激活函數：
        「讓資料有能力表達非線性，也就是彎彎曲曲的想法」
        如果沒有激活函數，神經網路就只能學會「直線關係」，沒辦法做複雜判斷。
        激活函數會幫資料過濾：哪些值要留下（>0），哪些值要忽略（<=0）

        卷積：
        「掃描附近的資訊，找出有用的模式」
        卷積就是這樣：「拿一個小窗口掃過整條資訊，找出裡面有什麼有用的規律」。

        正規化：
        「讓所有資料看起來比較平均，不要忽然有極端值亂入」
        正規化會把資料壓平在一個範圍內，讓學習更穩定、更快。
        """
        super().__init__()
        self.pre_actv = pre_actv

        if pre_actv:    # 先激活
            self.res_unit = nn.Sequential(
                norm_builder(),                                                          # 1. 正規化
                actv_builder(),                                                          # 2. 激活函數
                nn.Conv1d(channels, channels, kernel_size=3, padding=1, bias=False),     # 3. 卷積1
                norm_builder(),                                                          # 4. 再一次正規化
                actv_builder(),                                                          # 5. 再激活
                nn.Conv1d(channels, channels, kernel_size=3, padding=1, bias=False),     # 6. 卷積2
            )
        else:           # 先卷積
            self.res_unit = nn.Sequential(
                nn.Conv1d(channels, channels, kernel_size=3, padding=1, bias=False),     # 1. 卷積1
                norm_builder(),                                                          # 2. 正規化
                actv_builder(),                                                          # 3. 激活函數
                nn.Conv1d(channels, channels, kernel_size=3, padding=1, bias=False),     # 4. 卷積2
                norm_builder(),                                                          # 5. 再一次正規化
            )
            self.actv = actv_builder()                                                   # 6. 再激活
        self.ca = ChannelAttention(channels, actv_builder=actv_builder, bias=True)       # 自動挑出「哪些通道的資訊要被放大」

    def forward(self, x):
        out = self.res_unit(x)   # 把資料丟進剛剛做好的「兩層卷積處理區」
        out = self.ca(out)       # 加上注意力，放大重要的資訊
        out = out + x            # 和原始資料相加（殘差）
        if not self.pre_actv:
            out = self.actv(out) # 如果是後激活模式，再加一次激活
        return out

class ResNet(nn.Module):
    """
    建立一個多層的神經網路，重複堆疊 ResBlock（殘差區塊）進行深度分析，最後把輸入資料轉成一個長度 1024 的向量，給後面的 AI 決策使用。
    """
    def __init__(
        self,
        in_channels,                # 輸入資料的通道數
        conv_channels,              # 卷積後中間層的通道數
        num_blocks,                 # 要堆幾層 ResBlock
        *,
        norm_builder = nn.Identity, # 要不要正規化
        actv_builder = nn.ReLU,     # 激活函數
        pre_actv = False,           # 先激活否
    ):
        super().__init__()

        blocks = []
        """
        建立 num_blocks 個殘差區塊，堆起來做「深度分析」
        「這就像你 AI 要連續經過 5 個思考環節，第一層先看有沒有役，第二層看進張，第三層看安全牌……這樣一層一層想下去。」
        """
        for _ in range(num_blocks): 
            blocks.append(ResBlock(
                conv_channels,
                norm_builder = norm_builder,
                actv_builder = actv_builder,
                pre_actv = pre_actv,
            ))

        layers = [nn.Conv1d(in_channels, conv_channels, kernel_size=3, padding=1, bias=False)] # 原始輸入做第一次分析、轉換形狀，準備進入 ResBlock

        if pre_actv:
            layers += [*blocks, norm_builder(), actv_builder()]
        else:
            layers += [norm_builder(), actv_builder(), *blocks]

        layers += [
            nn.Conv1d(conv_channels, 32, kernel_size=3, padding=1), # 再卷一次，變成 32 個通道，為了後面好算
            actv_builder(),                                         # 最後一層激活
            nn.Flatten(),                                           # 把資料攤平成一條向量（從 3D → 1D）
            nn.Linear(32 * 34, 1024),                               # 轉成 1024 維的向量，這就是最後給 AI 決策的特徵
        ]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

class Brain(nn.Module):
    def __init__(self, *, conv_channels, num_blocks, is_oracle=False, version=1):
        super().__init__()
        self.is_oracle = is_oracle  # 要看「對手資訊」否
        self.version = version

        in_channels = obs_shape(version)[0]
        if is_oracle:   # 要看「對手隱藏資訊」（oracle），就額外加通道
            in_channels += oracle_obs_shape(version)[0]

        norm_builder = partial(nn.BatchNorm1d, conv_channels, momentum=0.01)    # BatchNorm1d 當作正規化方式，momentum 小一點代表「更新平均值要保守」
        actv_builder = partial(nn.Mish, inplace=True)                           # Mish 是激活函數，比 ReLU 更平滑，適合用在深層網路
        pre_actv = True                                                         # 預設先激活

        match version:
            case 1:
                # 換回傳統的「卷積 → 激活」順序 + 用 ReLU
                actv_builder = partial(nn.ReLU, inplace=True)
                pre_actv = False
                # 把 ResNet 輸出的特徵向量（1024 維）轉成潛在空間（latent space）512 維
                #  VAE 的架構
                self.latent_net = nn.Sequential(
                    nn.Linear(1024, 512),
                    nn.ReLU(inplace=True),
                )
                self.mu_head = nn.Linear(512, 512)      # 目前策略的中心（代表決策的平均）
                self.logsig_head = nn.Linear(512, 512)  # 決策的「不確定性」或「信心」
            case 2:
                # 不做特別處理
                pass
            case 3 | 4:
                # 一樣用 BatchNorm，但 eps 更小，代表精度提高，用於數值更敏感的訓練任務
                norm_builder = partial(nn.BatchNorm1d, conv_channels, momentum=0.01, eps=1e-3)
            case _:
                raise ValueError(f'Unexpected version {self.version}')
        # 根據選定的設定，建出一個特徵提取網路，最後輸出 1024 維的特徵向量
        self.encoder = ResNet(
            in_channels = in_channels,
            conv_channels = conv_channels,
            num_blocks = num_blocks,
            norm_builder = norm_builder,
            actv_builder = actv_builder,
            pre_actv = pre_actv,
        )
        self.actv = actv_builder()

        # always use EMA or CMA when True
        # 控制訓練時要不要「凍結 BatchNorm」
        self._freeze_bn = False

    def forward(self, obs: Tensor, invisible_obs: Optional[Tensor] = None) -> Union[Tuple[Tensor, Tensor], Tensor]:
        if self.is_oracle:
            assert invisible_obs is not None                # 額外的資訊（像是敵人的手牌）
            obs = torch.cat((obs, invisible_obs), dim=1)    # 兩段資訊合併
        phi = self.encoder(obs)                             # 用 ResNet 編碼資訊變成 φ（phi）

        match self.version:
            case 1:
                # 用 VAE 結構，輸出 μ 和 logσ 用來建策略分布，幫助強化學習做「探索 vs 穩定」的選擇
                latent_out = self.latent_net(phi)
                mu = self.mu_head(latent_out)
                logsig = self.logsig_head(latent_out)
                return mu, logsig
            case 2 | 3 | 4:
                # 把 phi 再經過激活函數（ReLU 或 Mish）輸出
                return self.actv(phi)
            case _:
                raise ValueError(f'Unexpected version {self.version}')

    def train(self, mode=True):
        super().train(mode) # 設定成訓練模式
        if self._freeze_bn: # 要不要凍結 BatchNorm（也就是不要讓它更新平均值和變異數）
            for mod in self.modules():
                if isinstance(mod, nn.BatchNorm1d):
                    mod.eval()
                    # I don't think this benefits
                    # module.requires_grad_(False)
        return self

    def reset_running_stats(self):
        """
        把所有 BatchNorm 累積的 mean/var 清掉，讓訓練從乾淨狀態重新開始
        """
        for mod in self.modules():
            if isinstance(mod, nn.BatchNorm1d):
                mod.reset_running_stats()

    def freeze_bn(self, value: bool):
        self._freeze_bn = value
        return self.train(self.training)

class AuxNet(nn.Module):
    """
    輔助預測模組，會把輸入的 x（1024 維向量）轉成多個不同的預測任務輸出
    """
    def __init__(self, dims=None):
        super().__init__()
        self.dims = dims                                    # 你要輸出幾個任務、每個任務要幾維
        self.net = nn.Linear(1024, sum(dims), bias=False)   # 用一層 linear 把輸入的 1024 維特徵轉成你要的多個任務結果

    def forward(self, x):
        """
        先把輸入 x（通常來自 Brain 或 ResNet）丟進 self.net，變成一個總輸出向量
        再用 .split(...) 按照 dims 把它切割成你想要的幾個部分
        """
        return self.net(x).split(self.dims, dim=-1)

class DQN(nn.Module):
    """
    根據場況資訊（phi 向量），評估出每一個出牌選項（34種）的 Q 值（價值分數），幫你決定要出哪張牌
    version = 1：經典教科書款，結構最單純
    version = 2：加入隱藏層 + Mish，效果強
    version = 3：和 2 類似，但隱藏層減半（想穩定收斂、又想快一點）
    version = 4：最簡速的輸出頭
    """
    def __init__(self, *, version=1):
        super().__init__()
        self.version = version
        match version:
            case 1:
                self.v_head = nn.Linear(512, 1)             #  預測「這個狀態整體的分數」
                self.a_head = nn.Linear(512, ACTION_SPACE)  #  預測「每一個動作的相對價值」
            case 2 | 3:
                hidden_size = 512 if version == 2 else 256
                self.v_head = nn.Sequential(
                    nn.Linear(1024, hidden_size),
                    nn.Mish(inplace=True),
                    nn.Linear(hidden_size, 1),
                )
                self.a_head = nn.Sequential(
                    nn.Linear(1024, hidden_size),
                    nn.Mish(inplace=True),
                    nn.Linear(hidden_size, ACTION_SPACE),
                )
            case 4:
                self.net = nn.Linear(1024, 1 + ACTION_SPACE)    # 不拆 V、A 頭，而是直接輸出 [V, A1, A2, ..., An]
                nn.init.constant_(self.net.bias, 0)             # 初始化 bias = 0，避免初期不穩定干擾

    def forward(self, phi, mask):
        if self.version == 4:
            v, a = self.net(phi).split((1, ACTION_SPACE), dim=-1)
        else:
            v = self.v_head(phi)                                # v 是一個 [batch_size, 1] 的狀態分數
            a = self.a_head(phi)                                # a 是一個 [batch_size, ACTION_SPACE] 的每個行動分數

        """
        我不是只看這動作值多少，而是它比其他合法動作高多少
        """
        a_sum = a.masked_fill(~mask, 0.).sum(-1, keepdim=True)  # 把所有非法動作對應的位置改成 0 再把合法動作的分數全部加總
        mask_sum = mask.sum(-1, keepdim=True)                   # 計算有多少個合法動作
        a_mean = a_sum / mask_sum                               # 拿合法動作的總分除以合法動作的數量得到合法動作的平均分數
        """
        q = V + A − mean(A)：這是 Dueling Q 的標準寫法
        masked_fill(~mask, -torch.inf)：把不能做的動作分數變成「無限小」，防止被選到
        """
        q = (v + a - a_mean).masked_fill(~mask, -torch.inf)
        return q
