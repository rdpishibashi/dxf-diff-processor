#!/usr/bin/env python3
"""
DXF Post-processor
DXF後処理専用ツール（線幅・線色・テキスト色・フォントサイズ統一）
"""

import os
import sys
import logging
import re
from pathlib import Path
import argparse
import time
from typing import Dict, Optional, List, Union
import ezdxf
from ezdxf.math import Vec3
from ezdxf.entities import DXFEntity


class DXFPostProcessor:
    """DXF後処理クラス（線幅・線色・テキスト処理統一）"""
    
    def __init__(self, 
                 line_width_mm: float = 0.25, 
                 line_color: int = 7,  # DXFでは色番号（7=白）
                 text_color_mapping: Optional[Dict[str, List[str]]] = None,
                 char_color_mapping: Optional[Dict[str, List[str]]] = None,
                 min_font_size_mm: float = 2.5):  # デフォルト2.5mm
        self.line_width_mm = line_width_mm
        self.line_color = line_color
        self.text_color_mapping = text_color_mapping or {}
        self.char_color_mapping = char_color_mapping or {}
        self.min_font_size_mm = min_font_size_mm
        
        # DXF色番号マッピング（一般的な色）
        self.color_mapping = {
            'white': 7,
            'red': 1,
            'yellow': 2,
            'green': 3,
            'cyan': 4,
            'blue': 5,
            'magenta': 6,
            'black': 0
        }
    
    def process_dxf_file(self, dxf_file_path: Path, output_file_path: Path = None) -> bool:
        """DXFファイルの後処理を実行"""
        try:
            # DXFファイルを読み込み
            doc = ezdxf.readfile(dxf_file_path)
            
            # レイヤーテーブルを処理（色を統一）
            self._process_layer_table(doc)
            
            # ブロック定義を処理（色を統一）
            self._process_block_definitions(doc)
            
            # モデル空間を処理
            msp = doc.modelspace()
            self._process_modelspace(msp)
            
            # ペーパー空間も処理（もしあれば）
            for layout in doc.layouts:
                if layout.name != 'Model':
                    self._process_layout(layout)
            
            # DXFファイルを保存（出力ファイルが指定されていれば別名保存、なければ上書き）
            output_path = output_file_path or dxf_file_path
            doc.saveas(output_path)
            return True
            
        except ezdxf.DXFStructureError as e:
            logging.error(f"DXF構造エラー {dxf_file_path.name}: {e}")
            return False
        except Exception as e:
            logging.error(f"DXF後処理エラー {dxf_file_path.name}: {e}")
            return False
    
    def _process_layer_table(self, doc):
        """レイヤーテーブルの色を統一"""
        try:
            layers = doc.layers
            for layer in layers:
                if hasattr(layer.dxf, 'color'):
                    original_color = layer.dxf.color
                    layer.dxf.color = self.line_color
                    logging.debug(f"レイヤー色変更: {layer.dxf.name} {original_color} -> {self.line_color}")
        except Exception as e:
            logging.warning(f"レイヤーテーブル処理エラー: {e}")
    
    def _process_block_definitions(self, doc):
        """ブロック定義内のエンティティを処理"""
        try:
            blocks = doc.blocks
            for block in blocks:
                # システムブロック（*で始まる）はスキップ
                if block.name.startswith('*'):
                    continue
                    
                logging.debug(f"ブロック定義処理: {block.name}")
                for entity in block:
                    self._process_entity(entity)
        except Exception as e:
            logging.warning(f"ブロック定義処理エラー: {e}")
    
    def _process_modelspace(self, msp):
        """モデル空間の全エンティティを処理"""
        for entity in msp:
            self._process_entity(entity)
    
    def _process_layout(self, layout):
        """レイアウト（ペーパー空間）の全エンティティを処理"""
        for entity in layout:
            self._process_entity(entity)
    
    def _process_entity(self, entity: DXFEntity):
        """単一エンティティの処理"""
        entity_type = entity.dxftype()
        
        # デバッグ用：処理前の色を記録
        original_color = getattr(entity.dxf, 'color', 'None') if hasattr(entity, 'dxf') else 'None'
        logging.debug(f"処理中エンティティ: {entity_type}, 元の色: {original_color}")
        
        # 特に cyan(4) と yellow(2) のエンティティを詳細ログ
        if original_color in [2, 4]:
            logging.debug(f"色変更対象発見: {entity_type}, 色: {original_color} -> {self.line_color}")
        
        # 線要素の処理
        if entity_type in ['LINE', 'POLYLINE', 'LWPOLYLINE', 'CIRCLE', 'ARC', 
                          'ELLIPSE', 'SPLINE', 'RAY', 'XLINE', 'POINT', 'SOLID', 
                          'TRACE', '3DFACE', 'HELIX', 'REGION']:
            self._process_line_entity(entity)
        
        # テキスト要素の処理
        elif entity_type in ['TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF']:
            self._process_text_entity(entity)
        
        # 寸法の処理
        elif entity_type.startswith('DIMENSION') or entity_type in ['DIMENSION', 'LEADER', 'MULTILEADER']:
            self._process_dimension_entity(entity)
        
        # ブロック参照の処理
        elif entity_type == 'INSERT':
            self._process_insert_entity(entity)
        
        # ハッチングの処理
        elif entity_type == 'HATCH':
            self._process_hatch_entity(entity)
        
        # その他のエンティティ（色を強制的に統一）
        else:
            self._process_general_entity(entity)
        
        # 処理後の色を確認（特に元が cyan/yellow だった場合）
        if original_color in [2, 4]:
            final_color = getattr(entity.dxf, 'color', 'None') if hasattr(entity, 'dxf') else 'None'
            logging.debug(f"色変更結果: {entity_type}, {original_color} -> {final_color}")
    
    def _process_line_entity(self, entity: DXFEntity):
        """線要素の線幅と色を統一"""
        try:
            # 線幅を設定（DXFでは線幅は lineweight属性）
            if hasattr(entity.dxf, 'lineweight'):
                # mm を 0.01mm単位に変換（DXFの lineweight は 0.01mm単位）
                lineweight = int(self.line_width_mm * 100)
                entity.dxf.lineweight = lineweight
            
            # 色を強制的に設定（すべての色を統一）
            if hasattr(entity.dxf, 'color'):
                entity.dxf.color = self.line_color
            
            # True Color（RGB）も強制的にリセット
            if hasattr(entity.dxf, 'true_color'):
                entity.dxf.true_color = None  # True colorを無効化してindex colorを使用
            
            # Color Book Color も無効化
            if hasattr(entity.dxf, 'color_name'):
                entity.dxf.color_name = None
                
        except Exception as e:
            logging.warning(f"線要素処理エラー {entity.dxftype()}: {e}")
    
    def _process_text_entity(self, entity: DXFEntity):
        """テキスト要素の処理"""
        try:
            entity_type = entity.dxftype()
            
            # テキスト内容を取得
            if entity_type == 'TEXT':
                text_content = getattr(entity.dxf, 'text', '')
            elif entity_type == 'MTEXT':
                text_content = getattr(entity.dxf, 'text', '')
                # MTEXT の制御コードをクリーンアップ
                text_content = self._clean_mtext_content(text_content)
            else:
                text_content = ''
            
            # テキスト色を決定
            text_color = self._get_text_color_for_entity(text_content)
            if hasattr(entity.dxf, 'color'):
                entity.dxf.color = text_color
            
            # True Color（RGB）も強制的にリセット
            if hasattr(entity.dxf, 'true_color'):
                entity.dxf.true_color = None
            
            # Color Book Color も無効化
            if hasattr(entity.dxf, 'color_name'):
                entity.dxf.color_name = None
            
            # フォントサイズの最小値を適用
            if entity_type == 'TEXT' and hasattr(entity.dxf, 'height'):
                if entity.dxf.height < self.min_font_size_mm:
                    entity.dxf.height = self.min_font_size_mm
            elif entity_type == 'MTEXT' and hasattr(entity.dxf, 'char_height'):
                if entity.dxf.char_height < self.min_font_size_mm:
                    entity.dxf.char_height = self.min_font_size_mm
            elif entity_type in ['ATTRIB', 'ATTDEF'] and hasattr(entity.dxf, 'height'):
                if entity.dxf.height < self.min_font_size_mm:
                    entity.dxf.height = self.min_font_size_mm
            
            # テキストスタイルの統一（オプション）
            if hasattr(entity.dxf, 'style'):
                # 必要に応じてテキストスタイルを統一
                pass
                
        except Exception as e:
            logging.warning(f"テキスト要素処理エラー {entity.dxftype()}: {e}")
    
    def _process_dimension_entity(self, entity: DXFEntity):
        """寸法要素の処理"""
        try:
            # 寸法の色を強制的に設定
            if hasattr(entity.dxf, 'color'):
                entity.dxf.color = self.line_color
            
            # True Color（RGB）も強制的にリセット
            if hasattr(entity.dxf, 'true_color'):
                entity.dxf.true_color = None
            
            # Color Book Color も無効化
            if hasattr(entity.dxf, 'color_name'):
                entity.dxf.color_name = None
            
            # 寸法線の線幅も設定
            if hasattr(entity.dxf, 'lineweight'):
                lineweight = int(self.line_width_mm * 100)
                entity.dxf.lineweight = lineweight
            
            # 寸法テキストのフォントサイズを調整
            if hasattr(entity.dxf, 'dimtxsty') and hasattr(entity.dxf, 'dimtxt'):
                # 寸法テキストサイズの調整
                if entity.dxf.dimtxt < self.min_font_size_mm:
                    entity.dxf.dimtxt = self.min_font_size_mm
            elif hasattr(entity.dxf, 'text_height'):
                # 一般的な寸法テキストの高さ
                if entity.dxf.text_height < self.min_font_size_mm:
                    entity.dxf.text_height = self.min_font_size_mm
                
        except Exception as e:
            logging.warning(f"寸法要素処理エラー {entity.dxftype()}: {e}")
    
    def _process_insert_entity(self, entity: DXFEntity):
        """ブロック参照（INSERT）の処理"""
        try:
            # ブロック参照の色を強制的に設定
            if hasattr(entity.dxf, 'color'):
                entity.dxf.color = self.line_color
            
            # True Color（RGB）も強制的にリセット
            if hasattr(entity.dxf, 'true_color'):
                entity.dxf.true_color = None
            
            # Color Book Color も無効化
            if hasattr(entity.dxf, 'color_name'):
                entity.dxf.color_name = None
            
            # 線幅も設定
            if hasattr(entity.dxf, 'lineweight'):
                lineweight = int(self.line_width_mm * 100)
                entity.dxf.lineweight = lineweight
                
        except Exception as e:
            logging.warning(f"ブロック参照処理エラー: {e}")
    
    def _process_hatch_entity(self, entity: DXFEntity):
        """ハッチング要素の処理"""
        try:
            # ハッチングの色を強制的に設定
            if hasattr(entity.dxf, 'color'):
                entity.dxf.color = self.line_color
            
            # True Color（RGB）も強制的にリセット
            if hasattr(entity.dxf, 'true_color'):
                entity.dxf.true_color = None
            
            # Color Book Color も無効化
            if hasattr(entity.dxf, 'color_name'):
                entity.dxf.color_name = None
            
            # ハッチングの境界線の色も設定
            if hasattr(entity, 'paths'):
                # ハッチング境界線の色も統一（より詳細な処理が必要な場合）
                pass
                
        except Exception as e:
            logging.warning(f"ハッチング要素処理エラー: {e}")
    
    def _process_general_entity(self, entity: DXFEntity):
        """一般的なエンティティの処理（色と線幅を強制的に統一）"""
        try:
            # 色を強制的に設定（すべてのエンティティの色を統一）
            if hasattr(entity.dxf, 'color'):
                entity.dxf.color = self.line_color
            
            # True Color（RGB）も強制的にリセット
            if hasattr(entity.dxf, 'true_color'):
                entity.dxf.true_color = None
            
            # Color Book Color も無効化
            if hasattr(entity.dxf, 'color_name'):
                entity.dxf.color_name = None
            
            # 線幅も設定（可能な場合）
            if hasattr(entity.dxf, 'lineweight'):
                lineweight = int(self.line_width_mm * 100)
                entity.dxf.lineweight = lineweight
                    
        except Exception as e:
            logging.warning(f"一般エンティティ処理エラー {entity.dxftype()}: {e}")
    
    def _clean_mtext_content(self, text: str) -> str:
        """MTEXTの制御コードをクリーンアップ"""
        if not text:
            return text
        
        cleaned = text
        
        # MTEXT制御コードの除去（svg_processor と同様）
        # フォント制御コード {\f...;...} を除去
        cleaned = re.sub(r'\\f[^;]*;', '', cleaned)
        
        # 高さ制御コード {\H...x;} を除去
        cleaned = re.sub(r'\\H[^;]*;', '', cleaned)
        
        # カラー制御コード {\C...;} を除去
        cleaned = re.sub(r'\\C[^;]*;', '', cleaned)
        
        # その他の制御コード {\...} を除去
        cleaned = re.sub(r'\\[^\\]*;', '', cleaned)
        
        # \P（段落区切り）は保持する - 完全なテキスト内容として扱う
        # cleaned = re.sub(r'\\P.*', '', cleaned)  # この行をコメントアウトして\Pを保持
        
        # スペース制御 \~ を通常のスペースに変換
        cleaned = cleaned.replace('\\~', ' ')
        
        # バックスラッシュエスケープを処理
        cleaned = cleaned.replace('\\\\', '\\')
        cleaned = cleaned.replace('\\{', '{')
        cleaned = cleaned.replace('\\}', '}')
        
        # 連続する空白を単一空白に変換
        cleaned = re.sub(r' +', ' ', cleaned)
        
        return cleaned.strip()
    
    def _normalize_whitespace(self, text: str) -> str:
        """ホワイトスペースを正規化"""
        import re
        # すべてのホワイトスペース文字を単一スペースに変換
        normalized = re.sub(r'\s+', ' ', text.strip())
        return normalized
    
    def _get_text_color_for_entity(self, text_content: str) -> int:
        """テキスト内容に基づいて色を決定（-cc優先→-tc→デフォルト）"""
        # 空の場合はデフォルト色
        if not text_content:
            return self.line_color
        
        # ホワイトスペースを正規化
        normalized_text = self._normalize_whitespace(text_content)
        
        # Priority 1: Character-color (-cc) exact matching (highest priority)
        for color_name, string_list in self.char_color_mapping.items():
            for match_string in string_list:
                # 両方のテキストをホワイトスペース正規化して比較
                normalized_match = self._normalize_whitespace(match_string)
                if normalized_match == normalized_text:
                    # 色名を色番号に変換
                    return self.color_mapping.get(color_name.lower(), self.line_color)
        
        # Priority 2: Text-color (-tc) exact matching
        for color_name, string_list in self.text_color_mapping.items():
            for match_string in string_list:
                # 両方のテキストをホワイトスペース正規化して比較
                normalized_match = self._normalize_whitespace(match_string)
                if normalized_match == normalized_text:
                    # 色名を色番号に変換
                    return self.color_mapping.get(color_name.lower(), self.line_color)
        
        # Priority 3: Default color
        return self.line_color
    
    def batch_process(self, input_directory: str, output_directory: Optional[str] = None,
                     recursive: bool = True) -> List[Dict]:
        """ディレクトリ内のDXFファイルを一括処理"""
        
        # 入力ディレクトリの検証
        input_path = Path(input_directory)
        if not input_path.exists() or not input_path.is_dir():
            logging.error(f"入力ディレクトリが無効です: {input_directory}")
            return []
        
        # 出力ディレクトリの設定
        output_path = None
        if output_directory:
            output_path = Path(output_directory)
            output_path.mkdir(parents=True, exist_ok=True)
        
        # DXFファイルを検索
        if recursive:
            dxf_files = list(input_path.rglob("*.dxf")) + list(input_path.rglob("*.DXF"))
        else:
            dxf_files = list(input_path.glob("*.dxf")) + list(input_path.glob("*.DXF"))
        
        if not dxf_files:
            logging.warning(f"DXFファイルが見つかりません: {input_directory}")
            return []
        
        logging.debug(f"{len(dxf_files)}個のDXFファイルが見つかりました")
        
        # 各ファイルを処理
        results = []
        for i, dxf_file in enumerate(dxf_files, 1):
            try:
                start_time = time.time()
                
                # 出力ファイルパスを決定
                if output_path:
                    output_file = output_path / dxf_file.name
                else:
                    output_file = None  # 上書き
                
                logging.debug(f"処理中 ({i}/{len(dxf_files)}): {dxf_file.name}")
                
                # ファイルを処理
                success = self.process_dxf_file(dxf_file, output_file)
                
                elapsed_time = time.time() - start_time
                
                results.append({
                    'success': success,
                    'input_file': str(dxf_file),
                    'output_file': str(output_file) if output_file else str(dxf_file),
                    'elapsed_time': elapsed_time
                })
                
                if success:
                    logging.debug(f"完了: {dxf_file.name} ({elapsed_time:.2f}秒)")
                else:
                    logging.error(f"失敗: {dxf_file.name}")
                    
            except Exception as e:
                logging.error(f"処理エラー {dxf_file.name}: {e}")
                results.append({
                    'success': False,
                    'input_file': str(dxf_file),
                    'error': str(e)
                })
        
        # 結果サマリー
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logging.debug(f"処理完了: 成功 {successful}件, 失敗 {failed}件")
        
        if failed > 0:
            logging.warning("失敗したファイル:")
            for result in results:
                if not result['success']:
                    logging.warning(f"  - {Path(result['input_file']).name}: {result.get('error', '不明なエラー')}")
        
        return results


def setup_logging(log_level: str = 'WARNING') -> None:
    """ログ設定を初期化"""
    log_dir = Path.home() / 'Library' / 'Logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'dxf_processing.log'
    
    # ログレベルの設定
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # ログフォーマットの設定
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # ログ設定
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.debug(f"ログファイル: {log_file}")


def parse_text_color_args(tc_args: List[str]) -> Dict[str, List[str]]:
    """テキスト色引数を解析（svg_processor.py と同様）"""
    color_mapping = {}
    
    for color_rule in tc_args:
        try:
            color, strings = color_rule.split(':', 1)
            color = color.strip()
            
            # ファイル指定の場合（.txtで終わる）
            if strings.strip().endswith('.txt'):
                file_path = strings.strip()
                # 通常のパス形式で処理（絶対パス、相対パスをサポート）
                if not os.path.isabs(file_path):
                    # 相対パスの場合は現在の作業ディレクトリからの相対パス
                    file_path = os.path.abspath(file_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # ファイルから行を読み込み、空行やコメント行をスキップ
                        string_list = []
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            # 空行やコメント行（#で始まる）をスキップ
                            if not line or line.startswith('#'):
                                continue
                            
                            # 引用符で囲まれた文字列の処理
                            if (line.startswith('"') and line.endswith('"')) or \
                               (line.startswith("'") and line.endswith("'")):
                                # 引用符を除去
                                line = line[1:-1]
                            
                            string_list.append(line)
                        
                        if string_list:
                            color_mapping[color] = string_list
                            print(f"📝 ファイルから読み込み: {color} = {len(string_list)}個のテキスト ({file_path})")
                        else:
                            print(f"⚠️  ファイルが空です: {file_path}")
                            
                except FileNotFoundError:
                    print(f"❌ エラー: ファイルが見つかりません: {file_path}")
                    continue
                except Exception as e:
                    print(f"❌ エラー: ファイル読み込みエラー: {file_path} - {e}")
                    continue
            else:
                # 通常の文字列指定の場合
                # カンマで分割
                string_list = []
                for s in strings.split(','):
                    s = s.strip()
                    # 引用符で囲まれた文字列の処理
                    if (s.startswith("'") and s.endswith("'")) or \
                       (s.startswith('"') and s.endswith('"')):
                        # 引用符を除去
                        s = s[1:-1]
                    string_list.append(s)
                
                color_mapping[color] = string_list
        
        except ValueError:
            print(f"❌ エラー: 無効な色指定形式: {color_rule}")
            print("   正しい形式: -tc color:string1,string2,... または -tc color:file.txt")
            continue
    
    return color_mapping


def parse_char_color_args(cc_args: List[str]) -> Dict[str, List[str]]:
    """文字色引数を解析（完全一致文字列用、-tcより優先）"""
    color_mapping = {}
    
    for color_rule in cc_args:
        try:
            color, strings = color_rule.split(':', 1)
            color = color.strip()
            
            # ファイル指定の場合（.txtで終わる）
            if strings.strip().endswith('.txt'):
                file_path = strings.strip()
                # 通常のパス形式で処理（絶対パス、相対パスをサポート）
                if not os.path.isabs(file_path):
                    # 相対パスの場合は現在の作業ディレクトリからの相対パス
                    file_path = os.path.abspath(file_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # ファイルから行を読み込み、空行やコメント行をスキップ
                        string_list = []
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            # 空行やコメント行（#で始まる）をスキップ
                            if not line or line.startswith('#'):
                                continue
                            
                            # 引用符で囲まれた文字列の処理
                            if (line.startswith('"') and line.endswith('"')) or \
                               (line.startswith("'") and line.endswith("'")):
                                # 引用符を除去
                                line = line[1:-1]
                            
                            string_list.append(line)
                        
                        if string_list:
                            color_mapping[color] = string_list
                            print(f"📝 ファイルから読み込み: {color} = {len(string_list)}個の文字列 ({file_path})")
                        else:
                            print(f"⚠️  ファイルが空です: {file_path}")
                            
                except FileNotFoundError:
                    print(f"❌ エラー: ファイルが見つかりません: {file_path}")
                    continue
                except Exception as e:
                    print(f"❌ エラー: ファイル読み込みエラー: {file_path} - {e}")
                    continue
            else:
                # 通常の文字列指定の場合
                # カンマで分割
                string_list = []
                for s in strings.split(','):
                    s = s.strip()
                    # 引用符で囲まれた文字列の処理
                    if (s.startswith("'") and s.endswith("'")) or \
                       (s.startswith('"') and s.endswith('"')):
                        # 引用符を除去
                        s = s[1:-1]
                    string_list.append(s)
                
                color_mapping[color] = string_list
        
        except ValueError:
            print(f"❌ エラー: 無効な文字色指定形式: {color_rule}")
            print("   正しい形式: -cc color:string1,string2,... または -cc color:file.txt")
            continue
    
    return color_mapping


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='DXF後処理ツール（線幅・線色・テキスト色・フォントサイズ統一）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s input.dxf                                    # 基本的な処理（上書き）
  %(prog)s input.dxf -o output.dxf                     # 別名で保存
  %(prog)s input.dxf -lw 0.5 -lc red                   # 線幅0.5mm、線色赤
  %(prog)s input.dxf -tc red:'(BL)','(RD)'             # テキスト色指定
  %(prog)s input.dxf -tc red:red.txt                   # ファイルからテキスト読み込み
  %(prog)s input.dxf -tc red:red.txt -tc blue:'(GN)'   # 複数色指定
  %(prog)s input.dxf -cc magenta:'(BL)','(RD)'         # 文字色指定（完全一致、最優先）
  %(prog)s input.dxf -cc red:red.txt -tc blue:'(GN)'   # -cc（最優先）と-tcの組み合わせ
  %(prog)s input.dxf --min-font-size 2.5               # 最小フォントサイズ2.5mm
  %(prog)s input.dxf --dry-run                         # 実行せずに設定確認
  %(prog)s /path/to/dxf/directory -o /path/to/output   # ディレクトリ一括処理

DXF色番号:
  white=7, red=1, yellow=2, green=3, cyan=4, blue=5, magenta=6, black=0

テキスト色指定ファイル形式:
  # コメント行
  (BL)
  "スペースを含む文字列"
  AWG16(R)
        """
    )
    
    # 必須引数
    parser.add_argument('input', help='入力DXFファイルまたはディレクトリ')
    
    # オプション引数
    parser.add_argument('-o', '--output', help='出力DXFファイルまたはディレクトリ（指定しない場合は入力ファイルを上書き）')
    parser.add_argument('-lw', '--line-width', type=float, default=0.25,
                        help='線幅 (mm) (デフォルト: 0.25)')
    parser.add_argument('-lc', '--line-color', default='white',
                        help='線色 (デフォルト: white) 使用可能: white,red,yellow,green,cyan,blue,magenta,black')
    parser.add_argument('-tc', '--text-color', action='append', default=[],
                        help='テキスト色指定 color:strings または color:file.txt (複数指定可能)')
    parser.add_argument('-cc', '--char-color', action='append', default=[],
                        help='文字色指定 color:strings または color:file.txt (完全一致、-tcより優先)')
    parser.add_argument('--min-font-size', type=float, default=2.5,
                        help='最小フォントサイズ (mm) (デフォルト: 2.5mm)')
    parser.add_argument('-r', '--recursive', action='store_true', default=True,
                        help='ディレクトリ処理時にサブディレクトリも検索（デフォルト: True）')
    parser.add_argument('--dry-run', action='store_true',
                        help='実際の処理は行わず、設定のみ表示')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='WARNING', help='ログレベル (デフォルト: WARNING)')
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.log_level)
    
    # 入力パスの確認
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ エラー: 入力パスが見つかりません: {input_path}")
        sys.exit(1)
    
    is_directory = input_path.is_dir()
    is_file = input_path.is_file()
    
    if is_file and not input_path.suffix.lower() == '.dxf':
        print(f"❌ エラー: DXFファイルを指定してください: {input_path}")
        sys.exit(1)
    elif not is_file and not is_directory:
        print(f"❌ エラー: 有効なファイルまたはディレクトリを指定してください: {input_path}")
        sys.exit(1)
    
    # 色設定の検証
    color_mapping = {
        'white': 7, 'red': 1, 'yellow': 2, 'green': 3,
        'cyan': 4, 'blue': 5, 'magenta': 6, 'black': 0
    }
    
    line_color = color_mapping.get(args.line_color.lower())
    if line_color is None:
        print(f"❌ エラー: 無効な線色: {args.line_color}")
        print(f"使用可能な色: {', '.join(color_mapping.keys())}")
        sys.exit(1)
    
    # テキスト色設定の解析
    text_color_mapping = {}
    if args.text_color:
        text_color_mapping = parse_text_color_args(args.text_color)
    
    # 文字色設定の解析
    char_color_mapping = {}
    if args.char_color:
        char_color_mapping = parse_char_color_args(args.char_color)
    
    # 出力パスの決定
    output_path = None
    if args.output:
        output_path = Path(args.output)
        if is_file:
            # 単一ファイルの場合、出力ディレクトリを作成
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # ディレクトリの場合、出力ディレクトリを作成
            output_path.mkdir(parents=True, exist_ok=True)
    
    # 設定の表示
    print(f"📁 入力: {input_path.absolute()}")
    if output_path:
        print(f"📄 出力: {output_path.absolute()}")
    else:
        print(f"📄 出力: {input_path.absolute()} (上書き)")
    print(f"🎨 DXF後処理設定:")
    print(f"  線幅: {args.line_width}mm")
    print(f"  線色: {args.line_color} (DXF色番号: {line_color})")
    print(f"  最小フォントサイズ: {args.min_font_size}mm")
    
    if char_color_mapping:
        print(f"  文字色設定 (-cc、完全一致、最優先):")
        for color, strings in char_color_mapping.items():
            color_num = color_mapping.get(color.lower(), 7)
            print(f"    {color} ({color_num}): {', '.join(strings)}")
    
    if text_color_mapping:
        print(f"  テキスト色設定 (-tc):")
        for color, strings in text_color_mapping.items():
            color_num = color_mapping.get(color.lower(), 7)
            print(f"    {color} ({color_num}): {', '.join(strings)}")
    
    if not char_color_mapping and not text_color_mapping:
        print(f"  テキスト色: {args.line_color}（固定）")
    
    if is_directory:
        print(f"  再帰検索: {'Yes' if args.recursive else 'No'}")
    
    if args.dry_run:
        print("\n実際の処理を行うには --dry-run オプションを外してください。")
        return
    
    # DXF後処理の実行
    start_time = time.time()
    
    processor = DXFPostProcessor(
        line_width_mm=args.line_width,
        line_color=line_color,
        text_color_mapping=text_color_mapping,
        char_color_mapping=char_color_mapping,
        min_font_size_mm=args.min_font_size
    )
    
    if is_directory:
        # ディレクトリ一括処理
        logging.info(f"DXF一括処理開始: {input_path}")
        results = processor.batch_process(
            input_directory=str(input_path),
            output_directory=str(output_path) if output_path else None,
            recursive=args.recursive
        )
        
        elapsed_time = time.time() - start_time
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        print(f"✅ DXF一括処理完了: {successful}/{total} ファイル ({elapsed_time:.2f}秒)")
        
        if successful < total:
            sys.exit(1)
    else:
        # 単一ファイル処理
        logging.info(f"DXF処理開始: {input_path.name}")
        
        if processor.process_dxf_file(input_path, output_path):
            elapsed_time = time.time() - start_time
            output_name = output_path.name if output_path else input_path.name
            logging.info(f"DXF処理完了: {output_name} ({elapsed_time:.2f}秒)")
            print(f"✅ DXF処理完了: {output_name}")
        else:
            logging.error(f"DXF処理失敗: {input_path.name}")
            print(f"❌ DXF処理失敗: {input_path.name}")
            sys.exit(1)


if __name__ == '__main__':
    main()