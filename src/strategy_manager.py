# stock_trading_bot/src/strategy_manager.py (抜粋 - 新規メソッドの追加)

import pandas as pd

from .config import SMA_LONG_RANGE, SMA_SHORT_RANGE  # 最適化範囲をインポート


class StrategyManager:
    def __init__(self):
        pass  # 初期化は不要

    # ... (既存の generate_trading_signals はそのまま) ...

    def optimize_strategy_parameters(self, df: pd.DataFrame):
        """
        与えられたデータフレームの期間内で、最適な戦略パラメータ（MA期間など）を見つけます。
        総リターンが最大となるパラメータの組み合わせを探索します。

        注意: この最適化は非常に計算コストがかかる可能性があります。
        """
        if df is None or df.empty:
            print("エラー: 最適化のためのデータがありません。")
            return None, None

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

                # シグナルを生成 (RSIは固定値と仮定、必要ならRSIも最適化範囲に含める)
                # 注: ここではgenerate_trading_signalsを直接呼び出さず、MAのみで簡易的にシグナルを生成
                # より厳密には、RSIや他の指標も組み合わせたバックテストロジックをここに移植する必要がある

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
                        # 'rsi_overbought': RSI_OVERBOUGHT, # RSIも最適化するならここに追加
                        # 'rsi_oversold': RSI_OVERSOLD
                    }
                    # print(f"  暫定最良パラメータ: {best_params}, リターン: {max_return:.2%}")

        print(
            f"最適化完了。最良パラメータ: {best_params}, 最大リターン: {max_return:.2%}"
        )
        return best_params
