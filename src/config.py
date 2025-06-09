# stock_trading_bot/src/config.py

# --- データ設定 ---
# 株価データを保存するファイルパス (各銘柄は別途CSVとして保存される)
STOCK_DATA_FILE = "data/stock_data.csv"
# バックテストを行う銘柄のティッカーシンボルリスト (例: 日本株なら '9984.T', 米国株なら 'AAPL')
TICKER_SYMBOLS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "SPY",  # 例: 複数銘柄に分散
]
# データ取得開始日 ('YYYY-MM-DD' 形式)
START_DATE = "2015-01-01"  # より長い期間に設定
# データ取得終了日 ('YYYY-MM-DD' 形式)
END_DATE = "2025-06-07"  # 最新の日付に調整

# --- 戦略設定 (移動平均線 - SMA) ---
# 短期移動平均線の期間 (これは最適化範囲で上書きされるため、デフォルト値のようなもの)
SHORT_MA_PERIOD = 5
# 長期移動平均線の期間 (これも最適化範囲で上書きされるため、デフォルト値のようなもの)
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
INITIAL_CASH = 20_000_000  # 2,000万円に増額 (月10万円目標に対してより現実的に)
# 利用するレバレッジ倍率 (例: 1 はレバレッジなし、2 は2倍レバレッジ)
LEVERAGE_RATIO = 1.0  # レバレッジなしに設定 (リスクを大幅に低減)

# --- ウォークフォワード最適化設定 ---
# パラメータ最適化に使用する過去データの期間 (日数)
OPTIMIZATION_WINDOW_DAYS = 180
# 最適化したパラメータを評価する期間 (日数)
TEST_WINDOW_DAYS = 60
# 最適化ウィンドウをずらす間隔 (日数)
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
