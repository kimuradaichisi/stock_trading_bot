# stock_trading_bot/src/strategy_manager.py

import pandas as pd

from .config import LONG_MA_PERIOD, SHORT_MA_PERIOD


class StrategyManager:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()  # オリジナルのデータフレームを保護

    def generate_golden_dead_cross_signals(self):
        """
        ゴールデンクロス・デッドクロス戦略に基づいて売買シグナルを生成します。
        """
        if self.df is None or self.df.empty:
            print("エラー: 戦略生成のためのデータがありません。")
            return None

        short_ma_col = f"SMA_{SHORT_MA_PERIOD}"
        long_ma_col = f"SMA_{LONG_MA_PERIOD}"

        if short_ma_col not in self.df.columns or long_ma_col not in self.df.columns:
            print(
                "エラー: 移動平均線が計算されていません。Data Managerで計算してください。"
            )
            return None

        print("売買シグナル生成中 (ゴールデンクロス/デッドクロス)...")
        self.df["Signal"] = 0  # 1: 買い, -1: 売り, 0: ホールド

        # ゴールデンクロス (短期MAが長期MAを上回ったら買いシグナル)
        self.df.loc[self.df[short_ma_col] > self.df[long_ma_col], "Signal"] = 1

        # デッドクロス (短期MAが長期MAを下回ったら売りシグナル)
        self.df.loc[self.df[short_ma_col] < self.df[long_ma_col], "Signal"] = -1

        # ポジションの変化点 (実際の売買行動のトリガー) を検出
        # 0: 何もしない, 1: 買い, -1: 売り
        self.df["Trade_Signal"] = self.df["Signal"].diff()

        print("売買シグナル生成完了。")
        return self.df
