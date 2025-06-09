# stock_trading_bot/src/report_generator.py

import os

import pandas as pd

from .config import REPORT_FILE_NAME  # ここを修正


class ReportGenerator:
    def __init__(self):
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_excel_report(
        self,
        portfolio_df: pd.DataFrame,
        trade_history_df: pd.DataFrame,
        summary_results: dict,
    ):
        """
        シミュレーション結果をExcelファイルとして出力します。
        """
        report_path = os.path.join(self.output_dir, REPORT_FILE_NAME)

        try:
            with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
                # サマリーシート
                summary_data = {
                    "項目": [
                        "初期資金",
                        "最終ポートフォリオ価値",
                        "総リターン (%)",
                        "利用レバレッジ",
                    ],
                    "値": [
                        f"{summary_results['initial_cash']:,.0f} 円",
                        f"{summary_results['final_portfolio_value']:,.0f} 円",
                        f"{summary_results['total_return_percentage']:.2f} %",
                        f"{summary_results['leverage_ratio']} 倍",
                    ],
                }
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name="Summary", index=False)

                # ポートフォリオ履歴シート
                if not portfolio_df.empty:
                    # 日付列の表示形式を調整
                    portfolio_df["Date"] = portfolio_df["Date"].dt.strftime("%Y-%m-%d")
                    portfolio_df.to_excel(
                        writer, sheet_name="Portfolio History", index=False
                    )
                else:
                    empty_df = pd.DataFrame(
                        {"Message": ["ポートフォリオ履歴データがありません。"]}
                    )
                    empty_df.to_excel(
                        writer, sheet_name="Portfolio History", index=False
                    )

                # 取引履歴シート
                if not trade_history_df.empty:
                    # 日付列の表示形式を調整
                    trade_history_df["Date"] = trade_history_df["Date"].dt.strftime(
                        "%Y-%m-%d"
                    )
                    trade_history_df.to_excel(
                        writer, sheet_name="Trade History", index=False
                    )
                else:
                    empty_df = pd.DataFrame(
                        {"Message": ["取引履歴データがありません。"]}
                    )
                    empty_df.to_excel(writer, sheet_name="Trade History", index=False)

            print(f"レポートを保存しました: {report_path}")

        except Exception as e:
            print(f"レポートの生成中にエラーが発生しました: {e}")
