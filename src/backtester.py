# stock_trading_bot/src/backtester.py

import pandas as pd

from .config import INITIAL_CASH


class Backtester:
    def __init__(self, df: pd.DataFrame, initial_cash: float = INITIAL_CASH):
        self.df = df.copy()
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.shares = 0
        self.portfolio_values = []
        self.trade_history = []

    def run_simulation(self):
        """
        売買シグナルに基づいて仮想取引シミュレーションを実行します。
        """
        if self.df is None or self.df.empty:
            print("エラー: シミュレーション実行のためのデータがありません。")
            return None, None

        print("バックテスト実行中...")
        # 最初のポートフォリオ価値を記録
        self.portfolio_values.append(self.cash + self.shares * self.df["Close"].iloc[0])

        for i in range(1, len(self.df)):
            current_date = self.df["Date"].iloc[i]
            current_close = self.df["Close"].iloc[i]
            trade_signal = self.df["Trade_Signal"].iloc[i]

            # 購入シグナル (Trade_Signalが1)
            if trade_signal == 1:
                if self.cash > 0:  # 現金がある場合のみ
                    # 買いは今日の終値で行うと仮定
                    shares_to_buy = self.cash // current_close
                    if shares_to_buy > 0:
                        self.shares += shares_to_buy
                        self.cash -= shares_to_buy * current_close
                        self.trade_history.append(
                            {
                                "Date": current_date,
                                "Action": "BUY",
                                "Price": current_close,
                                "Shares": int(shares_to_buy),
                                "Cash_Remaining": self.cash,
                                "Current_Shares": self.shares,
                                "Portfolio_Value": self.cash
                                + self.shares * current_close,
                            }
                        )
                        # print(f"{current_date.strftime('%Y-%m-%d')}: BUY {int(shares_to_buy)}株 @ {current_close:.2f}円")

            # 売却シグナル (Trade_Signalが-1)
            elif trade_signal == -1:
                if self.shares > 0:  # 株を保有している場合のみ
                    # 売りは今日の終値で行うと仮定
                    cash_from_sale = self.shares * current_close
                    self.cash += cash_from_sale
                    self.trade_history.append(
                        {
                            "Date": current_date,
                            "Action": "SELL",
                            "Price": current_close,
                            "Shares": int(self.shares),  # 売却した株数
                            "Cash_Remaining": self.cash,
                            "Current_Shares": 0,  # 全て売却
                            "Portfolio_Value": self.cash,  # 株式は0なので現金のみ
                        }
                    )
                    # print(f"{current_date.strftime('%Y-%m-%d')}: SELL {int(self.shares)}株 @ {current_close:.2f}円")
                    self.shares = 0

            # その日のポートフォリオ価値を記録
            self.portfolio_values.append(self.cash + self.shares * current_close)

        self.df["Portfolio_Value"] = pd.Series(
            self.portfolio_values[: len(self.df)]
        )  # サイズを合わせる

        print("バックテスト完了。")
        return self.df, pd.DataFrame(self.trade_history)

    def get_summary_results(self):
        """
        シミュレーションの最終結果を要約して返します。
        """
        if self.df is None or self.df.empty:
            return {}

        final_portfolio_value = self.portfolio_values[-1]
        total_return_percentage = (
            (final_portfolio_value - self.initial_cash) / self.initial_cash
        ) * 100

        # 比較用: ずっと保有していた場合の価値
        buy_and_hold_value = self.initial_cash * (
            self.df["Close"].iloc[-1] / self.df["Close"].iloc[0]
        )
        buy_and_hold_return_percentage = (
            (buy_and_hold_value - self.initial_cash) / self.initial_cash
        ) * 100

        return {
            "initial_cash": self.initial_cash,
            "final_portfolio_value": final_portfolio_value,
            "total_return_percentage": total_return_percentage,
            "buy_and_hold_return_percentage": buy_and_hold_return_percentage,
        }
