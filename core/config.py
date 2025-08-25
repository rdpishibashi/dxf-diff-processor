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
        
        # Get paths from environment or use defaults
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
        if not self.diff_processor_script.exists():
            raise FileNotFoundError(f"diff_label_processor.py not found: {self.diff_processor_script}")
        
        if not self.dxf_processor_script.exists():
            raise FileNotFoundError(f"dxf_processor.py not found: {self.dxf_processor_script}")
        
        if self.max_pairs < 1 or self.max_pairs > 10:
            raise ValueError("max_pairs must be between 1 and 10")


# Global configuration instance
config = DXFProcessingConfig.from_environment()