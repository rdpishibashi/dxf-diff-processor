# DXF差分プロセッサー (DXF-diff-processor)

２つのDXFファイルのラベルを比較し、その差分をハイライトします

## ✨ 特徴

### 🚀 Turn-key Solution
- **一元化されたインターフェース** - ファイル登録から処理完了まで1画面で完結
- **自動処理ワークフロー** - ボタン一つで4段階の処理を自動実行
- **手動開始制御** - ファイル確認後に手動で処理開始
- **日本語完全対応** - すべてのUI要素が日本語

### 📦 主要機能
- **マルチペア処理**: 最大5ペアのDXFファイルを同時処理
- **ZIP アーカイブ**: 個別ペアまたは全ペアの一括ダウンロード
- **色分け処理**: 削除(マゼンタ)、追加(シアン)、変更(イエロー)のラベル色分け
- **元ファイル名保持**: ダウンロードファイルは元の名前を維持
- **エラー時即停止**: エラー発生時の即座の処理停止
- **プログレス表示**: リアルタイム処理進捗表示

### 🎯 処理ワークフロー
1. **ラベル比較処理** - compare_labels_multi による差分抽出
2. **Excel→CSV変換** - 各シートを個別CSVファイルに変換
3. **ラベル差分処理** - diff_label_processor.py による詳細分析
4. **DXFファイル処理** - dxf_processor.py による色分け適用

## 📁 プロジェクト構造

```
DXF-diff-processor/
├── app.py                          # メインStreamlitアプリケーション
├── requirements.txt                # Python依存関係
├── core/                          # ビジネスロジック層
│   ├── __init__.py
│   ├── config.py                  # 設定管理
│   ├── exceptions.py              # カスタム例外
│   ├── models.py                  # データモデル・セッション管理
│   ├── processor.py               # コア処理ロジック
│   └── archive.py                 # ZIP アーカイブ機能
├── ui/                            # ユーザーインターフェース層
│   ├── __init__.py
│   └── components.py              # 再利用可能UIコンポーネント
├── pages/                         # Streamlitページ
│   ├── __init__.py
│   ├── dxf_processor_main.py      # メインアプリケーション
│   └── dxf_processor_turnkey.py   # 旧版（バックアップ）
├── tests/                         # テストスイート
│   ├── __init__.py
│   └── test_processor.py          # 単体テスト
└── README.md                      # このファイル
```

## 🛠️ インストール

### 1. 依存関係のインストール
```bash
cd /Users/ryozo/Dropbox/Client/ULVAC/ElectricDesignManagement/Tools/DXF-diff-processor
pip install -r requirements.txt
```

### 2. ディレクトリ構造の確認
```
/Users/ryozo/Dropbox/Client/ULVAC/ElectricDesignManagement/Tools/
├── DXF-diff-processor/          # このアプリケーション
├── DXF-tools/           # compare_labels機能のソース
└── DXF-viewer/          # diff_label_processor, dxf_processorのソース
```

### 3. 環境変数の設定（オプション）
```bash
export DXF_TOOLS_DIR="/path/to/Tools"
export DXF_MAX_PAIRS=5
export DXF_TIMEOUT=120
```

## 🚀 使用方法

### 1. アプリケーションの起動
```bash
streamlit run app.py
```

### 2. 基本ワークフロー
1. **ファイルペア登録** - DXFファイルA・Bとペア名を設定
2. **処理開始** - "処理を開始" ボタンをクリック
3. **自動処理** - 4段階の処理が自動実行される
4. **ダウンロード** - 処理済みファイルをZIP形式でダウンロード

### 3. ダウンロードオプション
- **個別ファイル**: 単一DXFファイルのダウンロード
- **ペアアーカイブ**: 1ペアの全ファイルをZIP形式
- **全ペアアーカイブ**: 全ペアの全ファイルをZIP形式

## 🧪 テスト

### シンプルテスト（推奨）
```bash
python tests/test_processor.py
```

### 高度なテスト（pytest使用）
```bash
# pytestのインストール
pip install pytest pytest-cov

# テスト実行
python tests/test_processor.py --pytest

# 詳細なテスト
pytest tests/test_processor.py -v

# カバレッジレポート
pytest tests/test_processor.py --cov=core
```

### テストヘルプ
```bash
python tests/test_processor.py --help
```

## ⚙️ 設定

### 設定ファイル: `core/config.py`
- **スクリプトパス**: diff_label_processor.py, dxf_processor.py の場所
- **最大ペア数**: 同時処理可能なファイルペア数
- **タイムアウト**: サブプロセス実行のタイムアウト時間
- **処理オプション**: フィルタリング、ソート順など

### 環境変数
- `DXF_TOOLS_DIR`: ツールディレクトリのパス
- `DXF_MAX_PAIRS`: 最大ペア数（デフォルト: 5）
- `DXF_TIMEOUT`: タイムアウト秒数（デフォルト: 120）

## 🏗️ アーキテクチャ

### レイヤー構造
- **UI層** (`ui/`): Streamlitコンポーネント
- **ビジネスロジック層** (`core/`): 処理ロジック
- **統合層** (`pages/`): UIとロジックの統合

### 主要クラス
- `DXFProcessor`: メイン処理エンジン
- `ArchiveCreator`: ZIP アーカイブ作成
- `SessionState`: セッション状態管理
- `FileUploadComponent`: ファイルアップロードUI
- `ProcessingComponent`: 処理制御UI
- `DownloadComponent`: ダウンロードUI

## 🔗 外部統合

### DXF-tools統合
- `utils.compare_labels.compare_labels_multi()` を直接インポート
- `common_utils` のファイル処理ユーティリティを使用
- 元のGUIオプションと同じインターフェースを維持

### DXF-viewer統合
- `diff_label_processor.py` をサブプロセスとして実行
- `dxf_processor.py` を色指定付きで実行
- 両スクリプトのコマンドライン引数を動的に構築

### 色分けスキーム
- **マゼンタ**: ファイルAから削除されたラベル（A Only）
- **シアン**: ファイルBに追加されたラベル（B Only）
- **イエロー**: 変更されたラベル（Different counts）

## 🛡️ エラーハンドリング

### カスタム例外階層
- `DXFProcessingError`: 基底例外
- `ComparisonError`: ラベル比較エラー
- `ExcelConversionError`: Excel変換エラー
- `DiffProcessorError`: diff_label_processor実行エラー
- `DXFProcessorError`: dxf_processor実行エラー
- `ArchiveError`: ZIP作成エラー

### エラー処理戦略
- **即座停止**: エラー発生時の処理即停止
- **詳細情報**: ペア名、ファイル種別、標準エラー出力を含む
- **継続処理**: 1ペアのエラーで他ペアの処理は継続

## 📊 依存関係

### 必須パッケージ
- streamlit>=1.28.0
- pandas>=1.5.0
- xlsxwriter>=3.0.0
- openpyxl>=3.0.0
- ezdxf>=1.0.0

### オプションパッケージ
- pytest（テスト用）
- pytest-cov（カバレッジ用）

### 標準ライブラリ
- pathlib, tempfile, shutil, os, sys, subprocess, zipfile, io

## 🚀 デプロイメント

### 本番環境
1. 環境変数でスクリプトパスを設定
2. ログレベルを適切に設定
3. エラーモニタリングを有効化

### 開発環境
1. テストスイートで動作確認
2. 設定検証でパス確認
3. モックデータでの動作テスト

## 🤝 貢献

### コード品質
- **型ヒント**: 全関数に型注釈
- **ドキュメント**: 包括的なdocstring
- **テスト**: 単体テスト・統合テスト
- **エラーハンドリング**: 具体的な例外処理

### 保守性
- **モジュール分離**: 単一責任原則
- **設定外部化**: 環境変数による設定
- **再利用性**: コンポーネントベース設計
- **拡張性**: プラガブルアーキテクチャ

---

