"""Core DXF processing logic"""

import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

from .config import config
from .exceptions import *
from .models import FilePair, ProcessingResult, ProcessingResults
from utils.compare_labels import compare_labels_multi
from common_utils import save_uploadedfile


class DXFProcessor:
    """Main processor for DXF file workflows"""
    
    def __init__(self):
        self.config = config
        self.config.validate()
    
    def process_file_pairs(self, file_pairs: List[FilePair], progress_callback=None) -> ProcessingResults:
        """Process multiple file pairs through the complete workflow"""
        
        # Create working directory
        working_dir = Path(tempfile.mkdtemp())
        results = {}
        
        try:
            # Step 1: Compare labels
            if progress_callback:
                progress_callback("ステップ 1: ラベル比較処理中...")
            
            excel_data = self._compare_labels(file_pairs)
            
            # Step 2: Convert Excel to CSV
            if progress_callback:
                progress_callback("ステップ 2: ExcelからCSVへの変換中...")
            
            csv_files = self._convert_excel_to_csv(excel_data, working_dir)
            
            # Step 3: Process each pair
            file_pairs_dict = self._create_file_pairs_dict(file_pairs)
            
            for pair_name in csv_files.keys():
                try:
                    if progress_callback:
                        progress_callback(f"ステップ 3: {pair_name} ラベル差分処理中...")
                    
                    # Run diff_label_processor
                    output_dir = self._run_diff_processor(pair_name, csv_files[pair_name], working_dir)
                    
                    if progress_callback:
                        progress_callback(f"ステップ 4: {pair_name} DXFファイル処理中...")
                    
                    # Run dxf_processor for both files
                    file_a_output, file_b_output = self._run_dxf_processor(
                        pair_name, file_pairs_dict[pair_name], output_dir
                    )
                    
                    # Success
                    results[pair_name] = ProcessingResult(
                        pair_name=pair_name,
                        success=True,
                        file_a_output=file_a_output,
                        file_b_output=file_b_output,
                        original_a_name=file_pairs_dict[pair_name]['file_a'].name,
                        original_b_name=file_pairs_dict[pair_name]['file_b'].name,
                        output_dir=output_dir
                    )
                    
                except Exception as e:
                    # Failure
                    results[pair_name] = ProcessingResult(
                        pair_name=pair_name,
                        success=False,
                        error_message=str(e),
                        error_details={'exception_type': type(e).__name__}
                    )
                    # Continue processing other pairs
                    continue
            
            if progress_callback:
                progress_callback("全ての処理が正常に完了しました！")
            
            return ProcessingResults(results=results, working_dir=working_dir)
        
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ 処理が失敗しました: {str(e)}")
            raise e
    
    def _compare_labels(self, file_pairs: List[FilePair]) -> bytes:
        """Step 1: Compare labels using compare_labels_multi"""
        try:
            temp_file_pairs = []
            
            for file_a, file_b, pair_name in file_pairs:
                temp_file_a = save_uploadedfile(file_a)
                temp_file_b = save_uploadedfile(file_b)
                temp_file_pairs.append((file_a, file_b, temp_file_a, temp_file_b, pair_name))
            
            return compare_labels_multi(
                temp_file_pairs,
                filter_non_parts=self.config.filter_non_parts,
                sort_order=self.config.sort_order,
                validate_ref_designators=self.config.validate_ref_designators
            )
        
        except Exception as e:
            raise ComparisonError(f"ラベル比較処理でエラーが発生しました: {str(e)}")
    
    def _convert_excel_to_csv(self, excel_data: bytes, working_dir: Path) -> Dict[str, Path]:
        """Step 2: Convert Excel sheets to CSV files"""
        try:
            temp_excel = working_dir / "comparison_results.xlsx"
            with open(temp_excel, 'wb') as f:
                f.write(excel_data)
            
            excel_file = pd.ExcelFile(temp_excel)
            sheet_names = [sheet for sheet in excel_file.sheet_names if sheet != 'Summary']
            
            csv_files = {}
            for sheet_name in sheet_names:
                df = pd.read_excel(temp_excel, sheet_name=sheet_name)
                csv_path = working_dir / f"{sheet_name}.csv"
                df.to_csv(csv_path, index=False)
                csv_files[sheet_name] = csv_path
            
            return csv_files
        
        except Exception as e:
            raise ExcelConversionError(f"Excel変換処理でエラーが発生しました: {str(e)}")
    
    def _create_file_pairs_dict(self, file_pairs: List[FilePair]) -> Dict:
        """Create a dictionary for file pair data"""
        file_pairs_dict = {}
        
        for file_a, file_b, pair_name in file_pairs:
            temp_file_a = save_uploadedfile(file_a)
            temp_file_b = save_uploadedfile(file_b)
            
            file_pairs_dict[pair_name] = {
                'file_a': file_a,
                'file_b': file_b,
                'temp_file_a': temp_file_a,
                'temp_file_b': temp_file_b,
                'file_a_name': Path(file_a.name).stem,
                'file_b_name': Path(file_b.name).stem
            }
        
        return file_pairs_dict
    
    def _run_diff_processor(self, pair_name: str, csv_path: Path, working_dir: Path) -> Path:
        """Step 3: Run diff_label_processor.py"""
        output_dir = working_dir / pair_name
        output_dir.mkdir(exist_ok=True)
        
        cmd = [
            sys.executable,
            str(self.config.diff_processor_script),
            str(csv_path),
            '-o', str(output_dir)
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.config.timeout_seconds
            )
            
            if result.returncode != 0:
                raise DiffProcessorError(
                    f"{pair_name}のdiff_label_processor処理が失敗しました",
                    pair_name=pair_name,
                    stderr=result.stderr
                )
            
            return output_dir
            
        except subprocess.TimeoutExpired:
            raise DiffProcessorError(
                f"{pair_name}のdiff_label_processor処理がタイムアウトしました",
                pair_name=pair_name
            )
    
    def _run_dxf_processor(self, pair_name: str, pair_data: Dict, output_dir: Path) -> Tuple[Path, Path]:
        """Step 4: Run dxf_processor.py for both files"""
        
        # Process File A
        file_a_output = output_dir / f"{pair_data['file_a_name']}_processed.dxf"
        deleted_file = output_dir / f"{pair_name}_deleted.txt"
        modified_a_file = output_dir / f"{pair_name}_modified_a.txt"
        
        cmd_a = [
            sys.executable,
            str(self.config.dxf_processor_script),
            pair_data['temp_file_a'],
            '-o', str(file_a_output),
            '-cc', 'red:"☆"'
        ]
        
        if deleted_file.exists():
            cmd_a.extend(['-tc', f'magenta:{deleted_file}'])
        if modified_a_file.exists():
            cmd_a.extend(['-tc', f'yellow:{modified_a_file}'])
        
        # Process File B
        file_b_output = output_dir / f"{pair_data['file_b_name']}_processed.dxf"
        added_file = output_dir / f"{pair_name}_added.txt"
        modified_b_file = output_dir / f"{pair_name}_modified_b.txt"
        
        cmd_b = [
            sys.executable,
            str(self.config.dxf_processor_script),
            pair_data['temp_file_b'],
            '-o', str(file_b_output),
            '-cc', 'red:"☆"'
        ]
        
        if added_file.exists():
            cmd_b.extend(['-tc', f'cyan:{added_file}'])
        if modified_b_file.exists():
            cmd_b.extend(['-tc', f'yellow:{modified_b_file}'])
        
        # Execute both commands
        try:
            result_a = subprocess.run(
                cmd_a, 
                capture_output=True, 
                text=True, 
                timeout=self.config.timeout_seconds
            )
            
            if result_a.returncode != 0:
                raise DXFProcessorError(
                    f"{pair_name} ファイルAのdxf_processor処理が失敗しました",
                    pair_name=pair_name,
                    file_type='A',
                    stderr=result_a.stderr
                )
            
            result_b = subprocess.run(
                cmd_b, 
                capture_output=True, 
                text=True, 
                timeout=self.config.timeout_seconds
            )
            
            if result_b.returncode != 0:
                raise DXFProcessorError(
                    f"{pair_name} ファイルBのdxf_processor処理が失敗しました",
                    pair_name=pair_name,
                    file_type='B',
                    stderr=result_b.stderr
                )
            
            return file_a_output, file_b_output
            
        except subprocess.TimeoutExpired as e:
            file_type = 'A' if 'file_a_output' in str(e) else 'B'
            raise DXFProcessorError(
                f"{pair_name} ファイル{file_type}のdxf_processor処理がタイムアウトしました",
                pair_name=pair_name,
                file_type=file_type
            )