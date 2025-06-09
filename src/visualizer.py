# stock_trading_bot/src/visualizer.py

import matplotlib.pyplot as plt
import pandas as pd

from .config import LONG_MA_PERIOD, SHORT_MA_PERIOD


class Visualizer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def plot_results(self, summary_results: dict):
        """
        シミュレーション結果をグラフで可視化します。
        """
        if self.df is None or self.df.empty:
            print("エラー: 可視化するためのデータがありません。")
            return

        print("グラフ描画中...")
        plt.figure(figsize=(14, 7))

        # 株価と移動平均線
        plt.plot(
            self.df["Date"],
            self.df["Close"],
            label="Stock Close Price",
            color="gray",
            alpha=0.7,
        )
        plt.plot(
            self.df["Date"],
            self.df[f"SMA_{SHORT_MA_PERIOD}"],
            label=f"SMA {SHORT_MA_PERIOD} (Short)",
            color="blue",
        )
        plt.plot(
            self.df["Date"],
            self.df[f"SMA_{LONG_MA_PERIOD}"],
            label=f"SMA {LONG_MA_PERIOD} (Long)",
            color="red",
        )

        # ポートフォリオ価値
        plt.plot(
            self.df["Date"],
            self.df["Portfolio_Value"],
            label="Portfolio Value (Strategy)",
            color="green",
            linewidth=2,
        )

        # Buy & Hold (ずっと保有) の比較
        # Buy & Hold の価値は、初期資金 * (最終株価 / 開始株価) で計算
        initial_close_price = self.df["Close"].iloc[0]
        buy_and_hold_portfolio_value = summary_results["initial_cash"] * (
            self.df["Close"] / initial_close_price
        )
        plt.plot(
            self.df["Date"],
            buy_and_hold_portfolio_value,
            label="Portfolio Value (Buy & Hold)",
            color="orange",
            linestyle="--",
            alpha=0.7,
        )

        # 売買シグナルをプロット
        # Trade_Signalが1の点が買いシグナル、-1の点が売りシグナル
        buy_points = self.df[self.df["Trade_Signal"] == 1]
        sell_points = self.df[self.df["Trade_Signal"] == -1]

        plt.scatter(
            buy_points["Date"],
            buy_points["Close"],
            marker="^",
            color="green",
            s=100,
            label="Buy Signal",
            zorder=5,
        )
        plt.scatter(
            sell_points["Date"],
            sell_points["Close"],
            marker="v",
            color="red",
            s=100,
            label="Sell Signal",
            zorder=5,
        )

        plt.title("Stock Trading Simulation (Golden/Dead Cross Strategy)")
        plt.xlabel("Date")
        plt.ylabel("Value (JPY)")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.show()
        print("グラフ描画完了。")
