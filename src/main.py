# stock_trading_bot/src/main.py

import os

from .backtester import Backtester
from .config import END_DATE, INITIAL_CASH, START_DATE, STOCK_DATA_FILE, TICKER_SYMBOL
from .data_manager import DataManager
from .report_generator import ReportGenerator
from .strategy_manager import StrategyManager
from .visualizer import Visualizer


def main():
    """
    株価自動取引シミュレーションのメイン実行関数です。
    """
    print("--- 株価自動取引シミュレーションを開始します ---")

    # 1. データ準備 (実データ取得)
    # dataフォルダが存在しない場合は作成
    os.makedirs(os.path.dirname(STOCK_DATA_FILE), exist_ok=True)

    data_manager = DataManager()

    # yfinance からデータを取得し、CSVに保存
    df_data = data_manager.fetch_data_from_yfinance(TICKER_SYMBOL, START_DATE, END_DATE)

    if df_data is None:
        print("データ取得に失敗しました。終了します。")
        return

    # 2. 移動平均線の計算
    df_processed = data_manager.calculate_moving_averages()
    if df_processed is None:
        print("移動平均線の計算に失敗しました。終了します。")
        return

    # 3. 戦略マネージャーの初期化とシグナル生成
    strategy_manager = StrategyManager(df_processed)
    df_signals = strategy_manager.generate_golden_dead_cross_signals()
    if df_signals is None:
        print("売買シグナル生成に失敗しました。終了します。")
        return

    # 4. バックテスターの初期化とシミュレーション実行
    backtester = Backtester(df_signals, initial_cash=INITIAL_CASH)
    df_portfolio, df_trades = backtester.run_simulation()
    if df_portfolio is None or df_trades is None:
        print("バックテスト実行に失敗しました。終了します。")
        return

    summary_results = backtester.get_summary_results()

    print("\n--- シミュレーション結果の概要 ---")
    print(f"対象銘柄: {TICKER_SYMBOL}")
    print(f"データ期間: {START_DATE} から {END_DATE}")
    print(f"初期資産: {summary_results['initial_cash']:,.0f} 円")
    print(f"最終資産: {summary_results['final_portfolio_value']:,.0f} 円")
    print(f"総リターン: {summary_results['total_return_percentage']:.2f}%")
    print(
        f"（もし最初から最後まで保有していた場合のリターン: {summary_results['buy_and_hold_return_percentage']:.2f}%）"
    )

    # 5. 可視化
    visualizer = Visualizer(df_portfolio)
    visualizer.plot_results(summary_results)

    # 6. レポート生成 (Excel出力)
    report_generator = ReportGenerator()
    report_generator.generate_excel_report(df_portfolio, df_trades, summary_results)

    print("\n--- シミュレーションが完了しました ---")


if __name__ == "__main__":
    main()
