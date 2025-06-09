# stock_trading_bot/src/report_generator.py

import pandas as pd

from .config import LONG_MA_PERIOD, OUTPUT_EXCEL_FILE, SHORT_MA_PERIOD


class ReportGenerator:
    def __init__(self, output_path=OUTPUT_EXCEL_FILE):
        self.output_path = output_path

    def generate_excel_report(
        self, df_portfolio: pd.DataFrame, df_trades: pd.DataFrame, summary_results: dict
    ):
        """
        シミュレーション結果をExcelファイルに出力します。
        """
        print(f"Excelレポート生成中: {self.output_path}")
        try:
            with pd.ExcelWriter(self.output_path, engine="openpyxl") as writer:
                # 総合結果シート
                summary_data = {
                    "項目": [
                        "初期資産",
                        "最終資産",
                        "総リターン(%)",
                        "Buy&Holdリターン(%)",
                        "短期MA期間",
                        "長期MA期間",
                    ],
                    "値": [
                        summary_results["initial_cash"],
                        summary_results["final_portfolio_value"],
                        summary_results["total_return_percentage"],
                        summary_results["buy_and_hold_return_percentage"],
                        SHORT_MA_PERIOD,
                        LONG_MA_PERIOD,
                    ],
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name="総合結果", index=False)

                # ポートフォリオ推移シート
                cols_to_export = [
                    "Date",
                    "Close",
                    f"SMA_{SHORT_MA_PERIOD}",
                    f"SMA_{LONG_MA_PERIOD}",
                    "Portfolio_Value",
                ]
                df_portfolio[cols_to_export].to_excel(
                    writer, sheet_name="ポートフォリオ推移", index=False
                )

                # 取引履歴シート
                if not df_trades.empty:
                    df_trades.to_excel(writer, sheet_name="取引履歴", index=False)
                else:
                    empty_df = pd.DataFrame({"Note": ["取引は発生しませんでした。"]})
                    empty_df.to_excel(writer, sheet_name="取引履歴", index=False)

            print(f"Excelレポートが '{self.output_path}' に出力されました。")
        except Exception as e:
            print(f"Excel出力中にエラーが発生しました: {e}")
