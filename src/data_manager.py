# stock_trading_bot/src/data_manager.py

import os

import pandas as pd
import yfinance as yf

# ここを修正: RSI_PERIODを追加
from .config import LONG_MA_PERIOD, RSI_PERIOD, SHORT_MA_PERIOD, STOCK_DATA_FILE


class DataManager:
    def __init__(self, file_path=STOCK_DATA_FILE):
        self.file_path = file_path
        self.df = None

    def load_data_from_csv(self, ticker_symbol: str = None):
        """
        CSVファイルから特定の銘柄データを読み込み、前処理を行います。
        ticker_symbolが指定された場合は、'data/{ticker_symbol}.csv'から読み込む。
        指定されない場合は、デフォルトのSTOCK_DATA_FILEから読み込む。
        """
        target_file_path = (
            os.path.join(os.path.dirname(self.file_path), f"{ticker_symbol}.csv")
            if ticker_symbol
            else self.file_path
        )

        print(f"データ読み込み中: {target_file_path}")
        try:
            df = pd.read_csv(target_file_path, parse_dates=["Date"])
            df = df.sort_values(by="Date").reset_index(drop=True)

            required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
            if not all(col in df.columns for col in required_columns):
                missing_cols = [
                    col for col in required_columns if col not in df.columns
                ]
                raise ValueError(
                    f"CSVファイルに必要な列が不足しています: {', '.join(missing_cols)}"
                )

            self.df = df
            print("データ読み込み完了。")
            return self.df
        except FileNotFoundError:
            print(
                f"エラー: 指定されたCSVファイル '{target_file_path}' が見つかりません。"
            )
            return None
        except Exception as e:
            print(f"データの読み込み中にエラーが発生しました: {e}")
            return None

    def fetch_multiple_data_from_yfinance(
        self, tickers: list, start_date: str, end_date: str
    ):
        """
        yfinance を使用して複数の銘柄の株価データを取得します。
        取得後、各銘柄のCSVファイルとして保存し、データフレームの辞書を返します。
        """
        all_dfs = {}
        data_dir = os.path.dirname(self.file_path)  # dataフォルダのパスを取得
        os.makedirs(data_dir, exist_ok=True)  # dataフォルダが存在しない場合は作成

        for ticker in tickers:
            ticker_file_path = os.path.join(data_dir, f"{ticker}.csv")
            print(
                f"yfinance から '{ticker}' のデータを取得中 ({start_date} から {end_date})..."
            )
            try:
                data = yf.download(
                    ticker, start=start_date, end=end_date, auto_adjust=True
                )

                if data.empty:
                    print(
                        f"警告: '{ticker}' のデータが取得できませんでした。ティッカーシンボルまたは期間を確認してください。"
                    )
                    continue

                # 列名を標準的な形式に変換
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [
                        "_".join(col).strip() for col in data.columns.values
                    ]

                new_columns = []
                for col in data.columns:
                    if col.endswith(
                        f"_{ticker}"
                    ):  # ティッカーシンボルが列名に付加されている場合
                        new_columns.append(col[: -len(f"_{ticker}")])
                    else:
                        new_columns.append(col)
                data.columns = new_columns

                if "Close" not in data.columns:
                    print(
                        f"エラー: '{ticker}' の 'Close' 列がデータフレームに見つかりません。取得された列: {data.columns.tolist()}"
                    )
                    continue

                data = data[["Open", "High", "Low", "Close", "Volume"]]
                data.reset_index(inplace=True)
                data["Date"] = data["Date"].dt.normalize()  # 時刻情報を削除

                all_dfs[ticker] = data
                print(
                    f"'{ticker}' のデータ取得完了。CSVファイルに保存します: {ticker_file_path}"
                )
                data.to_csv(ticker_file_path, index=False)

            except Exception as e:
                print(
                    f"yfinance から '{ticker}' のデータ取得中にエラーが発生しました: {e}"
                )
                continue

        # 複数銘柄のデータを一括で返す
        return all_dfs

    def calculate_moving_averages(self, df: pd.DataFrame):
        """
        終値データから短期・長期移動平均線を計算します。
        データフレームを引数として受け取るように変更。
        """
        if df is None or df.empty:
            print("エラー: 移動平均線計算のためのデータがありません。")
            return None

        # オリジナルのデータフレームを保護するためコピー
        df_copy = df.copy()

        # Close 列が存在するか確認
        if "Close" not in df_copy.columns:
            print("エラー: 'Close' 列が見つかりません。データ形式を確認してください。")
            return None

        # print("移動平均線計算中...") # 個別の計算では出力が多すぎるので削除
        df_copy[f"SMA_{SHORT_MA_PERIOD}"] = (
            df_copy["Close"].rolling(window=SHORT_MA_PERIOD).mean()
        )
        df_copy[f"SMA_{LONG_MA_PERIOD}"] = (
            df_copy["Close"].rolling(window=LONG_MA_PERIOD).mean()
        )

        # NaN（計算できない初期値）を除外
        df_copy.dropna(inplace=True)
        df_copy.reset_index(drop=True, inplace=True)

        if df_copy.empty:
            # print("エラー: 移動平均線の計算後、データが残っていません。期間が長すぎる可能性があります。") # 出力抑制
            return None

        return df_copy

    def calculate_rsi(self, df: pd.DataFrame):
        """
        RSI (Relative Strength Index) を計算します。
        """
        if df is None or df.empty or "Close" not in df.columns:
            return None

        df_copy = df.copy()

        delta = df_copy["Close"].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=RSI_PERIOD).mean()
        avg_loss = loss.rolling(window=RSI_PERIOD).mean()

        rs = avg_gain / avg_loss
        df_copy["RSI"] = 100 - (100 / (1 + rs))
        df_copy.dropna(inplace=True)
        df_copy.reset_index(drop=True, inplace=True)
        return df_copy
