# stock_trading_bot/src/main.py (抜粋 - メインロジックをウォークフォワードに)

from datetime import timedelta

import pandas as pd

from .backtester import Backtester
from .config import (
    END_DATE,
    INITIAL_CASH,  # MA期間は初期値として残す
    LEVERAGE_RATIO,
    LONG_MA_PERIOD,
    OPTIMIZATION_WINDOW_DAYS,  # ウォークフォワード設定
    SHORT_MA_PERIOD,
    START_DATE,
    TEST_WINDOW_DAYS,
    TICKER_SYMBOLS,
    WALK_FORWARD_STEP_DAYS,
    # 最適化範囲
)
from .data_manager import DataManager
from .report_generator import ReportGenerator
from .strategy_manager import StrategyManager


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
    all_walk_forward_results = []
    all_walk_forward_trades = pd.DataFrame()

    # 最初の最適化開始日を決定
    # 最も古いデータがある銘柄の最初のOPTIMIZATION_WINDOW_DAYS分のデータが必要
    min_date = min(
        df["Date"].min() for df in raw_dfs.values() if df is not None and not df.empty
    )
    max_date = max(
        df["Date"].max() for df in raw_dfs.values() if df is not None and not df.empty
    )

    current_optimization_start_date = min_date

    # ウォークフォワードループ
    while True:
        optimization_end_date = current_optimization_start_date + timedelta(
            days=OPTIMIZATION_WINDOW_DAYS
        )
        test_end_date = optimization_end_date + timedelta(days=TEST_WINDOW_DAYS)

        # テスト期間が全データ期間を超過したら終了
        if optimization_end_date > max_date or test_end_date > max_date:
            print("\nウォークフォワード最適化が全データ期間をカバーしました。")
            break

        print(
            f"\n--- ウォークフォワード期間: 最適化期間 [{current_optimization_start_date.strftime('%Y-%m-%d')} - {optimization_end_date.strftime('%Y-%m-%d')}] ---"
        )
        print(
            f"--- テスト期間: [{optimization_end_date.strftime('%Y-%m-%d')} - {test_end_date.strftime('%Y-%m-%d')}] ---"
        )

        # 各銘柄のデータを最適化期間とテスト期間に分割
        current_processed_dfs_for_optimization = {}
        current_processed_dfs_for_test = {}

        for ticker, df in raw_dfs.items():
            if df is None or df.empty:
                continue

            # 特徴量計算 (MA, RSI) - 全期間に対して一度に計算するのが効率的
            df_ma = data_manager.calculate_moving_averages(df.copy())
            if df_ma is None:
                continue
            df_final = data_manager.calculate_rsi(df_ma)
            if df_final is None:
                continue

            # 最適化期間のデータ
            opt_df = df_final[
                (df_final["Date"] >= current_optimization_start_date)
                & (df_final["Date"] < optimization_end_date)
            ].copy()
            if not opt_df.empty:
                current_processed_dfs_for_optimization[ticker] = opt_df

            # テスト期間のデータ
            test_df = df_final[
                (df_final["Date"] >= optimization_end_date)
                & (df_final["Date"] < test_end_date)
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
        # 実際には、この期間で最もパフォーマンスが良かった銘柄を選ぶ、等の工夫が必要
        optimization_ticker = list(current_processed_dfs_for_optimization.keys())[0]
        df_for_optimization = current_processed_dfs_for_optimization[
            optimization_ticker
        ]

        # 1. パラメータ最適化 (最適化期間のデータを使用)
        # strategy_manager.optimize_strategy_parameters はあくまで簡易的なもの。
        # 本格的なバックテストロジック（バックテスタークラス）を呼び出して
        # 最適化を実行するような構造にするべきですが、ここでは簡略化。
        best_params = strategy_manager.optimize_strategy_parameters(df_for_optimization)

        if not best_params:
            print("パラメータ最適化に失敗しました。スキップします。")
            current_optimization_start_date += timedelta(days=WALK_FORWARD_STEP_DAYS)
            continue

        # 最適化されたパラメータを元に、戦略マネージャーのシグナルを生成し直す
        # ここでは、最適なMA期間をstrategy_managerが使用するように、configの値を一時的に変更
        # または、generate_trading_signalsに直接パラメータを渡せるようにする

        # 現在の簡易的な generate_trading_signals は config のグローバル変数を使っているので、
        # ここで一時的に最適なパラメータを設定する
        # （これはベストプラクティスではないが、現行コードの変更を最小限にするため）
        import src.config

        src.config.SHORT_MA_PERIOD = best_params.get("short_ma", SHORT_MA_PERIOD)
        src.config.LONG_MA_PERIOD = best_params.get("long_ma", LONG_MA_PERIOD)
        # 必要なら RSI_OVERBOUGHT, RSI_OVERSOLD も同様に設定

        processed_dfs_for_test_with_optimized_params = {}
        for ticker, df_test_raw in current_processed_dfs_for_test.items():
            # テスト期間のデータに、最適化されたパラメータでMAとRSIを再計算
            df_test_ma = data_manager.calculate_moving_averages(
                df_test_raw.copy()
            )  # config変更後の値で計算
            if df_test_ma is None:
                continue
            df_test_final = data_manager.calculate_rsi(
                df_test_ma
            )  # config変更後の値で計算
            if df_test_final is None:
                continue

            df_test_signals = strategy_manager.generate_trading_signals(df_test_final)
            if df_test_signals is None:
                continue
            processed_dfs_for_test_with_optimized_params[ticker] = df_test_signals

        if not processed_dfs_for_test_with_optimized_params:
            print("テスト期間のデータ処理に失敗しました。スキップします。")
            current_optimization_start_date += timedelta(days=WALK_FORWARD_STEP_DAYS)
            continue

        # 2. テスト期間でバックテストを実行 (最適化されたパラメータを使用)
        backtester = Backtester(
            processed_dfs_for_test_with_optimized_params,
            initial_cash=INITIAL_CASH,
            leverage_ratio=LEVERAGE_RATIO,
        )
        # バックテストは、各ウォークフォワード期間の初めに初期資産をリセットして評価する
        # もしくは、前の期間の最終資産を引き継ぐ「連続バックテスト」にするか、設計の選択肢がある
        # 今回は簡易的に、各ウォークフォワード期間で初期資産100万円からのリターンを評価し、最終的に統合する。
        # 連続バックテストにするには、Backtesterの初期資金を、前の期間の最終資金にする必要があります。
        # (今回は簡易化のため、各期間で独立して評価し、最終結果で合計する)

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

        # 次の最適化期間の開始日を設定
        current_optimization_start_date += timedelta(days=WALK_FORWARD_STEP_DAYS)

    print("\n--- ウォークフォワードシミュレーション完了 ---")

    if not all_walk_forward_results:
        print("実行可能なシミュレーション期間がありませんでした。")
        return

    # 全期間を通した統合されたポートフォリオ価値を計算し、可視化
    # これは複雑な処理になるため、ここでは簡易的に累積リターンを表示する
    total_final_portfolio_value = INITIAL_CASH
    for res in all_walk_forward_results:
        # 各期間の最終リターンを初期資金に適用していく形で累積を計算
        # ただし、各期間の初期資金がINITIAL_CASHで固定されている場合、この累積は単純な合計とは異なる
        # 厳密なウォークフォワードでは、前の期間の最終資産が次の期間の初期資産となる
        # 今回は、各期間の「総リターン(%)」を平均して、総合的な戦略の有効性を測る

        # 簡易的な総リターン計算 (各期間の平均リターン)
        total_final_portfolio_value += (
            res["final_portfolio_value"] - res["initial_cash"]
        )  # 各期間の絶対利益/損失を合計

    # 総リターンは、あくまで各期間の合計損益
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
    print(f"全期間の累積損益額: {(total_final_portfolio_value - INITIAL_CASH):,.0f} 円")
    print(
        f"全期間の平均リターン (%): {total_overall_return_percentage:.2f}% (これは各期間のリターンを単純合計したもので、厳密なポートフォリオ推移ではありません)"
    )
    print("\n--- 注意 ---")
    print(
        "「半年で5倍」という目標は非常に高いリスクを伴い、本シミュレーションは極端な戦略に基づいています。"
    )
    print(
        "現実の投資では、これほどの高リターンを安定的に得ることは困難であり、資金を大きく失う可能性があります。"
    )

    # 統合された結果の可視化とレポート生成
    # ウォークフォワードの場合、ポートフォリオ価値の推移グラフは各テスト期間をつなぎ合わせる形になる
    # これはVisualizerで直接対応するのが難しいため、ここでは簡易的な出力のみに留める

    # 簡易的なポートフォリオ推移グラフの生成 (テスト期間ごとのリターンを連結)
    # 実際のグラフ描画は、各テスト期間のデータを統合したDataFrameを構築する必要がある
    # ここでは、簡略化のため、全期間の取引履歴のみでプロットは省略するか、手動で統合する

    # 全期間の取引履歴のみをレポートに出力
    final_integrated_portfolio_df = pd.DataFrame()  # グラフ描画用には別途構築が必要
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
