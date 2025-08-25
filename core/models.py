"""Data models for DXF processing"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple
import streamlit as st


class FilePair(NamedTuple):
    """Represents a pair of DXF files"""
    file_a: st.runtime.uploaded_file_manager.UploadedFile
    file_b: st.runtime.uploaded_file_manager.UploadedFile
    pair_name: str


@dataclass
class ProcessingResult:
    """Result of processing a single file pair"""
    pair_name: str
    success: bool
    file_a_output: Optional[Path] = None
    file_b_output: Optional[Path] = None
    original_a_name: Optional[str] = None
    original_b_name: Optional[str] = None
    output_dir: Optional[Path] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'pair_name': self.pair_name,
            'success': self.success,
            'file_a_output': str(self.file_a_output) if self.file_a_output else None,
            'file_b_output': str(self.file_b_output) if self.file_b_output else None,
            'original_a_name': self.original_a_name,
            'original_b_name': self.original_b_name,
            'output_dir': str(self.output_dir) if self.output_dir else None,
            'error_message': self.error_message,
            'error_details': self.error_details
        }


@dataclass
class ProcessingResults:
    """Collection of processing results"""
    results: Dict[str, ProcessingResult]
    working_dir: Path
    
    @property
    def successful_pairs(self) -> Dict[str, ProcessingResult]:
        """Get only successful results"""
        return {k: v for k, v in self.results.items() if v.success}
    
    @property
    def failed_pairs(self) -> Dict[str, ProcessingResult]:
        """Get only failed results"""
        return {k: v for k, v in self.results.items() if not v.success}
    
    @property
    def success_count(self) -> int:
        """Count of successful pairs"""
        return len(self.successful_pairs)
    
    @property
    def total_count(self) -> int:
        """Total count of pairs"""
        return len(self.results)


class SessionState:
    """Centralized session state management"""
    
    # Session state keys
    PROCESSING_STARTED = 'processing_started'
    PROCESSING_COMPLETED = 'processing_completed'
    PROCESSING_RESULTS = 'processing_results'
    WORKING_DIR = 'working_dir'
    
    @staticmethod
    def get_processing_started() -> bool:
        """Check if processing has started"""
        return st.session_state.get(SessionState.PROCESSING_STARTED, False)
    
    @staticmethod
    def set_processing_started(value: bool) -> None:
        """Set processing started flag"""
        st.session_state[SessionState.PROCESSING_STARTED] = value
    
    @staticmethod
    def get_processing_completed() -> bool:
        """Check if processing is completed"""
        return st.session_state.get(SessionState.PROCESSING_COMPLETED, False)
    
    @staticmethod
    def set_processing_completed(value: bool) -> None:
        """Set processing completed flag"""
        st.session_state[SessionState.PROCESSING_COMPLETED] = value
    
    @staticmethod
    def get_processing_results() -> Optional[ProcessingResults]:
        """Get processing results"""
        return st.session_state.get(SessionState.PROCESSING_RESULTS)
    
    @staticmethod
    def set_processing_results(results: ProcessingResults) -> None:
        """Set processing results"""
        st.session_state[SessionState.PROCESSING_RESULTS] = results
    
    @staticmethod
    def clear_all() -> None:
        """Clear all session state"""
        keys_to_clear = [
            SessionState.PROCESSING_STARTED,
            SessionState.PROCESSING_COMPLETED,
            SessionState.PROCESSING_RESULTS,
            SessionState.WORKING_DIR
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]