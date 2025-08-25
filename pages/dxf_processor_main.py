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
    st.title('ＤＸＦ差分プロセッサー')
    st.write('２つのDXFファイルのラベルを比較し、その差分をハイライトして処理します。')
    
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