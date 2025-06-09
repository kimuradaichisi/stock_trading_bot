# stock_trading_bot/src/data_manager.py

import pandas as pd
import yfinance as yf

from .config import LONG_MA_PERIOD, SHORT_MA_PERIOD, STOCK_DATA_FILE


class DataManager:
    def __init__(self, file_path=STOCK_DATA_FILE):
        self.file_path = file_path
        self.df = None

    def load_data_from_csv(self):
        """
        CSVファイルから株価データを読み込み、前処理を行います。
        (既存のCSVファイルからの読み込み用)
        """
        print(f"データ読み込み中: {self.file_path}")
        try:
            df = pd.read_csv(self.file_path, parse_dates=["Date"])
            df = df.sort_values(by="Date").reset_index(drop=True)

            # 必要な列が存在するかチェック
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
                f"エラー: 指定されたCSVファイル '{self.file_path}' が見つかりません。"
            )
            return None
        except Exception as e:
            print(f"データの読み込み中にエラーが発生しました: {e}")
            return None

    def fetch_data_from_yfinance(self, ticker: str, start_date: str, end_date: str):
        """
        yfinance を使用してインターネットから株価データを取得します。
        取得後、標準のCSV形式に合わせて整形し、CSVファイルに保存します。
        """
        print(
            f"yfinance から '{ticker}' のデータを取得中 ({start_date} から {end_date})..."
        )
        try:
            # yfinance でデータを取得
            # auto_adjust=Trueで調整後終値が自動的にClose列に格納されるようにする
            data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)

            if data.empty:
                print(
                    f"警告: '{ticker}' のデータが取得できませんでした。ティッカーシンボルまたは期間を確認してください。"
                )
                return None

            # 列名を標準的な形式に変換
            # yfinanceがMultiIndexを返す場合があるため、まずフラットにする
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = ["_".join(col).strip() for col in data.columns.values]

            # その後、必要な列名を正規化 (例: 'Close_9984.T' -> 'Close')
            new_columns = []
            for col in data.columns:
                # ティッカーシンボルが列名に付加されている場合があるので除去
                # 例: 'Close_9984.T' -> 'Close'
                if col.endswith(f"_{ticker}"):
                    new_columns.append(
                        col[: -len(f"_{ticker}")]
                    )  # 末尾の '_9984.T' を除去
                else:
                    new_columns.append(col)
            data.columns = new_columns

            # 'Close' 列が最終的に存在するか確認
            if "Close" not in data.columns:
                print("エラー: 'Close' 列がデータフレームに見つかりません。")
                print(f"取得された列: {data.columns.tolist()}")
                return None

            # 必要な列のみを選択し、'Date' を列として追加 (yfinanceはインデックスとして日付を持つため)
            data = data[["Open", "High", "Low", "Close", "Volume"]]
            data.reset_index(inplace=True)
            data["Date"] = data["Date"].dt.normalize()  # 時刻情報を削除

            self.df = data
            print(
                f"'{ticker}' のデータ取得完了。CSVファイルに保存します: {self.file_path}"
            )
            self.df.to_csv(self.file_path, index=False)  # CSVファイルに保存
            return self.df
        except Exception as e:
            print(f"yfinance からのデータ取得中にエラーが発生しました: {e}")
            return None

    def calculate_moving_averages(self):
        """
        終値データから短期・長期移動平均線を計算します。
        """
        if self.df is None:
            print(
                "エラー: データがロードされていません。まず load_data_from_csv() または fetch_data_from_yfinance() を実行してください。"
            )
            return None

        print("移動平均線計算中...")
        # Close 列が存在するか確認
        if "Close" not in self.df.columns:
            print("エラー: 'Close' 列が見つかりません。データ形式を確認してください。")
            return None

        self.df[f"SMA_{SHORT_MA_PERIOD}"] = (
            self.df["Close"].rolling(window=SHORT_MA_PERIOD).mean()
        )
        self.df[f"SMA_{LONG_MA_PERIOD}"] = (
            self.df["Close"].rolling(window=LONG_MA_PERIOD).mean()
        )

        # NaN（計算できない初期値）を除外
        self.df.dropna(inplace=True)
        self.df.reset_index(drop=True, inplace=True)

        if self.df.empty:
            print(
                "エラー: 移動平均線の計算後、データが残っていません。期間が長すぎる可能性があります。"
            )
            return None

        print("移動平均線計算完了。")
        return self.df
