# stock_trading_bot/src/visualizer.py

import matplotlib.pyplot as plt
import pandas as pd

from .config import LONG_MA_PERIOD, SHORT_MA_PERIOD


class Visualizer:
    def __init__(self, df_portfolio_history: pd.DataFrame, ticker_symbol: str = None):
        # バックテスターから返された、ポートフォリオ価値と単一銘柄のデータを統合したDataFrameを受け取る
        self.df = df_portfolio_history.copy()
        self.ticker_symbol = ticker_symbol  # プロット対象銘柄 (任意)

    def plot_results(self, summary_results: dict):
        """
        シミュレーション結果をグラフで可視化します。
        ポートフォリオ価値を中心にプロットします。
        """
        if self.df is None or self.df.empty or "Portfolio_Value" not in self.df.columns:
            print("エラー: 可視化するためのデータがありません。")
            return

        print("グラフ描画中...")
        plt.figure(figsize=(16, 8))  # グラフサイズを少し大きく

        # --- サブプロット1: ポートフォリオ価値の推移 ---
        ax1 = plt.subplot(2, 1, 1)  # 2行1列の1番目のサブプロット
        ax1.plot(
            self.df["Date"],
            self.df["Portfolio_Value"],
            label="Portfolio Value (Strategy)",
            color="green",
            linewidth=2,
        )
        ax1.axhline(
            y=summary_results["initial_cash"],
            color="gray",
            linestyle="--",
            label="Initial Cash",
        )

        # Buy & Hold (ポートフォリオ全体でのBuy & Holdは複雑なので、ここではプロットしないか、
        # 特定の指標（例: 日経平均）と比較する形にする)
        # 簡易的に、最初の銘柄のBuy & Holdを参考として表示
        if "Close" in self.df.columns:
            initial_close_price_for_buy_and_hold = self.df["Close"].iloc[0]
            # もし、ポートフォリオ初期値と銘柄初期値に乖離がある場合は、適切なスケール調整が必要
            buy_and_hold_portfolio_value_proxy = summary_results["initial_cash"] * (
                self.df["Close"] / initial_close_price_for_buy_and_hold
            )
            ax1.plot(
                self.df["Date"],
                buy_and_hold_portfolio_value_proxy,
                label="Reference (Buy & Hold of 1st Ticker)",
                color="orange",
                linestyle="--",
                alpha=0.7,
            )

        ax1.set_title(
            f"Portfolio Value Trend (Leverage: {summary_results['leverage_ratio']}x)"
        )
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Portfolio Value (JPY)")
        ax1.legend()
        ax1.grid(True, linestyle="--", alpha=0.6)

        # --- サブプロット2: 対象銘柄の株価とシグナル ---
        # バックテストで使われた代表銘柄 (ここではデータフレームに結合された最初の銘柄) をプロット
        ax2 = plt.subplot(
            2, 1, 2, sharex=ax1
        )  # 2行1列の2番目のサブプロット, x軸をax1と共有

        if "Close" in self.df.columns and f"SMA_{SHORT_MA_PERIOD}" in self.df.columns:
            ax2.plot(
                self.df["Date"],
                self.df["Close"],
                label=f"{self.ticker_symbol if self.ticker_symbol else 'Stock'} Close Price",
                color="gray",
                alpha=0.7,
            )
            ax2.plot(
                self.df["Date"],
                self.df[f"SMA_{SHORT_MA_PERIOD}"],
                label=f"SMA {SHORT_MA_PERIOD}",
                color="blue",
            )
            ax2.plot(
                self.df["Date"],
                self.df[f"SMA_{LONG_MA_PERIOD}"],
                label=f"SMA {LONG_MA_PERIOD}",
                color="red",
            )

            # 売買シグナルをプロット (Trade_Signalが1の点が買い、-1の点が売り)
            # Portoflio_Value DFにTrade_Signalがない場合があるので、元のDFから取得
            buy_points = self.df[self.df["Trade_Signal"] == 1]
            sell_points = self.df[self.df["Trade_Signal"] == -1]

            ax2.scatter(
                buy_points["Date"],
                buy_points["Close"],
                marker="^",
                color="green",
                s=100,
                label="Buy Signal",
                zorder=5,
            )
            ax2.scatter(
                sell_points["Date"],
                sell_points["Close"],
                marker="v",
                color="red",
                s=100,
                label="Sell Signal",
                zorder=5,
            )
        else:
            ax2.text(
                0.5,
                0.5,
                "Stock Price & Signals data not available for plot.",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax2.transAxes,
            )

        ax2.set_title(
            f"Stock Price and Signals ({self.ticker_symbol if self.ticker_symbol else 'Selected Ticker'})"
        )
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Stock Price (JPY)")
        ax2.legend()
        ax2.grid(True, linestyle="--", alpha=0.6)

        plt.tight_layout()  # サブプロット間のスペースを調整
        plt.show()
        print("グラフ描画完了。")
