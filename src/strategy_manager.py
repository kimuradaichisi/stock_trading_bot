# stock_trading_bot/src/strategy_manager.py

import pandas as pd

from .config import (  # 最適化範囲をインポート
    LONG_MA_PERIOD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    SHORT_MA_PERIOD,
    SMA_LONG_RANGE,
    SMA_SHORT_RANGE,
)


class StrategyManager:
    def __init__(self):
        pass  # 初期化は不要

    def generate_trading_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データフレームに売買シグナルを生成します。
        - ゴールデンクロス/デッドクロス (MAに基づく)
        - RSIの買われすぎ/売られすぎ
        結合して最終的な売買シグナル ('Trade_Signal': 1=買い, -1=売り, 0=なし) を生成します。
        """
        if df.empty:
            return pd.DataFrame()

        df_copy = df.copy()

        # MAシグナル
        # 'SMA_SHORT_MA_PERIOD' と 'SMA_LONG_MA_PERIOD' は config.py で定義された期間に対応
        # ただし、ウォークフォワード中は main.py で config.SHORT_MA_PERIOD/LONG_MA_PERIOD が一時的に書き換えられるため、
        # ここでは直接 config から期間を取得するのではなく、df_copyに既に計算済みのMA列があることを前提とします。
        # df_copy に MA列がない場合はエラーになるため、適切なMA列が存在するか確認するか、
        # generate_trading_signals に MA期間を引数として渡す設計にするのがより頑健です。
        # 現在の設計では、data_managerがMA列を計算しているため、それが df に含まれているはずです。

        # MAの列名が存在するか確認
        short_ma_col = f"SMA_{SHORT_MA_PERIOD}"
        long_ma_col = f"SMA_{LONG_MA_PERIOD}"

        if short_ma_col not in df_copy.columns or long_ma_col not in df_copy.columns:
            print(
                f"警告: 必要なMA列 ({short_ma_col}または{long_ma_col})が見つかりません。シグナル生成をスキップします。"
            )
            # この場合、generate_trading_signalsを呼び出す前に、
            # data_managerでMAが計算されていることを保証する必要があります。
            # main.pyで config の値を一時的に変更した後に、再度 calculate_moving_averages を呼び出すのが安全です。
            return pd.DataFrame()  # 空のDataFrameを返すか、エラーを発生させる

        df_copy["MA_Signal"] = 0
        df_copy["RSI_Signal"] = 0

        # ゴールデンクロス (買い) / デッドクロス (売り)
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

        # RSIシグナル
        if "RSI" in df_copy.columns:
            df_copy.loc[df_copy["RSI"] <= RSI_OVERSOLD, "RSI_Signal"] = (
                1  # 売られすぎ -> 買い
            )
            df_copy.loc[
                df_copy["RSI"] >= RSI_OVERBOUGHT, "RSI_Signal"
            ] = -1  # 買われすぎ -> 売り

        # 最終的な売買シグナルを決定 (ここではMAシグナルを優先し、RSIで補完する簡易ロジック)
        # より高度な戦略では、ここで複数のシグナルを組み合わせる複雑なルールを定義します。
        df_copy["Trade_Signal"] = 0
        # MAの買いシグナルが出たら買う
        df_copy.loc[df_copy["MA_Signal"] == 1, "Trade_Signal"] = 1
        # MAの売りシグナルが出たら売る
        df_copy.loc[df_copy["MA_Signal"] == -1, "Trade_Signal"] = -1

        # MAシグナルがない場合にRSIシグナルを考慮（例：RSIが売られすぎでMAシグナルがなければ買う）
        # ただし、現在の「半年で5倍」高レバレッジ戦略では、MAクロスに重点を置くため、
        # ここではMAシグナルがゼロの場合にRSIのみでトレードするのは避けるか、慎重に実装すべきです。
        # 今回は、MAクロスがメインシグナルとし、RSIはあくまで補助的な確認指標として用いる。
        # バックテストロジックはMAシグナルのみで動いているので、ここではMA_SignalをそのままTrade_Signalに。
        # df_copy['Trade_Signal'] = df_copy['MA_Signal'] # MAシグナルをそのままTrade_Signalとする

        # 例: MAシグナルがなく、かつRSIが極端な場合にのみRSIシグナルを採用
        # df_copy.loc[(df_copy['MA_Signal'] == 0) & (df_copy['RSI_Signal'] == 1), 'Trade_Signal'] = 1
        # df_copy.loc[(df_copy['MA_Signal'] == 0) & (df_copy['RSI_Signal'] == -1), 'Trade_Signal'] = -1

        return df_copy

    # ... (optimize_strategy_parameters メソッドはそのまま維持) ...
    def optimize_strategy_parameters(self, df: pd.DataFrame):
        """
        与えられたデータフレームの期間内で、最適な戦略パラメータ（MA期間など）を見つけます。
        総リターンが最大となるパラメータの組み合わせを探索します。

        注意: この最適化は非常に計算コストがかかる可能性があります。
        """
        if df is None or df.empty:
            print("エラー: 最適化のためのデータがありません。")
            return None

        best_params = {}
        max_return = -float("inf")  # 負の無限大で初期化

        print("戦略パラメータを最適化中...")

        # グリッドサーチ (総当たり) で最適なパラメータを探す
        for short_ma in SMA_SHORT_RANGE:
            for long_ma in SMA_LONG_RANGE:
                if short_ma >= long_ma:  # 短期MAが長期MAより短いことを確認
                    continue

                # 現在のパラメータで移動平均線を計算
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
                # MAシグナルだけで売買をシミュレートする簡易ロジック
                cash = 1000000  # 仮の初期資金
                shares = 0
                buy_price = 0

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
                                buy_price = curr_close  # 買値記録
                                cash -= shares_to_buy * curr_close

                    # デッドクロス (売りシグナル)
                    elif prev_short_ma >= prev_long_ma and curr_short_ma < curr_long_ma:
                        if shares > 0:
                            cash += shares * curr_close
                            shares = 0
                            buy_price = 0  # 買値リセット

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
                    # print(f"  暫定最良パラメータ: {best_params}, リターン: {max_return:.2%}")

        print(
            f"最適化完了。最良パラメータ: {best_params}, 最大リターン: {max_return:.2%}"
        )
        return best_params
