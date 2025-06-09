# stock_trading_bot/src/visualizer.py

import matplotlib.pyplot as plt
import pandas as pd

from .config import LONG_MA_PERIOD, SHORT_MA_PERIOD  # これらのインポートも必要


class Visualizer:
    def __init__(self, df_portfolio_history: pd.DataFrame):
        self.df_portfolio_history = df_portfolio_history

    # ▼ ここを修正 ▼
    def plot_results(
        self,
        df_portfolio: pd.DataFrame,
        df_trades: pd.DataFrame,
        file_name: str,
        reference_ticker_data: pd.DataFrame = None,
    ):
        # ▲ ここまで修正 ▲
        """
        ポートフォリオ価値の推移と取引シグナルをグラフで表示し、ファイルに保存します。
        """
        plt.style.use("seaborn-v0_8-darkgrid")  # スタイルを適用

        fig, axes = plt.subplots(
            2, 1, figsize=(16, 12), gridspec_kw={"height_ratios": [2, 1]}
        )
        fig.suptitle("Trading Strategy Backtest Results", fontsize=18)

        # 1. ポートフォリオ価値の推移
        axes[0].plot(
            df_portfolio["Date"],
            df_portfolio["Portfolio_Value"],
            label="Portfolio Value (Strategy)",
            color="green",
            linewidth=2,
        )
        axes[0].axhline(
            y=df_portfolio["Portfolio_Value"].iloc[0],
            color="lightgray",
            linestyle="--",
            label="Initial Cash",
        )  # 初期資金の線を引く

        # 参照銘柄の株価（基準）をグラフに追加
        if reference_ticker_data is not None and not reference_ticker_data.empty:
            # reference_ticker_data に 'Close' 列があると仮定
            # ポートフォリオ価値と同じスケールにするために正規化する
            # 基準価格の初期値をポートフォリオの初期資金に合わせる
            ref_initial_close = reference_ticker_data["Close"].iloc[0]
            ref_scaled_value = (
                reference_ticker_data["Close"] / ref_initial_close
            ) * self.df_portfolio_history["Portfolio_Value"].iloc[0]
            axes[0].plot(
                reference_ticker_data["Date"],
                ref_scaled_value,
                label=f"Reference (Buy & Hold of {reference_ticker_data['Ticker'].iloc[0]})",
                color="orange",
                linestyle="--",
            )

        axes[0].set_title("Portfolio Value Trend (Leverage: 3x)", fontsize=14)
        axes[0].set_xlabel("Date", fontsize=12)
        axes[0].set_ylabel("Portfolio Value (JPY)", fontsize=12)
        axes[0].legend(fontsize=10)
        axes[0].grid(True, linestyle=":", alpha=0.7)
        axes[0].ticklabel_format(style="plain", axis="y")  # y軸の表記を通常の数値にする

        # 2. 株価と取引シグナル
        # 参照銘柄データが存在する場合のみ、その銘柄の株価とシグナルを表示
        if reference_ticker_data is not None and not reference_ticker_data.empty:
            axes[1].plot(
                reference_ticker_data["Date"],
                reference_ticker_data["Close"],
                label=f"{reference_ticker_data['Ticker'].iloc[0]} Close Price",
                color="gray",
                alpha=0.8,
            )

            # SMAラインを描画
            if f"SMA_{SHORT_MA_PERIOD}" in reference_ticker_data.columns:
                axes[1].plot(
                    reference_ticker_data["Date"],
                    reference_ticker_data[f"SMA_{SHORT_MA_PERIOD}"],
                    label=f"SMA {SHORT_MA_PERIOD}",
                    color="blue",
                    linewidth=1.5,
                )
            if f"SMA_{LONG_MA_PERIOD}" in reference_ticker_data.columns:
                axes[1].plot(
                    reference_ticker_data["Date"],
                    reference_ticker_data[f"SMA_{LONG_MA_PERIOD}"],
                    label=f"SMA {LONG_MA_PERIOD}",
                    color="red",
                    linewidth=1.5,
                )

            # Buy/Sell シグナルを描画
            buy_signals = df_trades[df_trades["Trade_Type"] == "BUY"]
            sell_signals = df_trades[df_trades["Trade_Type"] == "SELL"]

            # シグナルと参照銘柄のクローズ価格を結合し、表示
            # 同じ日の取引シグナルがある場合、その日のクローズ価格を使用
            # Buyシグナル
            if not buy_signals.empty:
                buy_plot_data = pd.merge(
                    buy_signals,
                    reference_ticker_data[["Date", "Close"]],
                    on="Date",
                    how="inner",
                )
                axes[1].scatter(
                    buy_plot_data["Date"],
                    buy_plot_data["Close"],
                    marker="^",
                    color="green",
                    s=100,
                    label="Buy Signal",
                    alpha=1,
                    zorder=5,
                )

            # Sellシグナル
            if not sell_signals.empty:
                sell_plot_data = pd.merge(
                    sell_signals,
                    reference_ticker_data[["Date", "Close"]],
                    on="Date",
                    how="inner",
                )
                axes[1].scatter(
                    sell_plot_data["Date"],
                    sell_plot_data["Close"],
                    marker="v",
                    color="red",
                    s=100,
                    label="Sell Signal",
                    alpha=1,
                    zorder=5,
                )

            axes[1].set_title(
                f"Stock Price and Signals ({reference_ticker_data['Ticker'].iloc[0]})",
                fontsize=14,
            )
            axes[1].set_xlabel("Date", fontsize=12)
            axes[1].set_ylabel("Stock Price (JPY)", fontsize=12)
            axes[1].legend(fontsize=10)
            axes[1].grid(True, linestyle=":", alpha=0.7)
            axes[1].ticklabel_format(
                style="plain", axis="y"
            )  # y軸の表記を通常の数値にする
        else:
            axes[1].set_title(
                "Stock Price and Signals (No reference data)", fontsize=14
            )
            axes[1].text(
                0.5,
                0.5,
                "No reference ticker data available for plotting signals.",
                horizontalalignment="center",
                verticalalignment="center",
                transform=axes[1].transAxes,
                fontsize=12,
            )
            axes[1].set_xlabel("Date", fontsize=12)
            axes[1].set_ylabel("Stock Price (JPY)", fontsize=12)

        plt.tight_layout(
            rect=[0, 0.03, 1, 0.96]
        )  # タイトルとサブプロットが重ならないように調整
        plt.savefig(file_name, dpi=300)

        plt.show()

        plt.close(fig)  # メモリ解放のために図を閉じる
