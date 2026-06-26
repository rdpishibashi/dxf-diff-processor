# TECHNICAL.md — DXF-diff-processor

## 概要

複数の DXF ファイルペアに対してラベル比較・差分ハイライト・アーカイブ作成を一括実行する Streamlit アプリ。
内部では外部 Python スクリプト（`diff_label_processor.py`、`dxf_processor.py`）をサブプロセスとして呼び出す 4 ステップパイプラインで動作する。

---

## ディレクトリ構成

```
DXF-diff-processor/
├── app.py                  # Streamlit エントリポイント
├── common_utils.py         # 共通ユーティリティ（save_uploadedfile 等）
├── requirements.txt
├── core/
│   ├── config.py           # 設定管理（スクリプトパス・環境変数）
│   ├── models.py           # データモデル（FilePair, ProcessingResult 等）
│   ├── processor.py        # メイン処理パイプライン（DXFProcessor）
│   └── exceptions.py       # 例外クラス定義
├── ui/
│   └── components.py       # UI コンポーネント（FileUpload, Processing, Download）
├── utils/
│   ├── compare_labels.py   # ラベル比較（compare_labels_multi）
│   └── extract_labels.py   # ラベル抽出
├── scripts/
│   ├── diff_label_processor.py  # 差分ラベル処理スクリプト
│   └── dxf_processor.py         # DXF ファイル処理スクリプト
└── tests/
```

---

## アーキテクチャ

### 処理パイプライン（`core/processor.py`）

```
Step 1: compare_labels_multi()     # ラベル比較 → Excel バイナリ
Step 2: Excel → CSV 変換           # 一時ディレクトリに展開
Step 3: diff_label_processor.py   # サブプロセス：差分ラベルリスト生成
Step 4: dxf_processor.py          # サブプロセス：DXF ファイルへの差分ハイライト
→ ZIP アーカイブ生成 → ダウンロード
```

各ペアは独立して処理され、1 ペアの失敗が他ペアに影響しない。

### データモデル（`core/models.py`）

| クラス | 役割 |
|--------|------|
| `FilePair` | NamedTuple: (file_a, file_b, pair_name) |
| `ProcessingResult` | 1 ペアの処理結果（成功/失敗・出力パス・エラー情報） |
| `ProcessingResults` | 全ペアの結果集合（working_dir 保持） |
| `SessionState` | Streamlit session_state への静的アクセサ群 |

### 設定管理（`core/config.py`）

外部スクリプトのパスを以下の優先順で解決する:

1. `scripts/diff_label_processor.py`（ローカル同梱版）
2. `$DXF_TOOLS_DIR/DXF-viewer/` 以下（環境変数指定）
3. デフォルトパス（`/Users/ryozo/.../DXF-viewer/`）

環境変数:

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `DXF_TOOLS_DIR` | ハードコード | 外部スクリプトディレクトリ |
| `DXF_MAX_PAIRS` | 5 | 最大ペア数 |
| `DXF_TIMEOUT` | 120 | サブプロセスタイムアウト（秒） |

---

## UI コンポーネント（`ui/components.py`）

| コンポーネント | 役割 |
|--------------|------|
| `FileUploadComponent.render()` | 最大 5 ペア分のファイルアップロード UI |
| `ProcessingComponent.render()` | 処理開始ボタン・進捗表示・コールバック呼び出し |
| `DownloadComponent.render()` | 結果ファイルの ZIP ダウンロードボタン |

---

## 出力ファイル

| ファイル | 説明 |
|---------|------|
| ラベル差分比較 Excel | `compare_labels_multi()` の出力 |
| 差分ラベルリスト | `diff_label_processor.py` の出力 |
| 差分ハイライト DXF（A・B 各 1 本） | `dxf_processor.py` の出力 |
| ZIP アーカイブ | 全出力ファイルをまとめたもの |

---

## 依存パッケージ

```
streamlit>=1.40.0, ezdxf>=1.4.2, pandas>=2.0.0
xlsxwriter>=3.0.0, openpyxl>=3.0.0, numpy>=1.24.0
```

---

## 既知の制限

| 制限 | 詳細 |
|------|------|
| サブプロセス依存 | `diff_label_processor.py` / `dxf_processor.py` がパス上に必要 |
| Streamlit Cloud 非対応 | サブプロセス経由の外部スクリプト呼び出しはクラウドで動作しない可能性がある |
| 一時ファイルの残留 | サブプロセス異常終了時に `tempfile.mkdtemp()` の一時ディレクトリが残ることがある |
| タイムアウト固定 | 大きい DXF ファイルで 120 秒を超えると失敗する |

---

## 機能拡張ポイント

| テーマ | 実装アプローチ |
|--------|--------------|
| サブプロセス廃止 | `scripts/` のロジックを `core/` に直接組み込み Python 関数化する |
| ペア数上限の変更 | `DXF_MAX_PAIRS` 環境変数または `config.py` の `max_pairs` を変更 |
| 進捗バー | `progress_callback` を `st.progress()` に接続 |
| エラー詳細レポート | `ProcessingResult.error_details` を UI で展開表示 |
| 並列処理 | `concurrent.futures.ThreadPoolExecutor` でペアを並列処理 |
