# stock_trading_bot/src/backtester.py

import pandas as pd

from .config import INITIAL_CASH, LEVERAGE_RATIO


class Backtester:
    def __init__(
        self,
        processed_dfs: dict,
        initial_cash: float = INITIAL_CASH,
        leverage_ratio: float = LEVERAGE_RATIO,
    ):
        self.processed_dfs = processed_dfs  # 全銘柄の処理済みデータフレーム
        self.initial_cash = initial_cash
        self.current_cash = initial_cash
        self.leverage_ratio = leverage_ratio

        # 銘柄ごとの保有株数と買値
        self.shares_held = {ticker: 0 for ticker in processed_dfs.keys()}
        self.bought_price = {ticker: 0 for ticker in processed_dfs.keys()}

        self.portfolio_values = []  # 各日のポートフォリオ価値を記録
        self.trade_history = []

        # 全銘柄のデータを統合した日付リスト (最も短い期間に合わせる)
        # 処理済みデータフレームが存在しない銘柄は除外
        valid_dfs = [
            df for df in processed_dfs.values() if df is not None and not df.empty
        ]
        if not valid_dfs:
            self.dates = []  # 有効なデータがなければ空リスト
            print("エラー: バックテスト可能な共通の日付範囲が見つかりません。")
            return

        # 共通の日付範囲を抽出
        common_dates = set(valid_dfs[0]["Date"].tolist())
        for df in valid_dfs[1:]:
            common_dates = common_dates.intersection(set(df["Date"].tolist()))

        self.dates = sorted(list(common_dates))

        if not self.dates:
            print("エラー: バックテスト可能な共通の日付範囲が見つかりません。")
            return

    def run_simulation(self):
        """
        売買シグナルに基づいて仮想取引シミュレーションを実行します。
        複数銘柄に対応し、レバレッジを考慮します。
        """
        if not self.processed_dfs or not self.dates:
            print("エラー: シミュレーション実行のためのデータがありません。")
            return None, None

        print("バックテスト実行中...")

        for i in range(len(self.dates)):
            current_date = self.dates[i]

            # その日のポートフォリオ価値を計算
            current_portfolio_value = self.current_cash
            for ticker, shares in self.shares_held.items():
                if shares > 0:
                    df = self.processed_dfs[ticker]
                    daily_data = df[df["Date"] == current_date]
                    if not daily_data.empty:
                        current_portfolio_value += shares * daily_data["Close"].iloc[0]

            self.portfolio_values.append(current_portfolio_value)

            # シグナルチェックと取引実行
            for ticker in self.processed_dfs.keys():
                df = self.processed_dfs[ticker]
                # 現在日のデータがあるかチェック (データが存在しない場合があるため)
                daily_data = df[df["Date"] == current_date]

                if daily_data.empty:
                    continue  # その日のデータがなければスキップ

                current_close = daily_data["Close"].iloc[0]
                trade_signal = daily_data["Trade_Signal"].iloc[0]

                # 買いシグナル (Trade_Signalが1)
                if trade_signal == 1:
                    # ポジションがない銘柄、または現在の現金で買える場合
                    # （今回の「半年で5倍」戦略では、全資産を最も有望な銘柄に投下するため、
                    # 既に他の銘柄を保有している場合は買わない、という簡易ロジックにします）
                    if (
                        self.current_cash > (INITIAL_CASH * 0.001)
                        and sum(self.shares_held.values()) == 0
                    ):  # ほぼ現金が残っていて、他に保有がない場合
                        investable_cash_with_leverage = (
                            self.current_cash * self.leverage_ratio
                        )
                        shares_to_buy = int(
                            investable_cash_with_leverage // current_close
                        )  # intにキャスト

                        if shares_to_buy > 0:
                            self.shares_held[ticker] = shares_to_buy
                            self.bought_price[ticker] = current_close
                            self.current_cash -= (
                                shares_to_buy * current_close
                            ) / self.leverage_ratio  # 実際に減る現金

                            self.trade_history.append(
                                {
                                    "Date": current_date,
                                    "Ticker": ticker,
                                    "Action": "BUY",
                                    "Price": current_close,
                                    "Shares": shares_to_buy,
                                    "Cash_Remaining": self.current_cash,
                                    "Current_Shares_in_Ticker": self.shares_held[
                                        ticker
                                    ],
                                    "Portfolio_Value": current_portfolio_value,  # その日のポートフォリオ価値を記録
                                }
                            )
                            # print(f"{current_date.strftime('%Y-%m-%d')}: {ticker} BUY {shares_to_buy}株 @ {current_close:.2f}円")

                # 売りシグナル (Trade_Signalが-1)
                elif trade_signal == -1:
                    if self.shares_held[ticker] > 0:  # 株を保有している場合のみ
                        cash_from_sale = self.shares_held[ticker] * current_close
                        self.current_cash += (
                            cash_from_sale / self.leverage_ratio
                        )  # レバレッジ考慮して現金に戻す

                        profit_loss = (
                            current_close - self.bought_price[ticker]
                        ) * self.shares_held[ticker]

                        self.trade_history.append(
                            {
                                "Date": current_date,
                                "Ticker": ticker,
                                "Action": "SELL",
                                "Price": current_close,
                                "Shares": self.shares_held[ticker],
                                "Cash_Remaining": self.current_cash,
                                "Current_Shares_in_Ticker": 0,
                                "Profit_Loss_on_Trade": profit_loss,
                                "Portfolio_Value": current_portfolio_value,  # その日のポートフォリオ価値を記録
                            }
                        )
                        # print(f"{current_date.strftime('%Y-%m-%d')}: {ticker} SELL {self.shares_held[ticker]}株 @ {current_close:.2f}円")
                        self.shares_held[ticker] = 0
                        self.bought_price[ticker] = 0

        # ポートフォリオ価値のSeriesを作成
        portfolio_df = pd.DataFrame(
            {"Date": self.dates, "Portfolio_Value": self.portfolio_values}
        )

        # 最終的なポートフォリオ価値を統合したデータフレームにマージ
        first_ticker = list(self.processed_dfs.keys())[0]
        final_df_for_plot = self.processed_dfs[first_ticker].copy()

        # マージ前にDate列の型を一致させることを強く推奨
        final_df_for_plot["Date"] = pd.to_datetime(final_df_for_plot["Date"])
        portfolio_df["Date"] = pd.to_datetime(portfolio_df["Date"])

        # merge前に、final_df_for_plot と portfolio_df の日付範囲が異なる場合があるため、
        # 共通の日付範囲で揃えるか、how='outer' などで対応することも検討
        final_df_for_plot = pd.merge(
            final_df_for_plot, portfolio_df, on="Date", how="left"
        )

        # 欠損値の補間 (Weekendなどデータがない日がある場合)
        # inplace=True を使わない推奨形式に修正
        final_df_for_plot["Portfolio_Value"] = final_df_for_plot[
            "Portfolio_Value"
        ].ffill()
        final_df_for_plot["Portfolio_Value"] = final_df_for_plot[
            "Portfolio_Value"
        ].bfill()
        final_df_for_plot["Portfolio_Value"] = final_df_for_plot[
            "Portfolio_Value"
        ].fillna(self.initial_cash)

        print("バックテスト完了。")
        return final_df_for_plot, pd.DataFrame(self.trade_history)

    def get_summary_results(self):
        """
        シミュレーションの最終結果を要約して返します。
        """
        if not self.portfolio_values:  # ポートフォリオ価値が計算されていない場合
            return {}

        final_portfolio_value = self.portfolio_values[-1]
        total_return_percentage = (
            (final_portfolio_value - self.initial_cash) / self.initial_cash
        ) * 100

        return {
            "initial_cash": self.initial_cash,
            "final_portfolio_value": final_portfolio_value,
            "total_return_percentage": total_return_percentage,
            "leverage_ratio": self.leverage_ratio,
        }
