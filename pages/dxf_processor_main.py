"""Refactored DXF Processing Suite - Main Application"""

import streamlit as st
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from core.processor import DXFProcessor
from core.models import SessionState
from ui.components import FileUploadComponent, ProcessingComponent, DownloadComponent


def app():
    """Main application entry point"""
    st.title('DXF Diff Processor')
    st.write('２つのDXFファイルのラベルを比較し、その差分をハイライトして処理します。')
    
    # プログラム説明
    with st.expander("ℹ️ プログラム説明", expanded=False):
        help_text = [
            "このツールは、複数のDXFファイルペアからラベル比較、差分処理、アーカイブ作成を一括で実行します。",
            "",
            "**使用手順：**",
            "1. 各ファイルペアを登録してください（最大5ペア）",
            "2. 「処理を開始」ボタンをクリックして処理を実行します",
            "3. 処理完了後、結果をダウンロードできます",
            "",
            "**処理内容：**",
            "- ラベル比較をまとめたExcelファイル生成",
            "- ラベル差分リストファイルの生成",
            "- 差分ラベルの処理とハイライト",
            "- 結果のアーカイブ（ZIP）作成",
            "",
            "**出力ファイル：**",
            "- ラベル差分比較結果Excelふぁいる",
            "- ラベル差分リストファイル", 
            "- 差分処理済みDXFファイル",
            "- 全ファイルを含むZIPアーカイブ"
        ]
        
        st.info("\n".join(help_text))
    
    # Initialize processor
    processor = DXFProcessor()
    
    # File upload component
    file_pairs = FileUploadComponent.render()
    
    # Processing component
    ProcessingComponent.render(
        file_pairs=file_pairs,
        processor_callback=lambda pairs, callback: processor.process_file_pairs(pairs, callback)
    )
    
    # Download component (if processing is completed)
    if SessionState.get_processing_completed():
        results = SessionState.get_processing_results()
        if results:
            DownloadComponent.render(results)


if __name__ == "__main__":
    app()