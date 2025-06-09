# stock_trading_bot/src/config.py

# --- データ設定 ---
# 株価データを保存するファイルパス (各銘柄は別途CSVとして保存される)
STOCK_DATA_FILE = "data/stock_data.csv"
# バックテストを行う銘柄のティッカーシンボルリスト (例: 日本株なら '9984.T', 米国株なら 'AAPL')
TICKER_SYMBOLS = [
    "NVDA"
]  # 例: NVIDIAのティッカー。複数設定する場合は ['AAPL', 'MSFT', 'NVDA'] のように記述。
# データ取得開始日 ('YYYY-MM-DD' 形式)
START_DATE = "2024-01-01"
# データ取得終了日 ('YYYY-MM-DD' 形式)
END_DATE = "2025-06-07"  # 最新の日付に調整してください (今日の日付から少し前が安全)

# --- 戦略設定 (移動平均線 - SMA) ---
# 短期移動平均線の期間
SHORT_MA_PERIOD = 5
# 長期移動平均線の期間
LONG_MA_PERIOD = 20

# --- 戦略設定 (RSI - Relative Strength Index) ---
# RSIの計算期間
RSI_PERIOD = 14
# RSIの買われすぎ閾値
RSI_OVERBOUGHT = 70
# RSIの売られすぎ閾値
RSI_OVERSOLD = 30

# --- バックテスト設定 ---
# 初期投資資金
INITIAL_CASH = 1_000_000  # 100万円
# 利用するレバレッジ倍率 (例: 1 はレバレッジなし、2 は2倍レバレッジ)
LEVERAGE_RATIO = 3  # 半年で資金を5倍にする戦略を想定し、高めのレバレッジを設定

# --- ウォークフォワード最適化設定 ---
# パラメータ最適化に使用する過去データの期間 (日数)
# 例: 180日 = 約半年分のデータで最適なMA期間などの組み合わせを見つける
OPTIMIZATION_WINDOW_DAYS = 180
# 最適化したパラメータを評価する期間 (日数)
# 例: 次の30日 = 1ヶ月分のデータで、見つけたパラメータがどのくらい機能するかをテストする
TEST_WINDOW_DAYS = 30
# 最適化ウィンドウをずらす間隔 (日数)
# 例: 30日 = 1ヶ月ごとにパラメータを再最適化し、次の1ヶ月をテストする
WALK_FORWARD_STEP_DAYS = 30

# 最適化するパラメータの探索範囲 (グリッドサーチ用)
# 短期移動平均線の期間の探索範囲 (開始, 終了+1, ステップ)
SMA_SHORT_RANGE = range(5, 26, 5)  # 例: 5, 10, 15, 20, 25
# 長期移動平均線の期間の探索範囲 (開始, 終了+1, ステップ)
SMA_LONG_RANGE = range(10, 61, 10)  # 例: 10, 20, 30, 40, 50, 60

# --- 出力設定 ---
# レポートファイル名
REPORT_FILE_NAME = "trading_simulation_results.xlsx"
# グラフファイル名
PLOT_FILE_NAME = "portfolio_and_signals.png"
