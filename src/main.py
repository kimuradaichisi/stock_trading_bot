# stock_trading_bot/src/main.py

from datetime import timedelta

import pandas as pd

from .backtester import Backtester
from .config import (
    END_DATE,
    INITIAL_CASH,
    LEVERAGE_RATIO,
    LONG_MA_PERIOD,
    OPTIMIZATION_WINDOW_DAYS,
    PLOT_FILE_NAME,
    SHORT_MA_PERIOD,
    START_DATE,
    TEST_WINDOW_DAYS,
    TICKER_SYMBOLS,
    WALK_FORWARD_STEP_DAYS,
)
from .data_manager import DataManager
from .report_generator import ReportGenerator
from .strategy_manager import StrategyManager
from .visualizer import Visualizer


def main():
    """
    株価自動取引シミュレーションのメイン実行関数です。
    ウォークフォワード最適化に基づいた、日次更新を想定したシミュレーションを行います。
    """
    print("--- 株価自動取引シミュレーションを開始します ---")

    data_manager = DataManager()
    strategy_manager = StrategyManager()

    # 全期間の生データを一度取得・更新 (後でウォークフォワード用に分割)
    # config.START_DATE と config.END_DATE を使って全期間のデータを取得
    raw_dfs = data_manager.fetch_multiple_data_from_yfinance(
        TICKER_SYMBOLS, START_DATE, END_DATE
    )

    if not raw_dfs:
        print("データ取得に失敗しました。終了します。")
        return

    # ウォークフォワードシミュレーションの結果を保存するためのリスト
    all_walk_forward_results = []  # 各テスト期間のサマリー結果
    all_walk_forward_trades = pd.DataFrame()  # 全期間の統合された取引履歴
    all_walk_forward_portfolio_dfs = []  # 各テスト期間のポートフォリオ推移DF

    # 最初の最適化開始日を決定
    # 最も古いデータがある銘柄の最初のOPTIMIZATION_WINDOW_DAYS分のデータが必要
    # 有効なデータフレームのみを対象にする
    valid_dfs_for_min_max_date = [
        df for df in raw_dfs.values() if df is not None and not df.empty
    ]
    if not valid_dfs_for_min_max_date:
        print("有効なデータが見つかりませんでした。終了します。")
        return

    min_date = min(df["Date"].min() for df in valid_dfs_for_min_max_date)
    max_date = max(df["Date"].max() for df in valid_dfs_for_min_max_date)

    current_optimization_start_date = min_date

    # ウォークフォワードループ
    while True:
        # ウォークフォワードのウィンドウを定義
        optimization_end_date = current_optimization_start_date + timedelta(
            days=OPTIMIZATION_WINDOW_DAYS
        )
        test_start_date = (
            optimization_end_date  # テスト期間の開始日は最適化期間の終了日
        )
        test_end_date = test_start_date + timedelta(days=TEST_WINDOW_DAYS)

        # テスト期間が全データ期間を超過したら終了
        # データがない期間で最適化・テストを試みないようにする
        if (
            optimization_end_date > max_date or test_start_date >= test_end_date
        ):  # テスト期間が有効かどうかもチェック
            print("\nウォークフォワード最適化が全データ期間をカバーしました。")
            break

        print(
            f"\n--- ウォークフォワード期間: 最適化期間 [{current_optimization_start_date.strftime('%Y-%m-%d')} - {optimization_end_date.strftime('%Y-%m-%d')}] ---"
        )
        print(
            f"--- テスト期間: [{test_start_date.strftime('%Y-%m-%d')} - {test_end_date.strftime('%Y-%m-%d')}] ---"
        )

        # 各銘柄のデータを最適化期間とテスト期間に分割
        current_processed_dfs_for_optimization = {}
        current_processed_dfs_for_test = {}

        # 生データに対して一度MA/RSIを計算し、それを期間で区切る
        # これにより、最適化・テスト期間ごとに再度MA/RSIを計算する二重計算を防ぐ
        full_processed_dfs = {}
        for ticker, df in raw_dfs.items():
            if df is None or df.empty:
                continue

            df_ma = data_manager.calculate_moving_averages(df.copy())
            if df_ma is None:
                continue
            df_final = data_manager.calculate_rsi(df_ma)
            if df_final is None:
                continue

            # シグナル生成は、最適化後のパラメータでテスト期間に対してのみ実行するため、ここでは保留
            full_processed_dfs[ticker] = df_final

        for ticker, df_full_processed in full_processed_dfs.items():
            # 最適化期間のデータ
            opt_df = df_full_processed[
                (df_full_processed["Date"] >= current_optimization_start_date)
                & (df_full_processed["Date"] < optimization_end_date)
            ].copy()
            if not opt_df.empty:
                current_processed_dfs_for_optimization[ticker] = opt_df

            # テスト期間のデータ
            test_df = df_full_processed[
                (df_full_processed["Date"] >= test_start_date)
                & (df_full_processed["Date"] < test_end_date)
            ].copy()
            if not test_df.empty:
                current_processed_dfs_for_test[ticker] = test_df

        if (
            not current_processed_dfs_for_optimization
            or not current_processed_dfs_for_test
        ):
            print(
                "この期間の最適化またはテストデータが不足しています。次の期間へスキップします。"
            )
            current_optimization_start_date += timedelta(days=WALK_FORWARD_STEP_DAYS)
            continue

        # 最も有望な銘柄のデータを取得 (ここでは最適化期間の代表銘柄として最初の銘柄を使用)
        # より高度な戦略では、この期間で最もパフォーマンスが良かった銘柄を選ぶ、等の工夫が必要
        optimization_ticker = list(current_processed_dfs_for_optimization.keys())[0]
        df_for_optimization = current_processed_dfs_for_optimization[
            optimization_ticker
        ]

        # 1. パラメータ最適化 (最適化期間のデータを使用)
        # strategy_manager.optimize_strategy_parameters はあくまで簡易的なもの。
        # 本格的なバックテストロジック（バックテスタークラス）を呼び出して
        # 最適化を実行するような構造にするべきですが、ここでは簡略化しています。
        best_params = strategy_manager.optimize_strategy_parameters(df_for_optimization)

        if not best_params:
            print("パラメータ最適化に失敗しました。スキップします。")
            current_optimization_start_date += timedelta(days=WALK_FORWARD_STEP_DAYS)
            continue

        # 最適化されたパラメータを元に、戦略マネージャーのシグナルを生成し直す
        # config のグローバル変数を一時的に変更する (ベストプラクティスではないが簡略化のため)
        import src.config

        src.config.SHORT_MA_PERIOD = best_params.get("short_ma", SHORT_MA_PERIOD)
        src.config.LONG_MA_PERIOD = best_params.get("long_ma", LONG_MA_PERIOD)
        # 必要なら RSI_OVERBOUGHT, RSI_OVERSOLD も同様に設定

        processed_dfs_for_test_with_optimized_params = {}
        for ticker, df_test_raw in current_processed_dfs_for_test.items():
            # テスト期間のデータに、最適化されたパラメータでMAとRSIを再計算 (config変更後の値で)
            # 再計算は不要な場合があるが、パラメータ変更を反映させるために行っている
            # 既にfull_processed_dfsで計算済みだが、その時点のconfig値なので、ここで再計算が必要
            df_test_ma = data_manager.calculate_moving_averages(df_test_raw.copy())
            if df_test_ma is None:
                continue
            df_test_final = data_manager.calculate_rsi(df_test_ma)
            if df_test_final is None:
                continue

            # 最適化されたパラメータを反映したシグナルを生成
            df_test_signals = strategy_manager.generate_trading_signals(df_test_final)
            if df_test_signals is None:
                continue
            processed_dfs_for_test_with_optimized_params[ticker] = df_test_signals

        if not processed_dfs_for_test_with_optimized_params:
            print("テスト期間のデータ処理に失敗しました。スキップします。")
            current_optimization_start_date += timedelta(days=WALK_FORWARD_STEP_DAYS)
            continue

        # 2. テスト期間でバックテストを実行 (最適化されたパラメータを使用)
        # 各ウォークフォワード期間で初期資産をリセットして評価（簡易化のため）
        # 連続バックテストを行う場合は、前期間の最終資産を current_cash に引き継ぐ必要がある
        backtester = Backtester(
            processed_dfs_for_test_with_optimized_params,
            initial_cash=INITIAL_CASH,
            leverage_ratio=LEVERAGE_RATIO,
        )

        df_portfolio_current_test, df_trades_current_test = backtester.run_simulation()

        if df_portfolio_current_test is None or df_trades_current_test is None:
            print("バックテスト実行に失敗しました。スキップします。")
            current_optimization_start_date += timedelta(days=WALK_FORWARD_STEP_DAYS)
            continue

        summary_results_current_test = backtester.get_summary_results()

        # 結果を蓄積
        all_walk_forward_results.append(summary_results_current_test)
        all_walk_forward_trades = pd.concat(
            [all_walk_forward_trades, df_trades_current_test], ignore_index=True
        )
        all_walk_forward_portfolio_dfs.append(df_portfolio_current_test)

        # 次の最適化期間の開始日を設定
        current_optimization_start_date += timedelta(days=WALK_FORWARD_STEP_DAYS)

    print("\n--- ウォークフォワードシミュレーション完了 ---")

    if not all_walk_forward_results:
        print("実行可能なシミュレーション期間がありませんでした。")
        return

    # 全期間を通した統合されたポートフォリオ価値を計算し、可視化
    # 各テスト期間のポートフォリオ履歴を結合して一つのDataFrameを作成
    final_integrated_portfolio_df = pd.DataFrame()
    if all_walk_forward_portfolio_dfs:
        # 重複する日付の処理 (最新の値、または平均値など) を考慮し、日付でソートして結合
        final_integrated_portfolio_df = (
            pd.concat(all_walk_forward_portfolio_dfs)
            .drop_duplicates(subset="Date", keep="last")
            .sort_values(by="Date")
            .reset_index(drop=True)
        )
    else:
        print(
            "統合されたポートフォリオ履歴データがありません。最終グラフ描画をスキップします。"
        )

    # 最終的なポートフォリオ価値の計算
    total_final_portfolio_value = INITIAL_CASH  # 最初の初期資金から始める
    if not final_integrated_portfolio_df.empty:
        total_final_portfolio_value = final_integrated_portfolio_df[
            "Portfolio_Value"
        ].iloc[-1]

    total_overall_return_percentage = (
        ((total_final_portfolio_value - INITIAL_CASH) / INITIAL_CASH) * 100
        if INITIAL_CASH != 0
        else 0
    )

    print("\n--- 統合シミュレーション結果の概要 ---")
    print(f"対象銘柄: {', '.join(TICKER_SYMBOLS)}")
    print(f"データ期間: {START_DATE} から {END_DATE}")
    print(
        f"ウォークフォワード設定: 最適化期間 {OPTIMIZATION_WINDOW_DAYS}日, テスト期間 {TEST_WINDOW_DAYS}日, ステップ {WALK_FORWARD_STEP_DAYS}日"
    )
    print(f"初期資産 (各テスト期間ごと): {INITIAL_CASH:,.0f} 円")
    print(f"利用レバレッジ: {LEVERAGE_RATIO} 倍")
    print(f"全期間の最終ポートフォリオ価値: {total_final_portfolio_value:,.0f} 円")
    print(f"全期間の総リターン (%): {total_overall_return_percentage:.2f}%")
    print("\n--- 注意 ---")
    print(
        "「半年で5倍」という目標は非常に高いリスクを伴い、本シミュレーションは極端な戦略に基づいています。"
    )
    print(
        "現実の投資では、これほどの高リターンを安定的に得ることは困難であり、資金を大きく失う可能性があります。"
    )

    # 統合された結果の可視化とレポート生成
    print("グラフ描画中...")
    visualizer = Visualizer()

    # 基準となる銘柄のデータを取得 (参照用)
    # 最初の銘柄の処理済みデータ（全期間）を可視化の基準とする
    reference_ticker_df = None
    if TICKER_SYMBOLS and TICKER_SYMBOLS[0] in raw_dfs:
        temp_df = raw_dfs[TICKER_SYMBOLS[0]].copy()
        temp_df = data_manager.calculate_moving_averages(temp_df)
        if temp_df is not None:
            temp_df = data_manager.calculate_rsi(temp_df)
            if temp_df is not None:
                # シグナルは最適化されたものではないが、グラフの基準として描画
                reference_ticker_df = strategy_manager.generate_trading_signals(temp_df)
                # 'Ticker' 列を追加（Visualizerで利用するため）
                if reference_ticker_df is not None:
                    reference_ticker_df["Ticker"] = TICKER_SYMBOLS[0]

    visualizer.plot_results(
        final_integrated_portfolio_df,
        all_walk_forward_trades,
        PLOT_FILE_NAME,
        reference_ticker_data=reference_ticker_df,
    )

    print("レポート生成中...")
    report_generator = ReportGenerator()
    report_generator.generate_excel_report(
        final_integrated_portfolio_df,
        all_walk_forward_trades,
        {
            "initial_cash": INITIAL_CASH,
            "final_portfolio_value": total_final_portfolio_value,
            "total_return_percentage": total_overall_return_percentage,
            "leverage_ratio": LEVERAGE_RATIO,
        },
    )

    print("\n--- シミュレーションが完了しました ---")


if __name__ == "__main__":
    main()
