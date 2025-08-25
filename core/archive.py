"""Archive creation utilities"""

import zipfile
import io
from pathlib import Path
from typing import Dict

from .exceptions import ArchiveError
from .models import ProcessingResults, ProcessingResult


class ArchiveCreator:
    """Handles ZIP archive creation for processed files"""
    
    @staticmethod
    def create_pair_archive(pair_result: ProcessingResult) -> bytes:
        """Create a ZIP archive for a single pair"""
        if not pair_result.success:
            raise ArchiveError(f"ペア {pair_result.pair_name} は処理に成功していません")
        
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                output_dir = Path(pair_result.output_dir)
                
                # Add all files in the directory to the ZIP
                for file_path in output_dir.iterdir():
                    if file_path.is_file():
                        # Use original filenames for DXF files
                        if file_path == pair_result.file_a_output:
                            arcname = f"{pair_result.pair_name}/{pair_result.original_a_name}"
                        elif file_path == pair_result.file_b_output:
                            arcname = f"{pair_result.pair_name}/{pair_result.original_b_name}"
                        else:
                            # For other files (txt, csv), keep original names
                            arcname = f"{pair_result.pair_name}/{file_path.name}"
                        
                        zip_file.write(file_path, arcname)
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
        
        except Exception as e:
            raise ArchiveError(f"ペア {pair_result.pair_name} のアーカイブ作成でエラーが発生しました: {str(e)}")
    
    @staticmethod
    def create_all_pairs_archive(results: ProcessingResults) -> bytes:
        """Create a ZIP archive containing all processed files from all pairs"""
        successful_pairs = results.successful_pairs
        
        if not successful_pairs:
            raise ArchiveError("処理に成功したペアがありません")
        
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for pair_name, result in successful_pairs.items():
                    # Add processed DXF files
                    if result.file_a_output and result.file_a_output.exists():
                        zip_file.write(
                            result.file_a_output, 
                            f"{pair_name}/{result.original_a_name}"
                        )
                    
                    if result.file_b_output and result.file_b_output.exists():
                        zip_file.write(
                            result.file_b_output, 
                            f"{pair_name}/{result.original_b_name}"
                        )
                    
                    # Add label files if they exist
                    output_dir = Path(result.output_dir)
                    for label_file in output_dir.glob("*.txt"):
                        zip_file.write(label_file, f"{pair_name}/{label_file.name}")
                    
                    # Add CSV file if it exists
                    csv_file = output_dir / f"{pair_name}.csv"
                    if csv_file.exists():
                        zip_file.write(csv_file, f"{pair_name}/{csv_file.name}")
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
        
        except Exception as e:
            raise ArchiveError(f"全ペア・アーカイブ作成でエラーが発生しました: {str(e)}")
    
    @staticmethod
    def get_archive_contents(pair_result: ProcessingResult) -> list:
        """Get list of filenames as they will appear in the ZIP archive"""
        if not pair_result.success:
            return []
        
        try:
            output_dir = Path(pair_result.output_dir)
            zip_contents = []
            
            # Add filenames as they will appear in the ZIP
            for file_path in output_dir.iterdir():
                if file_path.is_file():
                    if file_path == pair_result.file_a_output:
                        zip_contents.append(pair_result.original_a_name)
                    elif file_path == pair_result.file_b_output:
                        zip_contents.append(pair_result.original_b_name)
                    else:
                        zip_contents.append(file_path.name)
            
            return sorted(zip_contents)
        
        except Exception:
            return []