"""Reusable UI components"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path

from core.models import FilePair, ProcessingResults, SessionState
from core.config import config
from core.archive import ArchiveCreator
from core.exceptions import ArchiveError


class FileUploadComponent:
    """Component for file pair upload"""
    
    @staticmethod
    def render() -> List[FilePair]:
        """Render file upload interface and return valid file pairs"""
        st.subheader("ファイルペア登録")
        st.write("最大5ペアのDXFファイルを登録できます")
        
        file_pairs = []
        
        for i in range(config.max_pairs):
            with st.expander(f"ファイルペア {i+1}", expanded=i==0):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    uploaded_file_a = st.file_uploader(
                        f"DXFファイル A {i+1}", 
                        type="dxf", 
                        key=f"turnkey_a_{i}"
                    )
                    
                with col2:
                    uploaded_file_b = st.file_uploader(
                        f"DXFファイル B {i+1}", 
                        type="dxf", 
                        key=f"turnkey_b_{i}"
                    )
                
                with col3:
                    pair_name = st.text_input(
                        "ペア名",
                        value=f"Pair{i+1}",
                        key=f"turnkey_pair_name_{i}"
                    )
                
                # Add to valid pairs if both files are uploaded
                if uploaded_file_a and uploaded_file_b:
                    file_pairs.append(FilePair(uploaded_file_a, uploaded_file_b, pair_name))
                    st.success(f"{pair_name}: 処理準備完了")
        
        return file_pairs


class ProcessingComponent:
    """Component for processing control and status"""
    
    @staticmethod
    def render(file_pairs: List[FilePair], processor_callback: Callable) -> None:
        """Render processing control interface"""
        if not file_pairs:
            st.info("処理を開始するには、少なくとも1つのファイルペアをアップロードしてください")
            return
        
        st.subheader("処理対象")
        st.write(f"登録されたペア数： {len(file_pairs)}")
        
        # Display registered pairs
        for _, _, pair_name in file_pairs:
            st.write(f"• {pair_name}")
        
        # Check if processing has been started
        if not SessionState.get_processing_started():
            if st.button("処理を開始", type="primary", use_container_width=True):
                SessionState.set_processing_started(True)
                st.rerun()
        
        # Process if start button was clicked
        if SessionState.get_processing_started():
            try:
                # Create a single progress placeholder that updates in place
                progress_placeholder = st.empty()
                
                def progress_callback(message: str):
                    progress_placeholder.info(message)
                
                results = processor_callback(file_pairs, progress_callback)
                
                # Store results in session state
                SessionState.set_processing_results(results)
                SessionState.set_processing_completed(True)
                
                # Clear the progress message after completion
                progress_placeholder.empty()
                
            except Exception as e:
                st.error(f"❌ **処理エラー:** {str(e)}")
                SessionState.set_processing_started(False)
                st.stop()


class DownloadComponent:
    """Component for download functionality"""
    
    @staticmethod
    def render(results: ProcessingResults) -> None:
        """Render download interface"""
        st.subheader("処理結果")
        st.write("処理結果DXFファイルと関連データをダウンロードできます")
        
        successful_pairs = results.successful_pairs
        
        if not successful_pairs:
            st.warning("処理できたペアがありません。")
            return
        
        # Download all pairs button
        DownloadComponent._render_all_pairs_download(results)
        
        st.markdown("---")
        
        # Individual pair downloads
        DownloadComponent._render_individual_downloads(successful_pairs)
        
        st.success("処理が正常に完了しました！")
        
        # Reset button
        if st.button("🔄 新しい処理を開始", type="secondary"):
            SessionState.clear_all()
            st.rerun()
    
    @staticmethod
    def _render_all_pairs_download(results: ProcessingResults) -> None:
        """Render download all pairs section"""
        st.subheader("全ペアのダウンロード")
        
        try:
            all_zip_data = ArchiveCreator.create_all_pairs_archive(results)
            st.download_button(
                label="全ペアを一括ダウンロード (ZIP)",
                data=all_zip_data,
                file_name="all_processed_files.zip",
                mime="application/zip",
                key="download_all_pairs"
            )
        except ArchiveError as e:
            st.error(f"全ペアZIPファイル作成エラー: {str(e)}")
    
    @staticmethod
    def _render_individual_downloads(successful_pairs: dict) -> None:
        """Render individual pair downloads section"""
        st.subheader("個別ペアのダウンロード")
        
        for pair_name, result in successful_pairs.items():
            with st.expander(f"{pair_name}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    DownloadComponent._render_individual_files(pair_name, result)
                
                with col2:
                    DownloadComponent._render_pair_archive(pair_name, result)
    
    @staticmethod
    def _render_individual_files(pair_name: str, result) -> None:
        """Render individual file downloads"""
        st.write("**個別ファイル:**")
        
        # Download File A
        try:
            with open(result.file_a_output, 'rb') as f:
                file_a_data = f.read()
            
            st.download_button(
                label=f"{result.original_a_name}",
                data=file_a_data,
                file_name=result.original_a_name,
                mime="application/octet-stream",
                key=f"download_a_{pair_name}"
            )
        except Exception as e:
            st.error(f"ファイルＡ読み取りエラー: {str(e)}")
        
        # Download File B
        try:
            with open(result.file_b_output, 'rb') as f:
                file_b_data = f.read()
            
            st.download_button(
                label=f"{result.original_b_name}",
                data=file_b_data,
                file_name=result.original_b_name,
                mime="application/octet-stream",
                key=f"download_b_{pair_name}"
            )
        except Exception as e:
            st.error(f"ファイルＢ読み取りエラー: {str(e)}")
    
    @staticmethod
    def _render_pair_archive(pair_name: str, result) -> None:
        """Render pair archive download"""
        st.write("**全ファイル・アーカイブ:**")
        
        try:
            pair_zip_data = ArchiveCreator.create_pair_archive(result)
            st.download_button(
                label=f"{pair_name} 完全版 (ZIP)",
                data=pair_zip_data,
                file_name=f"{pair_name}_processed.zip",
                mime="application/zip",
                key=f"download_zip_{pair_name}"
            )
            
            # Show contents of the ZIP
            zip_contents = ArchiveCreator.get_archive_contents(result)
            if zip_contents:
                st.write("**アーカイブ内容:**")
                for filename in zip_contents:
                    st.write(f"• {filename}")
        
        except ArchiveError as e:
            st.error(f"ペアZIPファイル作成エラー: {str(e)}")