# stock_trading_bot/src/config.py

import os
from datetime import datetime, timedelta

# --- 全体設定 ---
# プロジェクトのルートディレクトリを基準としたパス
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- データ設定 ---
# データ保存先CSVファイル名 (yfinanceで取得したデータを保存)
STOCK_DATA_FILE = os.path.join(BASE_DIR, "data", "stock_data.csv")

# yfinance で取得する銘柄と期間
# 例: '9984.T' はソフトバンクグループ (東証)
# 例: '^N225' は日経平均株価
# 例: 'AAPL' はApple (米国)
# 例: 'VOO' はS&P 500 ETF (米国)
TICKER_SYMBOL = "9984.T"  # 取得したい銘柄のティッカーシンボルを指定

# データ取得期間 (YYYY-MM-DD)
# 終了日は今日の1日前など、最新のデータが取れるように調整
END_DATE = datetime.now().strftime("%Y-%m-%d")
START_DATE = (datetime.now() - timedelta(days=365 * 3)).strftime(
    "%Y-%m-%d"
)  # 過去3年間のデータ

# --- 戦略設定 (ゴールデンクロス/デッドクロス) ---
SHORT_MA_PERIOD = 5  # 短期移動平均線の期間 (例: 5日)
LONG_MA_PERIOD = 25  # 長期移動平均線の期間 (例: 25日)

# --- バックテスト設定 ---
INITIAL_CASH = 1_000_000  # 初期保有現金 (例: 100万円)

# --- 出力設定 ---
# outputフォルダ内のExcelファイル名
OUTPUT_EXCEL_FILE = os.path.join(BASE_DIR, "output", "trading_simulation_results.xlsx")
