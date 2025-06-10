# `src/backtester.py` 修正計画

## 1. 現状の課題と改善点

1.  **`Backtester` クラスの初期化における日付処理の改善**:
    *   `processed_dfs` の各DataFrameの 'Date' 列が既にDatetime型であるか、またはインデックスであるかをチェックし、冗長な変換を避けるようにします。
2.  **取引シグナルのカラム名の一貫性**:
    *   `trade_history` に追加する辞書で `"Action"` を `"Trade_Type"` に修正するコメントがあり、設計書と整合させるため、この修正を適用します。
3.  **レバレッジと資金配分のロジック**:
    *   現在のレバレッジの解釈（購入枠を増やすが、実際の購入は現金内で行う）で問題ないことをユーザーに確認済みです。このロジックは維持します。
4.  **ポートフォリオ価値の記録方法の改善**:
    *   現在の `pd.concat` を使用したループ内でのDataFrameへの追加はパフォーマンスが悪い可能性があります。一時的なリストに辞書を追加し、ループ後に一度にDataFrameに変換する方が効率的です。
    *   `portfolio_history_df` に `Strategy` 列を追加します。これは `main.py` で複数戦略を比較する際に必要になる情報です。
5.  **DocstringとPEP8準拠**:
    *   `_get_current_portfolio_value`、`run_simulation`、`get_summary_results` メソッドのDocstringをGoogleスタイルに準拠させ、詳細化します。
    *   全体的にPEP8の規約に沿っているか確認し、必要に応じて修正します。

## 2. 修正計画の詳細

以下のステップで `src/backtester.py` を修正します。

### 2.1. Docstringの追加・詳細化

*   **`_get_current_portfolio_value(self, current_prices: dict) -> float`**:
    *   現在のポートフォリオの総価値を計算するDocstringを追加します。
    *   Args: `current_prices` (dict): 各銘柄の現在価格を格納した辞書。
    *   Returns: `float`: 現在のポートフォリオの総価値。
*   **`run_simulation(self)`**:
    *   シミュレーションを実行し、ポートフォリオの推移と取引履歴を記録するDocstringを詳細化します。
    *   Returns: `tuple[pd.DataFrame, pd.DataFrame]`: ポートフォリオ履歴DataFrameと取引履歴DataFrame。
*   **`get_summary_results(self) -> dict`**:
    *   シミュレーションの最終結果を要約して返すDocstringを詳細化します。
    *   Returns: `dict`: シミュレーションの要約結果を含む辞書。

### 2.2. `Backtester` クラスの初期化 (`__init__`) の改善

*   `self.portfolio_values = []` の行を削除します。（未使用のため）
*   日付処理のロジックを以下のように変更します。
    ```python
    # 各データフレームの 'Date' 列がインデックスであることを確認し、DatetimeIndexに変換（既に変換されていることを想定しているが念のため）
    for df in valid_dfs:
        if "Date" not in df.columns:
            print("警告: バックテスター初期化: データフレームに 'Date' 列が見つかりません。")
            self.dates = []
            return

        # 'Date' 列が既にDatetime型でない場合のみ変換
        if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
            df["Date"] = pd.to_datetime(df["Date"])

        # 'Date' 列がインデックスでない場合のみ設定
        if not isinstance(df.index, pd.DatetimeIndex) or "Date" in df.index.name:
            df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)  # インデックスでソートされていることを確認
    ```

### 2.3. `run_simulation` メソッドの改善

*   **取引履歴のカラム名修正**:
    *   `trade_history.append` の `"Action"` キーを `"Trade_Type"` に変更します。
        *   買いシグナル時: `"Trade_Type": "BUY"`
        *   売りシグナル時: `"Trade_Type": "SELL"`
*   **ポートフォリオ価値の記録方法の改善**:
    *   `self.portfolio_history_df` への追加ロジックを以下のように変更します。
        ```python
        # 各日のポートフォリオ価値を記録
        current_portfolio_value = self._get_current_portfolio_value(current_prices)
        # 一時的なリストにレコードを追加
        portfolio_records.append(
            {
                "Date": current_date,
                "Portfolio_Value": current_portfolio_value,
                "Strategy": self.strategy_name, # 戦略名を追加
            }
        )

        # ループ終了後、一度にDataFrameに変換
        self.portfolio_history_df = pd.DataFrame(portfolio_records)
        ```
    *   `run_simulation` メソッドの冒頭で `portfolio_records = []` を初期化します。

### 2.4. PEP8準拠の確認と修正

*   全体的にPEP8の規約に沿っているか確認し、必要に応じて修正します。特に、行の長さ、空白、命名規則などを確認します。

## 3. 修正後のフロー

```mermaid
graph TD
    A[現在のBacktester.py] --> B{課題特定};
    B --> C[修正計画立案];
    C -- ユーザー承認 --> D[docs/backtester_plan.md 生成];
    D --> E[モード切り替え (Codeモード)];
    E --> F[Backtester.py 修正実装];
    F --> G[テスト実行];
    G -- 成功 --> H[完了];
    G -- 失敗 --> F;
```

この計画書を作成しました。

次に、この計画に基づいてコードを実装するために、モードを `code` に切り替える必要があります。

<switch_mode>
<mode_slug>code</mode_slug>
<reason>バックテスト機能の修正計画が確定したため、コード実装フェーズに移行します。</reason>
</switch_mode>