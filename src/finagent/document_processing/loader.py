"""
Document loader for reading legal documents from various sources.

MVP: Supports TXT files
Future: PDF, HTML, databases
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class Document(BaseModel):
    """Represents a loaded document."""

    id: str  # Unique document identifier
    content: str  # Full text content
    metadata: dict[str, Any]  # Document metadata
    source: str  # Source file path or URL
    loaded_at: datetime  # When document was loaded

    class Config:
        arbitrary_types_allowed = True


class DocumentLoader:
    """Loads documents from various sources."""

    def __init__(self, base_path: str | None = None):
        """
        Initialize document loader.

        Args:
            base_path: Base directory for document files (default: ./data/documents)
        """
        self.base_path = Path(base_path or "./data/documents")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def load_txt(self, file_path: str, metadata: dict[str, Any] | None = None) -> Document:
        """
        Load a TXT file.

        Args:
            file_path: Path to TXT file (relative to base_path or absolute)
            metadata: Optional metadata dict

        Returns:
            Document object

        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file encoding is not UTF-8
        """
        # Resolve path
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Read file content
        with open(path, encoding="utf-8") as f:
            content = f.read()

        # Extract default metadata from filename/path
        default_metadata = {
            "filename": path.name,
            "file_extension": path.suffix,
            "file_size": path.stat().st_size,
            "file_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }

        # Merge with provided metadata
        if metadata:
            default_metadata.update(metadata)

        # Generate document ID from path
        doc_id = self._generate_doc_id(path)

        return Document(
            id=doc_id,
            content=content,
            metadata=default_metadata,
            source=str(path),
            loaded_at=datetime.now(),
        )

    def load_directory(
        self, directory: str, pattern: str = "*.txt", recursive: bool = False
    ) -> list[Document]:
        """
        Load all matching files from a directory.

        Args:
            directory: Directory path
            pattern: Glob pattern for files (default: *.txt)
            recursive: Whether to search recursively

        Returns:
            List of Document objects
        """
        dir_path = Path(directory)
        if not dir_path.is_absolute():
            dir_path = self.base_path / dir_path

        if not dir_path.exists() or not dir_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_path}")

        # Find matching files
        if recursive:
            file_paths = dir_path.rglob(pattern)
        else:
            file_paths = dir_path.glob(pattern)

        # Load all files
        documents = []
        for file_path in file_paths:
            try:
                doc = self.load_txt(str(file_path))
                documents.append(doc)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
                continue

        return documents

    def _generate_doc_id(self, path: Path) -> str:
        """
        Generate a unique document ID from path.

        Args:
            path: File path

        Returns:
            Document ID (e.g., "doc_filename_hash")
        """
        # Simple ID: filename without extension + hash of path
        import hashlib

        path_hash = hashlib.md5(str(path).encode()).hexdigest()[:8]
        filename = path.stem  # Filename without extension
        return f"doc_{filename}_{path_hash}"

    def get_document_info(self, file_path: str) -> dict[str, Any]:
        """
        Get document info without loading full content.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        stat = path.stat()
        return {
            "path": str(path),
            "filename": path.name,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "extension": path.suffix,
        }
