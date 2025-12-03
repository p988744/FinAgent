import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from finagent.document_processing.loader import DocumentLoader, Document

class TestDocumentLoader(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.loader = DocumentLoader(base_path=self.temp_dir)

    def tearDown(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test DocumentLoader initialization"""
        self.assertEqual(self.loader.base_path, Path(self.temp_dir))
        self.assertTrue(self.loader.base_path.exists())

    def test_load_txt_success(self):
        """Test loading a TXT file successfully"""
        # Create a test file
        test_file = Path(self.temp_dir) / "test.txt"
        test_content = "這是測試內容"
        test_file.write_text(test_content, encoding="utf-8")

        # Load the file
        document = self.loader.load_txt(str(test_file))

        # Verify
        self.assertIsInstance(document, Document)
        self.assertEqual(document.content, test_content)
        self.assertEqual(document.metadata["filename"], "test.txt")
        self.assertIn("file_size", document.metadata)
        self.assertIn("file_modified", document.metadata)
        self.assertIsNotNone(document.id)
        self.assertIsNotNone(document.source)
        self.assertIsNotNone(document.loaded_at)

    def test_load_txt_with_metadata(self):
        """Test loading a TXT file with additional metadata"""
        # Create a test file
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Content", encoding="utf-8")

        # Load with metadata
        custom_metadata = {"source_meta": "test", "category": "legal"}
        document = self.loader.load_txt(str(test_file), metadata=custom_metadata)

        # Verify custom metadata is merged
        self.assertEqual(document.metadata["source_meta"], "test")
        self.assertEqual(document.metadata["category"], "legal")
        self.assertIn("filename", document.metadata)

    def test_load_txt_file_not_found(self):
        """Test loading a non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.loader.load_txt("nonexistent.txt")

    def test_load_directory_success(self):
        """Test loading all TXT files from a directory"""
        # Create multiple test files
        (Path(self.temp_dir) / "file1.txt").write_text("Content 1", encoding="utf-8")
        (Path(self.temp_dir) / "file2.txt").write_text("Content 2", encoding="utf-8")
        (Path(self.temp_dir) / "file3.md").write_text("Not a txt", encoding="utf-8")

        # Load directory
        documents = self.loader.load_directory(self.temp_dir)

        # Verify
        self.assertEqual(len(documents), 2)
        filenames = [doc.metadata["filename"] for doc in documents]
        self.assertIn("file1.txt", filenames)
        self.assertIn("file2.txt", filenames)
        self.assertNotIn("file3.md", filenames)

    def test_load_directory_recursive(self):
        """Test loading files recursively from subdirectories"""
        # Create nested structure
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        (Path(self.temp_dir) / "root.txt").write_text("Root", encoding="utf-8")
        (sub_dir / "sub.txt").write_text("Sub", encoding="utf-8")

        # Load recursively
        documents = self.loader.load_directory(self.temp_dir, recursive=True)

        # Verify
        self.assertEqual(len(documents), 2)
        filenames = [doc.metadata["filename"] for doc in documents]
        self.assertIn("root.txt", filenames)
        self.assertIn("sub.txt", filenames)

    def test_load_directory_non_recursive(self):
        """Test loading files non-recursively (only root directory)"""
        # Create nested structure
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        (Path(self.temp_dir) / "root.txt").write_text("Root", encoding="utf-8")
        (sub_dir / "sub.txt").write_text("Sub", encoding="utf-8")

        # Load non-recursively
        documents = self.loader.load_directory(self.temp_dir, recursive=False)

        # Verify - should only find root.txt
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].metadata["filename"], "root.txt")

    def test_load_directory_empty(self):
        """Test loading from an empty directory"""
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir()

        documents = self.loader.load_directory(str(empty_dir))

        self.assertEqual(len(documents), 0)

    def test_load_directory_with_pattern(self):
        """Test loading files with a specific pattern"""
        # Create files with different extensions
        (Path(self.temp_dir) / "doc1.txt").write_text("TXT", encoding="utf-8")
        (Path(self.temp_dir) / "doc2.log").write_text("LOG", encoding="utf-8")

        # Load with custom pattern
        documents = self.loader.load_directory(self.temp_dir, pattern="*.log")

        # Verify
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].metadata["filename"], "doc2.log")

if __name__ == '__main__':
    unittest.main()
