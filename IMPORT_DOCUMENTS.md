# How to Import Your Own Documents

## Quick Start (3 Steps)

### Step 1: Prepare Your Documents

Convert your documents to **UTF-8 encoded TXT files** in Traditional Chinese.

```bash
# Place your TXT files in the documents directory
cp your_document.txt backend/data/documents/
```

### Step 2: Run Indexing Script

**Option A: Using CLI (Recommended)**
```bash
uv run finagent
# Then in the REPL:
finagent> /reindex
```

**Option B: Using Script Directly**
```bash
cd backend
uv run python scripts/index_documents.py
```

### Step 3: Query Your Documents

```bash
uv run finagent
# Then type your query in Traditional Chinese
```

---

## Detailed Guide

### 📁 Document Format Requirements

**Supported Format (Current):**
- ✅ **TXT files** (.txt)
- ✅ **Encoding**: UTF-8
- ✅ **Language**: Traditional Chinese (繁體中文)
- ✅ **Content**: Legal documents, enforcement actions, court judgments

**Coming Soon:**
- ⏳ PDF files (.pdf)
- ⏳ HTML pages
- ⏳ DOCX files

### 📝 Document Naming Convention

Use descriptive filenames that include:
1. **Institution/Entity name**
2. **Violation/Case type**
3. **Year**

**Good Examples:**
```
玉山銀行_洗錢防制裁罰_2020.txt
國泰世華銀行_內線交易_2021.txt
台新銀行_資訊揭露違規_2019.txt
中國信託_客戶資料外洩_2022.txt
```

**Bad Examples:**
```
document1.txt        ❌ Not descriptive
案件.txt             ❌ Too generic
penalty.txt          ❌ English, not descriptive
```

### 📂 Document Directory Structure

```
backend/
└── data/
    └── documents/
        ├── 玉山銀行_洗錢防制裁罰_2020.txt
        ├── 國泰世華銀行_內線交易_2021.txt
        ├── 台新銀行_資訊揭露違規_2019.txt
        └── your_new_document.txt  ← Add your files here
```

---

## Method 1: Simple File Copy (Recommended)

### For Single Document

```bash
# 1. Copy your TXT file to documents directory
cp /path/to/your/document.txt backend/data/documents/

# 2. Run indexing
cd backend
uv run python scripts/index_documents.py

# 3. Query!
uv run finagent
```

### For Multiple Documents

```bash
# Copy multiple files at once
cp /path/to/docs/*.txt backend/data/documents/

# Or move them
mv /path/to/docs/*.txt backend/data/documents/

# Then index
cd backend
uv run python scripts/index_documents.py
```

---

## Method 2: Batch Import Script

Create a custom import script for your specific needs:

### Create Import Script

```bash
cd backend
nano scripts/import_my_documents.py
```

**Script Content:**

```python
#!/usr/bin/env python3
"""
Import documents from a custom directory.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing import DocumentLoader, DocumentIndexer


def import_documents(source_dir: str):
    """
    Import documents from source directory.

    Args:
        source_dir: Path to directory containing TXT files
    """
    print(f"🚀 Importing documents from: {source_dir}\n")

    # Initialize
    loader = DocumentLoader(base_path=source_dir)
    indexer = DocumentIndexer()

    # Load documents
    print("📄 Loading documents...")
    documents = loader.load_directory(".", pattern="*.txt", recursive=True)

    if not documents:
        print("❌ No TXT files found!")
        return

    print(f"   Found {len(documents)} documents\n")

    # Index each document
    total_chunks = 0
    for doc in documents:
        filename = doc.metadata.get("filename")
        print(f"   Processing: {filename}")

        if indexer.document_exists(doc.id):
            print(f"   ⚠️  Already indexed, skipping...")
            continue

        chunks = indexer.index_document(doc)
        total_chunks += chunks
        print(f"   ✅ Indexed {chunks} chunks")

    # Summary
    print(f"\n📊 Import complete!")
    print(f"   Total new chunks: {total_chunks}")
    stats = indexer.get_collection_stats()
    print(f"   Total in database: {stats['total_chunks']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_my_documents.py <source_directory>")
        print("\nExample:")
        print("  python scripts/import_my_documents.py /Users/you/Downloads/legal_docs")
        sys.exit(1)

    source_dir = sys.argv[1]
    if not Path(source_dir).exists():
        print(f"❌ Directory not found: {source_dir}")
        sys.exit(1)

    import_documents(source_dir)
```

### Make it Executable

```bash
chmod +x scripts/import_my_documents.py
```

### Use It

```bash
# Import from any directory
uv run python scripts/import_my_documents.py /path/to/your/documents

# Examples:
uv run python scripts/import_my_documents.py ~/Downloads/legal_docs
uv run python scripts/import_my_documents.py /Users/you/Documents/裁罰案件
```

---

## Method 3: Convert Other Formats to TXT

### From PDF

If you have PDF files, convert them to TXT first:

**Option A: Using `pdftotext` (Command Line)**

```bash
# Install pdftotext (if not installed)
brew install poppler  # macOS
# or
sudo apt-get install poppler-utils  # Linux

# Convert single file
pdftotext -enc UTF-8 your_document.pdf backend/data/documents/your_document.txt

# Convert all PDFs in a directory
for file in /path/to/pdfs/*.pdf; do
    pdftotext -enc UTF-8 "$file" "backend/data/documents/$(basename "$file" .pdf).txt"
done
```

**Option B: Using Python Script**

```bash
cd backend
nano scripts/convert_pdf_to_txt.py
```

```python
#!/usr/bin/env python3
"""Convert PDF files to TXT for indexing."""

import sys
from pathlib import Path
import pymupdf  # PyMuPDF


def convert_pdf_to_txt(pdf_path: Path, output_dir: Path):
    """Convert PDF to TXT with UTF-8 encoding."""
    print(f"Converting: {pdf_path.name}")

    doc = pymupdf.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()

    # Save as TXT
    txt_path = output_dir / f"{pdf_path.stem}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"  ✅ Saved: {txt_path.name}")


def main(source_dir: str, output_dir: str):
    source_path = Path(source_dir)
    output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(source_path.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files\n")

    for pdf_file in pdf_files:
        try:
            convert_pdf_to_txt(pdf_file, output_path)
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/convert_pdf_to_txt.py <pdf_dir> <output_dir>")
        print("\nExample:")
        print("  python scripts/convert_pdf_to_txt.py ~/Downloads/pdfs backend/data/documents")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
```

**Use it:**

```bash
uv run python scripts/convert_pdf_to_txt.py ~/Downloads/pdfs backend/data/documents
```

### From Word Documents (.docx)

```bash
# Install python-docx
uv add python-docx

# Convert script
nano scripts/convert_docx_to_txt.py
```

```python
#!/usr/bin/env python3
"""Convert DOCX files to TXT."""

import sys
from pathlib import Path
from docx import Document


def convert_docx_to_txt(docx_path: Path, output_dir: Path):
    """Convert DOCX to TXT."""
    print(f"Converting: {docx_path.name}")

    doc = Document(docx_path)
    text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])

    txt_path = output_dir / f"{docx_path.stem}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"  ✅ Saved: {txt_path.name}")


def main(source_dir: str, output_dir: str):
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for docx_file in source_path.glob("*.docx"):
        try:
            convert_docx_to_txt(docx_file, output_path)
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/convert_docx_to_txt.py <docx_dir> <output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
```

---

## Method 4: Re-indexing (Clear and Start Fresh)

If you want to **clear all existing documents** and start fresh:

### Create Clear Script

```bash
cd backend
nano scripts/clear_and_reindex.py
```

```python
#!/usr/bin/env python3
"""Clear vector database and re-index all documents."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing import DocumentLoader, DocumentIndexer


def main():
    print("🗑️  Clearing vector database...\n")

    # Initialize
    indexer = DocumentIndexer()

    # Clear collection
    indexer.clear_collection()
    print("✅ Vector database cleared!\n")

    # Re-index
    print("🔍 Re-indexing documents...\n")

    base_dir = Path(__file__).parent.parent
    docs_path = base_dir / "data" / "documents"

    loader = DocumentLoader(base_path=str(docs_path))
    documents = loader.load_directory(".", pattern="*.txt")

    print(f"Found {len(documents)} documents\n")

    total_chunks = 0
    for doc in documents:
        filename = doc.metadata.get("filename")
        print(f"  Processing: {filename}")
        chunks = indexer.index_document(doc)
        total_chunks += chunks
        print(f"  ✅ Indexed {chunks} chunks")

    print(f"\n📊 Re-indexing complete!")
    print(f"   Total chunks: {total_chunks}")


if __name__ == "__main__":
    response = input("⚠️  This will DELETE all indexed documents. Continue? (yes/no): ")
    if response.lower() == "yes":
        main()
    else:
        print("Cancelled.")
```

**Use it:**

```bash
uv run python scripts/clear_and_reindex.py
```

---

## Verification & Testing

### Check What's Indexed

```bash
cd backend
uv run python -c "
from finagent.document_processing import DocumentRetriever

retriever = DocumentRetriever()
stats = retriever.get_stats()

print('📊 Database Status:')
print(f\"  Collection: {stats['collection_name']}\")
print(f\"  Total chunks: {stats['total_chunks']}\")
print(f\"  Exists: {stats['exists']}\")
"
```

### List All Indexed Documents

```bash
cd backend
nano scripts/list_documents.py
```

```python
#!/usr/bin/env python3
"""List all indexed documents."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing import DocumentIndexer


def main():
    indexer = DocumentIndexer()

    # Get all unique documents
    results = indexer.collection.get(include=["metadatas"])

    if not results or not results["metadatas"]:
        print("No documents indexed yet.")
        return

    # Extract unique documents
    docs = {}
    for metadata in results["metadatas"]:
        doc_id = metadata.get("doc_id")
        filename = metadata.get("filename", "unknown")
        if doc_id and doc_id not in docs:
            docs[doc_id] = filename

    print(f"📚 Indexed Documents ({len(docs)}):\n")
    for i, (doc_id, filename) in enumerate(docs.items(), 1):
        print(f"  {i}. {filename}")
        print(f"     ID: {doc_id}")


if __name__ == "__main__":
    main()
```

**Use it:**

```bash
uv run python scripts/list_documents.py
```

### Test Query

```bash
# Test if your documents are searchable
uv run finagent query "your search term here"

# Or in REPL
uv run finagent
# Then type your query
```

---

## Troubleshooting

### Problem: "No documents found"

**Solution:**
```bash
# Check files exist
ls -la backend/data/documents/

# Check file encoding
file backend/data/documents/*.txt

# Should show: UTF-8 Unicode text
```

### Problem: "Import failed"

**Solutions:**

1. **Check file encoding:**
```bash
# Convert to UTF-8 if needed
iconv -f BIG5 -t UTF-8 old_file.txt > new_file.txt
```

2. **Check for empty files:**
```bash
# Remove empty files
find backend/data/documents -type f -empty -delete
```

3. **Check API key:**
```bash
# Make sure OpenAI API key is set
grep OPENAI_API_KEY backend/.env
```

### Problem: "Chunks not retrieved"

**Solution:**
```bash
# Re-index with verbose output
cd backend
uv run python scripts/index_documents.py

# Check if chunks were created
uv run python -c "
from finagent.document_processing import DocumentRetriever
r = DocumentRetriever()
print(f'Total chunks: {r.collection.count()}')
"
```

---

## Best Practices

### 1. Document Quality

✅ **Good:**
- Clear, structured text
- Proper paragraph breaks (double newlines)
- Complete sentences
- Legal terminology in Traditional Chinese

❌ **Avoid:**
- Scanned images without OCR
- Corrupted files
- Mixed languages without clear separation
- Excessive whitespace or formatting characters

### 2. Chunking Optimization

The system automatically chunks at **500 characters** with **50 character overlap**.

For better results:
- Use clear section headers (第一章, 第二條, etc.)
- Separate paragraphs with double newlines
- Keep related information together

### 3. Metadata Enhancement

Add metadata to filenames for better organization:

```
[Entity]_[Type]_[Year]_[CaseNumber].txt

Examples:
玉山銀行_洗錢防制裁罰_2020_金管銀法字10900123456.txt
國泰世華_內線交易_2021_110年台上字1234.txt
```

---

## Complete Workflow Example

Let's say you have 10 PDF files of legal documents:

```bash
# 1. Convert PDFs to TXT
uv run python scripts/convert_pdf_to_txt.py ~/Downloads/legal_pdfs backend/data/documents

# 2. Check what was created
ls -lh backend/data/documents/

# 3. Index them
cd backend
uv run python scripts/index_documents.py

# 4. Verify
uv run python scripts/list_documents.py

# 5. Start querying!
uv run finagent
```

---

## Advanced: Programmatic Import

For integration with other systems:

```python
from finagent.document_processing import DocumentLoader, DocumentIndexer

# Initialize
loader = DocumentLoader()
indexer = DocumentIndexer()

# Load and index a single document
doc = loader.load_txt("path/to/document.txt", metadata={
    "case_number": "110年台上字第1234號",
    "institution": "玉山銀行",
    "year": 2020,
    "category": "洗錢防制"
})

# Index it
chunks = indexer.index_document(doc)
print(f"Indexed {chunks} chunks")

# Now it's searchable!
```

---

## Summary

**Simplest Method:**
```bash
# 1. Put TXT files in data/documents/
cp your_docs/*.txt backend/data/documents/

# 2. Index
cd backend && uv run python scripts/index_documents.py

# 3. Query
uv run finagent
```

**For Your Own Data Pipeline:**
- Use Method 2 (batch import script) for automation
- Use Method 3 (conversion scripts) for PDFs/DOCX
- Use Method 4 (clear and reindex) when starting fresh

**Need Help?**
- Check `TEST_RESULTS.md` for troubleshooting
- See `RAG_QUICKSTART.md` for technical details
- Run `uv run finagent query --help` for CLI options

---

🎉 **You're ready to import your own documents!** Start with a few test files and expand from there.
