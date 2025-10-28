#!/usr/bin/env python3
"""
CSV Label Processor
CSVファイルから削除・追加・変更されたラベルを抽出するツール
"""

import csv
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

def process_csv_file(csv_file_path: Path) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    CSVファイルを処理して削除・追加・変更されたラベルを抽出
    
    Returns:
        deleted_labels: A Onlyのラベル一覧
        added_labels: B Onlyのラベル一覧
        modified_a_labels: Differentでdifference countがマイナスのラベル一覧
        modified_b_labels: Differentでdifference countがプラスのラベル一覧
    """
    deleted_labels = []
    added_labels = []
    modified_a_labels = []
    modified_b_labels = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            # CSVリーダーを作成
            csv_reader = csv.reader(f)
            
            # ヘッダー行をスキップ
            header = next(csv_reader)
            print(f"📋 CSVヘッダー: {header}")
            
            # データ行を処理
            for row_num, row in enumerate(csv_reader, start=2):
                if len(row) < 5:
                    print(f"⚠️  行 {row_num}: 列数が不足しています ({len(row)} < 5)")
                    continue
                
                label = row[0].strip()  # Column 1: ラベル
                comparison_result = row[3].strip()  # Column 4: 比較結果
                difference_count = int(row[4].strip())  # Column 5: 差分個数
                
                # 比較結果に基づいて分類
                if comparison_result == "A Only":
                    deleted_labels.append(label)
                elif comparison_result == "B Only":
                    added_labels.append(label)
                elif comparison_result == "Different":
                    if difference_count < 0:
                        modified_a_labels.append(label)
                    else:
                        modified_b_labels.append(label)
    
    except FileNotFoundError:
        print(f"❌ エラー: ファイルが見つかりません: {csv_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: CSV処理中にエラーが発生しました: {e}")
        sys.exit(1)
    
    return deleted_labels, added_labels, modified_a_labels, modified_b_labels

def write_label_file(labels: List[str], output_path: Path, label_type: str):
    """ラベル一覧をファイルに書き込み"""
    try:
        # 出力ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for label in labels:
                f.write(f"{label}\n")
        
        print(f"✅ {label_type}ラベル {len(labels)}件を出力: {output_path}")
    
    except Exception as e:
        print(f"❌ エラー: {label_type}ラベルファイルの書き込みに失敗: {e}")
        sys.exit(1)

def generate_output_paths(input_path: Path, output_dir: Path = None) -> Tuple[Path, Path, Path, Path]:
    """出力ファイルパスを生成"""
    # 出力ディレクトリが指定されていない場合は入力ファイルと同じディレクトリ
    if output_dir is None:
        output_dir = input_path.parent
    
    # 入力ファイル名から拡張子を除去してベース名を作成
    base_name = input_path.stem
    
    # 出力ファイルパスを生成
    deleted_path = output_dir / f"{base_name}_deleted.txt"
    added_path = output_dir / f"{base_name}_added.txt"
    modified_a_path = output_dir / f"{base_name}_modified_a.txt"
    modified_b_path = output_dir / f"{base_name}_modified_b.txt"
    
    return deleted_path, added_path, modified_a_path, modified_b_path

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='CSVファイルから削除・追加・変更されたラベルを抽出',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s pair.csv                           # 基本的な処理
  %(prog)s pair.csv -o output_dir             # 出力ディレクトリ指定
  %(prog)s pair.csv --dry-run                 # 実行せずに設定確認

入力CSVファイル形式:
  - 1行目: ヘッダー行
  - 2行目以降: データ行
  - Column 1: ラベル（文字列）
  - Column 2: A図面の個数
  - Column 3: B図面の個数
  - Column 4: 比較結果（"A Only", "B Only", "Different"）
  - Column 5: 差分個数

出力ファイル:
  - {入力ファイル名}_deleted.txt    : A Onlyのラベル一覧
  - {入力ファイル名}_added.txt      : B Onlyのラベル一覧
  - {入力ファイル名}_modified_a.txt : Differentで差分個数がマイナス（A側減少）のラベル一覧
  - {入力ファイル名}_modified_b.txt : Differentで差分個数がプラス（B側増加）のラベル一覧
        """
    )
    
    # 必須引数
    parser.add_argument('csv_file', help='入力CSVファイル')
    
    # オプション引数
    parser.add_argument('-o', '--output-dir', help='出力ディレクトリ（指定しない場合は入力ファイルと同じディレクトリ）')
    parser.add_argument('--dry-run', action='store_true',
                        help='実際の処理は行わず、設定のみ表示')
    
    args = parser.parse_args()
    
    # 入力ファイルの確認
    input_path = Path(args.csv_file)
    if not input_path.exists():
        print(f"❌ エラー: 入力ファイルが見つかりません: {input_path}")
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.csv':
        print(f"❌ エラー: CSVファイルを指定してください: {input_path}")
        sys.exit(1)
    
    # 出力ディレクトリの設定
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
    
    # 出力ファイルパスの生成
    deleted_path, added_path, modified_a_path, modified_b_path = generate_output_paths(input_path, output_dir)
    
    # 設定の表示
    print(f"📁 入力ファイル: {input_path.absolute()}")
    print(f"📄 出力ファイル:")
    print(f"  削除ラベル: {deleted_path}")
    print(f"  追加ラベル: {added_path}")
    print(f"  変更ラベル(A側): {modified_a_path}")
    print(f"  変更ラベル(B側): {modified_b_path}")
    
    if args.dry_run:
        print("\n実際の処理を行うには --dry-run オプションを外してください。")
        return
    
    # CSVファイルの処理
    print(f"\n🔄 CSV処理開始: {input_path.name}")
    deleted_labels, added_labels, modified_a_labels, modified_b_labels = process_csv_file(input_path)
    
    # 結果の表示
    print(f"\n📊 処理結果:")
    print(f"  削除ラベル (A Only): {len(deleted_labels)}件")
    print(f"  追加ラベル (B Only): {len(added_labels)}件")
    print(f"  変更ラベル (A側減少): {len(modified_a_labels)}件")
    print(f"  変更ラベル (B側増加): {len(modified_b_labels)}件")
    
    # ファイル出力
    print(f"\n📝 ファイル出力中...")
    write_label_file(deleted_labels, deleted_path, "削除")
    write_label_file(added_labels, added_path, "追加")
    write_label_file(modified_a_labels, modified_a_path, "変更(A側)")
    write_label_file(modified_b_labels, modified_b_path, "変更(B側)")
    
    print(f"\n✅ 処理完了: 4つのファイルが生成されました")

if __name__ == '__main__':
    main()