"""Tests for DXF processor"""

import pytest
import tempfile
import argparse
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.processor import DXFProcessor
from core.models import FilePair, ProcessingResult
from core.exceptions import *
from core.config import DXFProcessingConfig


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = DXFProcessingConfig(
        diff_processor_script=Path("/mock/diff_processor.py"),
        dxf_processor_script=Path("/mock/dxf_processor.py"),
        max_pairs=5,
        timeout_seconds=60
    )
    return config


@pytest.fixture
def mock_file_pair():
    """Mock file pair for testing"""
    mock_file_a = Mock()
    mock_file_a.name = "test_a.dxf"
    
    mock_file_b = Mock()
    mock_file_b.name = "test_b.dxf"
    
    return FilePair(mock_file_a, mock_file_b, "TestPair")


class TestDXFProcessor:
    """Tests for DXFProcessor class"""
    
    def test_initialization(self, mock_config):
        """Test processor initialization"""
        with patch('core.processor.config', mock_config):
            processor = DXFProcessor()
            assert processor.config == mock_config
    
    @patch('core.processor.save_uploadedfile')
    @patch('core.processor.compare_labels_multi')
    def test_compare_labels_success(self, mock_compare, mock_save, mock_config, mock_file_pair):
        """Test successful label comparison"""
        # Setup mocks
        mock_save.return_value = "/tmp/mock_file"
        mock_compare.return_value = b"excel_data"
        
        with patch('core.processor.config', mock_config):
            processor = DXFProcessor()
            result = processor._compare_labels([mock_file_pair])
        
        assert result == b"excel_data"
        assert mock_compare.called
    
    @patch('core.processor.save_uploadedfile')
    @patch('core.processor.compare_labels_multi')
    def test_compare_labels_failure(self, mock_compare, mock_save, mock_config, mock_file_pair):
        """Test label comparison failure"""
        # Setup mocks to fail
        mock_save.return_value = "/tmp/mock_file"
        mock_compare.side_effect = Exception("Comparison failed")
        
        with patch('core.processor.config', mock_config):
            processor = DXFProcessor()
            
            with pytest.raises(ComparisonError):
                processor._compare_labels([mock_file_pair])
    
    @patch('pandas.ExcelFile')
    @patch('pandas.read_excel')
    def test_convert_excel_to_csv_success(self, mock_read_excel, mock_excel_file, mock_config):
        """Test successful Excel to CSV conversion"""
        # Setup mocks
        mock_excel_file.return_value.sheet_names = ['Sheet1', 'Summary', 'Sheet2']
        mock_df = Mock()
        mock_read_excel.return_value = mock_df
        
        with patch('core.processor.config', mock_config):
            processor = DXFProcessor()
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = processor._convert_excel_to_csv(b"excel_data", Path(tmp_dir))
                
                assert len(result) == 2  # Should exclude Summary sheet
                assert 'Sheet1' in result
                assert 'Sheet2' in result
    
    @patch('subprocess.run')
    def test_run_diff_processor_success(self, mock_run, mock_config):
        """Test successful diff processor execution"""
        # Setup mock
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        with patch('core.processor.config', mock_config):
            processor = DXFProcessor()
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                working_dir = Path(tmp_dir)
                csv_path = working_dir / "test.csv"
                csv_path.touch()  # Create empty file
                
                result = processor._run_diff_processor("TestPair", csv_path, working_dir)
                
                assert result.exists()
                assert result.name == "TestPair"
    
    @patch('subprocess.run')
    def test_run_diff_processor_failure(self, mock_run, mock_config):
        """Test diff processor execution failure"""
        # Setup mock to fail
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_run.return_value = mock_result
        
        with patch('core.processor.config', mock_config):
            processor = DXFProcessor()
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                working_dir = Path(tmp_dir)
                csv_path = working_dir / "test.csv"
                csv_path.touch()
                
                with pytest.raises(DiffProcessorError) as exc_info:
                    processor._run_diff_processor("TestPair", csv_path, working_dir)
                
                assert exc_info.value.pair_name == "TestPair"
                assert exc_info.value.stderr == "Error message"


# Integration test example
class TestProcessorIntegration:
    """Integration tests for the complete workflow"""
    
    @patch('core.processor.subprocess.run')
    @patch('core.processor.save_uploadedfile')
    @patch('core.processor.compare_labels_multi')
    @patch('pandas.ExcelFile')
    @patch('pandas.read_excel')
    def test_full_workflow_success(
        self, 
        mock_read_excel, 
        mock_excel_file, 
        mock_compare, 
        mock_save,
        mock_subprocess,
        mock_config,
        mock_file_pair
    ):
        """Test the complete processing workflow"""
        # Setup all mocks for success case
        mock_save.return_value = "/tmp/mock_file"
        mock_compare.return_value = b"excel_data"
        mock_excel_file.return_value.sheet_names = ['TestPair', 'Summary']
        mock_df = Mock()
        mock_read_excel.return_value = mock_df
        
        # Mock subprocess calls
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        with patch('core.processor.config', mock_config):
            processor = DXFProcessor()
            
            def mock_progress(msg):
                print(f"Progress: {msg}")
            
            # This would be a full integration test
            # results = processor.process_file_pairs([mock_file_pair], mock_progress)
            # assert results.success_count == 1


def run_simple_tests():
    """Run tests in a simple way without pytest"""
    print("🧪 DXF Processor Tests")
    print("=" * 50)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Configuration validation
    print("\n📋 Test 1: Configuration Validation")
    try:
        # Test with mock paths (will fail validation, which is expected)
        config = DXFProcessingConfig(
            diff_processor_script=Path("/nonexistent/diff_processor.py"),
            dxf_processor_script=Path("/nonexistent/dxf_processor.py")
        )
        
        try:
            config.validate()
            print("❌ FAIL: Should have failed validation for non-existent files")
            tests_failed += 1
        except FileNotFoundError:
            print("✅ PASS: Correctly detected missing script files")
            tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        tests_failed += 1
    
    # Test 2: Exception creation
    print("\n📋 Test 2: Custom Exceptions")
    try:
        # Test ComparisonError
        error = ComparisonError("Test error", pair_name="TestPair")
        assert error.pair_name == "TestPair"
        assert str(error) == "Test error"
        print("✅ PASS: ComparisonError works correctly")
        tests_passed += 1
        
        # Test DiffProcessorError
        error = DiffProcessorError("Diff error", pair_name="TestPair", stderr="stderr output")
        assert error.pair_name == "TestPair"
        assert error.stderr == "stderr output"
        print("✅ PASS: DiffProcessorError works correctly")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ FAIL: Exception test failed: {e}")
        tests_failed += 1
    
    # Test 3: FilePair model
    print("\n📋 Test 3: Data Models")
    try:
        mock_file_a = Mock()
        mock_file_a.name = "test_a.dxf"
        mock_file_b = Mock()
        mock_file_b.name = "test_b.dxf"
        
        pair = FilePair(mock_file_a, mock_file_b, "TestPair")
        assert pair.pair_name == "TestPair"
        assert pair.file_a.name == "test_a.dxf"
        assert pair.file_b.name == "test_b.dxf"
        print("✅ PASS: FilePair model works correctly")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ FAIL: Data model test failed: {e}")
        tests_failed += 1
    
    # Test 4: ProcessingResult model
    print("\n📋 Test 4: ProcessingResult Model")
    try:
        result = ProcessingResult(
            pair_name="TestPair",
            success=True,
            original_a_name="file_a.dxf",
            original_b_name="file_b.dxf"
        )
        
        result_dict = result.to_dict()
        assert result_dict['pair_name'] == "TestPair"
        assert result_dict['success'] == True
        assert result_dict['original_a_name'] == "file_a.dxf"
        print("✅ PASS: ProcessingResult model works correctly")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ FAIL: ProcessingResult test failed: {e}")
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"📊 Total:  {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed.")
        return 1


def run_pytest_tests():
    """Run tests using pytest"""
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pytest", __file__, "-v"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return result.returncode
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        print("💡 You may need to install pytest: pip install pytest")
        return 1


def main():
    """Main entry point with command line argument handling"""
    parser = argparse.ArgumentParser(
        description='DXF Processor Test Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python test_processor.py                    # シンプルテストを実行
  python test_processor.py --pytest          # pytestを使用してテストを実行
  python test_processor.py --help            # このヘルプを表示

テストの種類:
  1. 設定検証テスト - 設定ファイルの妥当性をチェック
  2. カスタム例外テスト - エラーハンドリングの動作確認
  3. データモデルテスト - FilePairとProcessingResultの動作確認
  4. 統合テスト - 完全なワークフローの動作確認 (pytest使用時)

必要な依存関係:
  - pytest (オプション): pip install pytest
  - mock: 標準ライブラリに含まれています

pytestの高度な使用法:
  pytest test_processor.py -v              # 詳細な出力
  pytest test_processor.py --cov=core      # カバレッジレポート付き
  pytest test_processor.py -k test_name    # 特定のテストのみ実行
        """
    )
    
    parser.add_argument(
        '--pytest', 
        action='store_true',
        help='pytestを使用してテストを実行（より詳細なテスト結果）'
    )
    
    parser.add_argument(
        '--simple', 
        action='store_true',
        help='シンプルテストを実行（pytestが不要）'
    )
    
    args = parser.parse_args()
    
    if args.pytest:
        print("🔬 Running tests with pytest...")
        return run_pytest_tests()
    else:
        print("🧪 Running simple tests...")
        return run_simple_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)