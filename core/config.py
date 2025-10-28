"""Configuration management for DXF Processing Suite"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class DXFProcessingConfig:
    """Configuration for DXF processing workflow"""
    
    # Script paths
    diff_processor_script: Path
    dxf_processor_script: Path
    
    # Processing parameters
    max_pairs: int = 5
    timeout_seconds: int = 120
    
    # Default processing options
    filter_non_parts: bool = False
    sort_order: str = "asc"
    validate_ref_designators: bool = False
    
    @classmethod
    def from_environment(cls) -> 'DXFProcessingConfig':
        """Create configuration from environment variables"""
        
        # Check if we're running in Streamlit Cloud or local environment
        current_dir = Path(__file__).parent.parent.absolute()
        
        # First try local scripts (for Streamlit Cloud standalone deployment)
        diff_script = current_dir / 'scripts' / 'diff_label_processor.py'
        dxf_script = current_dir / 'scripts' / 'dxf_processor.py'
        
        # If not found, try original paths (for local development)
        if not diff_script.exists() or not dxf_script.exists():
            tools_dir = os.getenv(
                'DXF_TOOLS_DIR',
                '/Users/ryozo/Dropbox/Client/ULVAC/ElectricDesignManagement/Tools'
            )
            diff_script = Path(tools_dir) / 'DXF-viewer' / 'diff_label_processor.py'
            dxf_script = Path(tools_dir) / 'DXF-viewer' / 'dxf_processor.py'
        
        return cls(
            diff_processor_script=diff_script,
            dxf_processor_script=dxf_script,
            max_pairs=int(os.getenv('DXF_MAX_PAIRS', '5')),
            timeout_seconds=int(os.getenv('DXF_TIMEOUT', '120'))
        )
    
    def validate(self) -> None:
        """Validate configuration"""
        # In Streamlit Cloud, external scripts may not be available initially
        # Skip validation if running in cloud environment (no local file system access)
        if os.getenv('STREAMLIT_SHARING_MODE') or 'streamlit.app' in os.getenv('SERVER_NAME', ''):
            return
            
        if not self.diff_processor_script.exists():
            raise FileNotFoundError(f"diff_label_processor.py not found: {self.diff_processor_script}")
        
        if not self.dxf_processor_script.exists():
            raise FileNotFoundError(f"dxf_processor.py not found: {self.dxf_processor_script}")
        
        if self.max_pairs < 1 or self.max_pairs > 10:
            raise ValueError("max_pairs must be between 1 and 10")


# Global configuration instance
config = DXFProcessingConfig.from_environment()