# stock_trading_bot/src/data_manager.py

import os

import numpy as np
import pandas as pd
import yfinance as yf

# ★ここを修正/追加★
from .config import STRATEGIES  # 修正

# ★ここまで修正/追加★


class DataManager:
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_data_from_yfinance(
        self, ticker: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        yfinanceから指定した銘柄の株価データを取得します。
        """
        print(
            f"yfinance から '{ticker}' のデータを取得中 ({start_date} から {end_date})..."
        )
        try:
            df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
            if df.empty:
                print(f"警告: '{ticker}' のデータが取得できませんでした。")
                return pd.DataFrame()

            df.reset_index(inplace=True)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)

            # 列名がMultiIndexの場合、フラット化する
            if isinstance(df.columns, pd.MultiIndex):
                # 2つのレベルを持つMultiIndexを想定し、内側のレベル（Close, Openなど）を列名にする
                df.columns = df.columns.get_level_values(
                    0
                )  # これが 'Close', 'High', etc. になることを期待
                print(
                    f"デバッグ: MultiIndex列をフラット化しました。新しい列: {df.columns.tolist()}"
                )

            # 最終的に必要な列だけを確実に取得
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            current_cols = df.columns.tolist()
            if not all(col in current_cols for col in required_cols):
                print(
                    f"エラー: 必要な列 ({required_cols}) の一部または全てがデータフレームにありません。現在の列: {current_cols}"
                )
                return pd.DataFrame()

            return df[required_cols]

        except Exception as e:
            print(f"エラー: '{ticker}' のデータ取得中に問題が発生しました: {e}")
            return pd.DataFrame()

    def fetch_multiple_data_from_yfinance(
        self, tickers: list, start_date: str, end_date: str
    ) -> dict:
        """
        複数の銘柄の株価データをyfinanceから取得し、CSVに保存します。
        """
        all_dfs = {}
        for ticker in tickers:
            file_path = os.path.join(self.data_dir, f"{ticker}.csv")
            df = self.fetch_data_from_yfinance(ticker, start_date, end_date)

            if not df.empty:
                df.reset_index(inplace=True)
                df.to_csv(file_path, index=False)
                print(
                    f"'{ticker}' のデータ取得完了。CSVファイルに保存します: {file_path}"
                )
                df.set_index("Date", inplace=True)
                all_dfs[ticker] = df
            else:
                all_dfs[ticker] = pd.DataFrame()
        return all_dfs

    def load_data_from_csv(self, ticker: str) -> pd.DataFrame:
        """
        CSVファイルから株価データをロードします。
        """
        file_path = os.path.join(self.data_dir, f"{ticker}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
            df.sort_index(inplace=True)
            return df
        else:
            print(f"エラー: CSVファイルが見つかりません: {file_path}")
            return pd.DataFrame()

    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データフレームに短期および長期移動平均線を追加します。
        """
        if df.empty:
            print(
                "警告: calculate_moving_averages に空のデータフレームが渡されました。"
            )
            return None

        df_copy = df.copy()
        sma_short_col = f"SMA_{STRATEGIES['SMA_Strategy']['short_ma']}"  # 修正
        sma_long_col = f"SMA_{STRATEGIES['SMA_Strategy']['long_ma']}"  # 修正

        print(
            f"\n--- MA計算デバッグ: DataFrameサイズ={len(df_copy)}, 列={df_copy.columns.tolist()} ---"
        )
        print(
            f"MA計算対象のデータ期間: {df_copy.index.min().strftime('%Y-%m-%d')} - {df_copy.index.max().strftime('%Y-%m-%d')}"
        )
        print(f"Close列の最初の5行:\n{df_copy['Close'].head()}")

        # 計算を実行
        df_copy[sma_short_col] = (
            df_copy["Close"]
            .rolling(window=STRATEGIES["SMA_Strategy"]["short_ma"], min_periods=1)
            .mean()  # 修正
        )
        df_copy[sma_long_col] = (
            df_copy["Close"]
            .rolling(window=STRATEGIES["SMA_Strategy"]["long_ma"], min_periods=1)
            .mean()  # 修正
        )

        print(
            f"MA計算後デバッグ: DataFrameサイズ={len(df_copy)}, 新しい列={df_copy.columns.tolist()}"
        )

        cols_to_check = []

        if (
            sma_short_col in df_copy.columns
            and not df_copy[sma_short_col].isnull().all()
        ):
            cols_to_check.append(sma_short_col)
        else:
            print(
                f"警告: SMA列 '{sma_short_col}' がデータフレームに作成されないか、全てNaNです。このSMA列はdropnaの対象外とします。"
            )

        if sma_long_col in df_copy.columns and not df_copy[sma_long_col].isnull().all():
            cols_to_check.append(sma_long_col)
        else:
            print(
                f"警告: SMA列 '{sma_long_col}' がデータフレームに作成されないか、全てNaNです。このSMA列はdropnaの対象外とします。"
            )

        if not cols_to_check:
            print(
                "警告: 短期および長期移動平均線のいずれも有効なデータを含みません。計算をスキップしNoneを返します。"
            )
            return None

        print(f"dropna対象の列: {cols_to_check}")
        df_copy.dropna(subset=cols_to_check, inplace=True)

        if df_copy.empty:
            print(
                "警告: 移動平均線計算後にデータフレームが空になりました。原因: NaNが多い。"
            )
            return None

        print(
            f"MA計算とdropna後デバッグ: DataFrameサイズ={len(df_copy)}, 列={df_copy.columns.tolist()} ---"
        )
        return df_copy

    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データフレームにRSI (Relative Strength Index) を追加します。
        """
        if df.empty:
            print("警告: calculate_rsi に空のデータフレームが渡されました。")
            return None

        df_copy = df.copy()

        print(
            f"\n--- RSI計算デバッグ: DataFrameサイズ={len(df_copy)}, 列={df_copy.columns.tolist()} ---"
        )
        print(
            f"RSI計算対象のデータ期間: {df_copy.index.min().strftime('%Y-%m-%d')} - {df_copy.index.max().strftime('%Y-%m-%d')}"
        )
        print(f"Close列の最初の5行:\n{df_copy['Close'].head()}")

        delta = df_copy["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # ここで RSI_PERIOD が定義されていないというエラーが出ていました
        avg_gain = gain.rolling(
            window=STRATEGIES["RSI_Strategy"]["rsi_period"], min_periods=1
        ).mean()  # 修正
        avg_loss = loss.rolling(
            window=STRATEGIES["RSI_Strategy"]["rsi_period"], min_periods=1
        ).mean()  # 修正

        rs = avg_gain / avg_loss.replace(0, np.nan)
        df_copy["RSI"] = 100 - (100 / (1 + rs))

        print(
            f"RSI計算後デバッグ: DataFrameサイズ={len(df_copy)}, 新しい列={df_copy.columns.tolist()}"
        )
        if "RSI" in df_copy.columns:
            print(f"RSIのNaN数: {df_copy['RSI'].isnull().sum()}")

        if "RSI" not in df_copy.columns or df_copy["RSI"].isnull().all():
            print(
                "警告: RSI列がデータフレームに作成されないか、全てNaNです。計算をスキップします。"
            )
            return None

        df_copy.dropna(subset=["RSI"], inplace=True)
        if df_copy.empty:
            print("警告: RSI計算後にデータフレームが空になりました。原因: NaNが多い。")
            return None

        print(
            f"RSI計算とdropna後デバッグ: DataFrameサイズ={len(df_copy)}, 列={df_copy.columns.tolist()} ---"
        )
        return df_copy
