"""Custom exceptions for DXF processing"""


class DXFProcessingError(Exception):
    """Base exception for DXF processing errors"""
    pass


class ComparisonError(DXFProcessingError):
    """Error during label comparison step"""
    def __init__(self, message: str, pair_name: str = None):
        self.pair_name = pair_name
        super().__init__(message)


class ExcelConversionError(DXFProcessingError):
    """Error during Excel to CSV conversion"""
    pass


class DiffProcessorError(DXFProcessingError):
    """Error during diff_label_processor execution"""
    def __init__(self, message: str, pair_name: str, stderr: str = None):
        self.pair_name = pair_name
        self.stderr = stderr
        super().__init__(message)


class DXFProcessorError(DXFProcessingError):
    """Error during dxf_processor execution"""
    def __init__(self, message: str, pair_name: str, file_type: str, stderr: str = None):
        self.pair_name = pair_name
        self.file_type = file_type  # 'A' or 'B'
        self.stderr = stderr
        super().__init__(message)


class ArchiveError(DXFProcessingError):
    """Error during ZIP archive creation"""
    def __init__(self, message: str, pair_name: str = None):
        self.pair_name = pair_name
        super().__init__(message)