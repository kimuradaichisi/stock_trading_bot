# stock_trading_bot/src/strategy_manager.py

import pandas as pd

from .config import (  # 最適化範囲をインポート
    SMA_LONG_RANGE,
    SMA_SHORT_RANGE,
    STRATEGIES,  # 新しく追加
)


class StrategyManager:
    def __init__(self):
        """
        StrategyManagerのコンストラクタ。
        利用可能な戦略をconfigからロードします。
        """
        self.available_strategies = STRATEGIES

    def _generate_sma_signals(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        移動平均線 (SMA) に基づく売買シグナルを生成します。

        Args:
            df (pd.DataFrame): 株価データを含むDataFrame。
            params (dict): 戦略パラメータ (例: {'short_ma': 5, 'long_ma': 20})。

        Returns:
            pd.DataFrame: 'MA_Signal' 列が追加されたDataFrame。
        """
        df_copy = df.copy()
        short_ma_period = params.get("short_ma")
        long_ma_period = params.get("long_ma")

        if short_ma_period is None or long_ma_period is None:
            print("エラー: SMA戦略に必要なパラメータが不足しています。")
            return pd.DataFrame()

        short_ma_col = f"SMA_{short_ma_period}"
        long_ma_col = f"SMA_{long_ma_period}"

        if short_ma_col not in df_copy.columns or long_ma_col not in df_copy.columns:
            print(
                f"警告: 必要なMA列 ({short_ma_col}または{long_ma_col})が見つかりません。シグナル生成をスキップします。"
            )
            return pd.DataFrame()

        df_copy["MA_Signal"] = 0

        for i in range(1, len(df_copy)):
            prev_short_ma = df_copy[short_ma_col].iloc[i - 1]
            curr_short_ma = df_copy[short_ma_col].iloc[i]
            prev_long_ma = df_copy[long_ma_col].iloc[i - 1]
            curr_long_ma = df_copy[long_ma_col].iloc[i]

            # ゴールデンクロス
            if prev_short_ma <= prev_long_ma and curr_short_ma > curr_long_ma:
                df_copy.loc[i, "MA_Signal"] = 1  # 買い

            # デッドクロス
            elif prev_short_ma >= prev_long_ma and curr_short_ma < curr_long_ma:
                df_copy.loc[i, "MA_Signal"] = -1  # 売り
        return df_copy

    def _generate_rsi_signals(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        RSI (Relative Strength Index) に基づく売買シグナルを生成します。

        Args:
            df (pd.DataFrame): 株価データを含むDataFrame。
            params (dict): 戦略パラメータ (例: {'rsi_period': 14, 'rsi_overbought': 70, 'rsi_oversold': 30})。

        Returns:
            pd.DataFrame: 'RSI_Signal' 列が追加されたDataFrame。
        """
        df_copy = df.copy()
        rsi_overbought = params.get("rsi_overbought")
        rsi_oversold = params.get("rsi_oversold")

        if rsi_overbought is None or rsi_oversold is None:
            print("エラー: RSI戦略に必要なパラメータが不足しています。")
            return pd.DataFrame()

        if "RSI" not in df_copy.columns:
            print("警告: RSI列が見つかりません。RSIシグナル生成をスキップします。")
            return pd.DataFrame()

        df_copy["RSI_Signal"] = 0
        df_copy.loc[df_copy["RSI"] <= rsi_oversold, "RSI_Signal"] = (
            1  # 売られすぎ -> 買い
        )
        df_copy.loc[
            df_copy["RSI"] >= rsi_overbought, "RSI_Signal"
        ] = -1  # 買われすぎ -> 売り
        return df_copy

    def generate_trading_signals(
        self, df: pd.DataFrame, strategy_name: str, params: dict
    ) -> pd.DataFrame:
        """
        指定された戦略に基づいてデータフレームに売買シグナルを生成します。

        Args:
            df (pd.DataFrame): 株価データを含むDataFrame。
            strategy_name (str): 使用する戦略の名前 (例: 'SMA_Strategy', 'RSI_Strategy')。
            params (dict): 戦略に適用するパラメータ。

        Returns:
            pd.DataFrame: 'Trade_Signal' 列が追加されたDataFrame。
        """
        if df.empty:
            return pd.DataFrame()

        df_copy = df.copy()
        df_copy["Trade_Signal"] = 0  # 初期化

        if strategy_name == "SMA_Strategy":
            df_with_ma_signal = self._generate_sma_signals(df_copy, params)
            if not df_with_ma_signal.empty:
                df_copy["Trade_Signal"] = df_with_ma_signal["MA_Signal"]
        elif strategy_name == "RSI_Strategy":
            df_with_rsi_signal = self._generate_rsi_signals(df_copy, params)
            if not df_with_rsi_signal.empty:
                df_copy["Trade_Signal"] = df_with_rsi_signal["RSI_Signal"]
        # 他の戦略もここに追加

        return df_copy

    def optimize_strategy_parameters(self, df: pd.DataFrame, strategy_name: str):
        """
        与えられたデータフレームの期間内で、指定された戦略の最適なパラメータを見つけます。
        総リターンが最大となるパラメータの組み合わせを探索します。

        Args:
            df (pd.DataFrame): 最適化に使用する株価データ。
            strategy_name (str): 最適化する戦略の名前。

        Returns:
            dict: 最適化されたパラメータの辞書、またはNone。
        """
        if df is None or df.empty:
            print("エラー: 最適化のためのデータがありません。")
            return None

        if strategy_name == "SMA_Strategy":
            return self._optimize_sma_parameters(df)
        elif strategy_name == "RSI_Strategy":
            # RSI戦略の最適化ロジックをここに追加
            print(
                "RSI戦略の最適化は未実装です。SMA戦略のデフォルトパラメータを返します。"
            )
            return self.available_strategies.get("RSI_Strategy")
        else:
            print(f"エラー: 未知の戦略 '{strategy_name}' です。")
            return None

    def _optimize_sma_parameters(self, df: pd.DataFrame):
        """
        SMA戦略の最適なパラメータ（短期/長期移動平均線期間）を見つけます。
        """
        best_params = {}
        max_return = -float("inf")  # 負の無限大で初期化

        print("SMA戦略パラメータを最適化中...")

        for short_ma in SMA_SHORT_RANGE:
            for long_ma in SMA_LONG_RANGE:
                if short_ma >= long_ma:  # 短期MAが長期MAより短いことを確認
                    continue

                df_temp = df.copy()
                df_temp[f"SMA_{short_ma}"] = (
                    df_temp["Close"].rolling(window=short_ma).mean()
                )
                df_temp[f"SMA_{long_ma}"] = (
                    df_temp["Close"].rolling(window=long_ma).mean()
                )
                df_temp.dropna(inplace=True)
                df_temp.reset_index(drop=True, inplace=True)

                if df_temp.empty:
                    continue

                # 簡易的な総リターン計算 (この期間でどれだけ増えたか)
                cash = 1000000  # 仮の初期資金
                shares = 0

                for k in range(1, len(df_temp)):
                    prev_short_ma = df_temp[f"SMA_{short_ma}"].iloc[k - 1]
                    curr_short_ma = df_temp[f"SMA_{short_ma}"].iloc[k]
                    prev_long_ma = df_temp[f"SMA_{long_ma}"].iloc[k - 1]
                    curr_long_ma = df_temp[f"SMA_{long_ma}"].iloc[k]

                    curr_close = df_temp["Close"].iloc[k]

                    # ゴールデンクロス (買いシグナル)
                    if prev_short_ma <= prev_long_ma and curr_short_ma > curr_long_ma:
                        if cash > 0:
                            shares_to_buy = int(cash // curr_close)
                            if shares_to_buy > 0:
                                shares += shares_to_buy
                                cash -= shares_to_buy * curr_close

                    # デッドクロス (売りシグナル)
                    elif prev_short_ma >= prev_long_ma and curr_short_ma < curr_long_ma:
                        if shares > 0:
                            cash += shares * curr_close
                            shares = 0

                # 最終的な資産価値
                final_value = cash + (
                    shares * df_temp["Close"].iloc[-1] if shares > 0 else 0
                )
                current_return = (
                    final_value - 1000000
                ) / 1000000  # 簡易的なリターン計算

                if current_return > max_return:
                    max_return = current_return
                    best_params = {
                        "short_ma": short_ma,
                        "long_ma": long_ma,
                    }

        print(
            f"最適化完了。最良パラメータ: {best_params}, 最大リターン: {max_return:.2%}"
        )
        return best_params
