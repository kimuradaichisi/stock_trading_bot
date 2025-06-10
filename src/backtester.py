# stock_trading_bot/src/backtester.py

import pandas as pd

from .config import INITIAL_CASH, LEVERAGE_RATIO


class Backtester:
    def __init__(
        self,
        processed_dfs: dict,
        strategy_name: str,  # 新しく追加
        initial_cash: float = INITIAL_CASH,
        leverage_ratio: float = LEVERAGE_RATIO,
    ):
        self.processed_dfs = (
            processed_dfs  # 各銘柄の処理済みデータフレーム (シグナル付き)
        )
        self.strategy_name = strategy_name  # 戦略名を保持
        self.initial_cash = initial_cash
        self.current_cash = initial_cash
        self.leverage_ratio = leverage_ratio

        # 銘柄ごとの保有株数と買値
        self.shares_held = {ticker: 0 for ticker in processed_dfs.keys()}
        self.bought_price = {ticker: 0 for ticker in processed_dfs.keys()}

        self.trade_history = []  # 取引履歴を記録

        # 全銘柄のデータを統合した日付リスト (最も短い期間に合わせる)
        # 処理済みデータフレームが存在しない銘柄は除外
        valid_dfs = [
            df for df in processed_dfs.values() if df is not None and not df.empty
        ]

        if not valid_dfs:
            print("エラー: バックテストのための有効なデータフレームが見つかりません。")
            self.dates = []
            return

        # 各データフレームの 'Date' 列がインデックスであることを確認し、DatetimeIndexに変換
        for df in valid_dfs:
            if "Date" not in df.columns:
                print(
                    "警告: バックテスター初期化: データフレームに 'Date' 列が見つかりません。"
                )
                self.dates = []
                return

            # 'Date' 列が既にDatetime型でない場合のみ変換
            if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
                df["Date"] = pd.to_datetime(df["Date"])

            # 'Date' 列がインデックスでない場合のみ設定
            if not isinstance(df.index, pd.DatetimeIndex) or "Date" in df.index.name:
                df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)  # インデックスでソートされていることを確認

        # 全ての有効なDFに存在する日付の共通集合を取得
        if valid_dfs:
            # インデックスの日付を正規化してセットにし、共通部分を抽出
            common_dates_set = set(
                valid_dfs[0].index.normalize().tolist()
            )  # .index を使用
            for df in valid_dfs[1:]:
                common_dates_set = common_dates_set.intersection(
                    set(df.index.normalize().tolist())
                )  # .index を使用
            self.dates = sorted(list(common_dates_set))
        else:
            self.dates = []

        if not self.dates:
            print("エラー: バックテスト可能な共通の日付範囲が見つかりません。")
            return

        # ポートフォリオ履歴DataFrameを初期化
        self.portfolio_history_df = pd.DataFrame(
            columns=["Date", "Portfolio_Value", "Strategy"]
        )  # 'Strategy' 列を追加

    def _get_current_portfolio_value(self, current_prices: dict) -> float:
        """現在のポートフォリオの総価値を計算します。

        Args:
            current_prices (dict): 各銘柄の現在価格を格納した辞書。

        Returns:
            float: 現在のポートフォリオの総価値。
        """
        holding_value = sum(
            self.shares_held[ticker] * current_prices.get(ticker, 0)
            for ticker in self.shares_held
        )
        return self.current_cash + holding_value

    def run_simulation(self):
        """シミュレーションを実行し、ポートフォリオの推移と取引履歴を記録します。

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: ポートフォリオ履歴DataFrameと取引履歴DataFrame。
        """
        if not self.dates:
            print("エラー: シミュレーション実行のためのデータがありません。")
            return None, None  # Noneを返すことで、main.pyでエラーを検知させる

        print(
            f"バックテスト期間: {self.dates[0].strftime('%Y-%m-%d')} から {self.dates[-1].strftime('%Y-%m-%d')}"
        )

        portfolio_records = []  # ポートフォリオ履歴を一時的に保持するリスト

        for i, current_date in enumerate(self.dates):
            current_prices = {}
            current_signals = {}
            has_data_for_today = True

            for ticker, df in self.processed_dfs.items():
                # その日のデータをインデックス（日付）で取得
                # current_date.normalize() は日付部分のみを比較するために使用
                # .loc[] を使ってインデックスベースでアクセス
                daily_data = df.loc[
                    df.index.normalize() == current_date.normalize()
                ]  # .index を使用

                if daily_data.empty:
                    has_data_for_today = False
                    break

                current_prices[ticker] = daily_data["Close"].iloc[0]
                current_signals[ticker] = daily_data["Trade_Signal"].iloc[0]

            if not has_data_for_today:
                # print(f"警告: {current_date.strftime('%Y-%m-%d')} のデータが一部銘柄で欠損しています。この日をスキップします。")
                continue  # この日のデータが一部の銘柄で欠損している場合はスキップ

            # 各銘柄に対してトレード戦略を適用
            for ticker in self.processed_dfs.keys():
                signal = current_signals.get(ticker, 0)
                current_price = current_prices.get(ticker, 0)

                if current_price == 0:  # 価格データがない場合はスキップ
                    continue

                if signal == 1:  # 買いシグナル
                    # レバレッジを考慮して、現金のLEVERAGE_RATIO倍まで購入可能とみなす
                    # ただし、実際に買えるのは現金分のみ。信用取引口座が別途必要。
                    # ここでは、現金のLEVERAGE_RATIO倍までという「余裕」を持って購入できると仮定

                    # 全銘柄が均等にレバレッジを考慮した資金を割り振る (簡易的な配分)
                    num_tickers = len(self.processed_dfs)
                    if num_tickers == 0:  # 銘柄がない場合はスキップ
                        continue

                    # 資金を各銘柄に均等配分（単純化のため）
                    # 実際に使用可能な「購入枠」
                    available_buying_power = (
                        self.current_cash * self.leverage_ratio
                    ) / num_tickers

                    if available_buying_power > 0:
                        # 買える株数
                        shares_to_buy = int(available_buying_power // current_price)

                        if shares_to_buy > 0:
                            # 実際の購入に必要な現金
                            cost = shares_to_buy * current_price
                            # 購入可能であれば、現金から支払い、保有株数を増やす
                            if (
                                self.current_cash >= cost
                            ):  # 現金が不足していれば買わない
                                self.current_cash -= cost
                                self.shares_held[ticker] += shares_to_buy
                                self.bought_price[ticker] = current_price  # 買値を記録
                                self.trade_history.append(
                                    {
                                        "Date": current_date,
                                        "Ticker": ticker,
                                        "Trade_Type": "BUY",
                                        "Price": current_price,
                                        "Shares": shares_to_buy,
                                        "Cash_Left": self.current_cash,
                                        "Portfolio_Value": self._get_current_portfolio_value(
                                            current_prices
                                        ),
                                    }
                                )

                elif signal == -1:  # 売りシグナル
                    if self.shares_held[ticker] > 0:
                        # 全て売却
                        revenue = self.shares_held[ticker] * current_price
                        self.current_cash += revenue

                        # 利益計算 (簡易的)
                        profit = (
                            (current_price - self.bought_price[ticker])
                            * self.shares_held[ticker]
                            if self.bought_price[ticker] > 0
                            else 0
                        )

                        self.shares_held[ticker] = 0
                        self.bought_price[ticker] = 0  # 買値をリセット
                        self.trade_history.append(
                            {
                                "Date": current_date,
                                "Ticker": ticker,
                                "Trade_Type": "SELL",
                                "Price": current_price,
                                "Shares": self.shares_held[ticker],  # 売却後の保有数
                                "Cash_Left": self.current_cash,
                                "Portfolio_Value": self._get_current_portfolio_value(
                                    current_prices
                                ),
                            }
                        )

            # 各日のポートフォリオ価値を記録
            current_portfolio_value = self._get_current_portfolio_value(current_prices)
            # 一時的なリストにレコードを追加
            portfolio_records.append(
                {
                    "Date": current_date,
                    "Portfolio_Value": current_portfolio_value,
                    "Strategy": self.strategy_name,  # 戦略名を追加
                }
            )
        # ループ終了後、一度にDataFrameに変換
        self.portfolio_history_df = pd.DataFrame(portfolio_records)

        # 最終日のポートフォリオ価値を更新
        if not self.portfolio_history_df.empty:
            final_portfolio_value = self.portfolio_history_df["Portfolio_Value"].iloc[
                -1
            ]
        else:
            final_portfolio_value = self.initial_cash

        # 取引履歴とポートフォリオ履歴をDataFrameに変換
        df_trade_history = pd.DataFrame(self.trade_history)

        # ★ここから追加★ df_trade_historyが空の場合の処理
        if df_trade_history.empty:
            print(
                "警告: 取引履歴が空です。'Trade_Type'カラムを含む取引が生成されませんでした。"
            )
            # Visualizerが期待するカラムを持つ空のDataFrameを作成
            df_trade_history = pd.DataFrame(
                columns=[
                    "Date",
                    "Ticker",
                    "Trade_Type",
                    "Price",
                    "Shares",
                    "Cash_Left",
                    "Portfolio_Value",
                ]
            )
        # ★ここまで追加★

        # df_portfolio_historyは、ウォークフォワード用に各期間の履歴を保持
        # 最終的にmain.pyで連結されることを想定

        return self.portfolio_history_df, df_trade_history

    def get_summary_results(self) -> dict:
        """シミュレーションの最終結果を要約して返します。

        Returns:
            dict: シミュレーションの要約結果を含む辞書。
        """
        # 最終ポートフォリオ価値
        if not self.portfolio_history_df.empty:
            final_portfolio_value = self.portfolio_history_df["Portfolio_Value"].iloc[
                -1
            ]
        else:
            final_portfolio_value = self.initial_cash

        # 総リターン率
        total_return_percentage = (
            ((final_portfolio_value - self.initial_cash) / self.initial_cash) * 100
            if self.initial_cash != 0
            else 0
        )

        return {
            "strategy_name": self.strategy_name,  # 戦略名を追加
            "initial_cash": self.initial_cash,
            "final_portfolio_value": final_portfolio_value,
            "total_return_percentage": total_return_percentage,
            "leverage_ratio": self.leverage_ratio,
        }
