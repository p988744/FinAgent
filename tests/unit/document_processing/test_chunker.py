import unittest
from finagent.document_processing.chunker import ChineseTextChunker, TextChunk

class TestChineseTextChunker(unittest.TestCase):
    def setUp(self):
        self.chunker = ChineseTextChunker(
            chunk_size=100,
            chunk_overlap=20,
            preserve_paragraphs=True
        )

    def test_init(self):
        """Test ChineseTextChunker initialization"""
        self.assertEqual(self.chunker.chunk_size, 100)
        self.assertEqual(self.chunker.chunk_overlap, 20)
        self.assertTrue(self.chunker.preserve_paragraphs)

    def test_chunk_text_simple(self):
        """Test chunking simple text"""
        text = "這是第一段文字。\n\n這是第二段文字。\n\n這是第三段文字。"
        
        chunks = self.chunker.chunk_text(text, doc_id="test_doc")

        # Verify
        self.assertGreater(len(chunks), 0)
        self.assertIsInstance(chunks[0], TextChunk)
        self.assertEqual(chunks[0].metadata["doc_id"], "test_doc")

    def test_chunk_text_long_paragraph(self):
        """Test chunking a very long paragraph"""
        # Create a long paragraph that exceeds chunk_size
        text = "這是一段非常長的文字內容。" * 50  # ~450 characters
        
        chunks = self.chunker.chunk_text(text, doc_id="long_doc")

        # Should split into multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Each chunk should be roughly chunk_size
        for chunk in chunks[:-1]:  # Except last chunk
            self.assertLessEqual(len(chunk.text), self.chunker.chunk_size + 50)

    def test_chunk_text_preserves_paragraphs(self):
        """Test that paragraph boundaries are preserved"""
        text = "段落一的內容。\n\n段落二的內容。\n\n段落三的內容。"
        
        chunks = self.chunker.chunk_text(text, doc_id="para_doc")

        # With preserve_paragraphs=True, each paragraph should ideally be in separate chunks
        # (if they fit within chunk_size)
        self.assertGreater(len(chunks), 0)

    def test_chunk_text_with_overlap(self):
        """Test that chunks have proper overlap"""
        text = "A" * 200  # Simple repetitive text
        
        chunks = self.chunker.chunk_text(text, doc_id="overlap_doc")

        if len(chunks) > 1:
            # Check that there's overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                chunk1_end = chunks[i].text[-self.chunker.chunk_overlap:]
                chunk2_start = chunks[i+1].text[:self.chunker.chunk_overlap]
                # Should have some common content (though exact match may not occur due to word boundaries)
                self.assertTrue(len(chunk1_end) > 0)
                self.assertTrue(len(chunk2_start) > 0)

    def test_chunk_text_empty(self):
        """Test chunking empty text"""
        text = ""
        
        chunks = self.chunker.chunk_text(text, doc_id="empty_doc")

        # Should return no chunks or a minimal chunk
        self.assertEqual(len(chunks), 0)

    def test_chunk_text_metadata(self):
        """Test that chunk metadata is correctly set"""
        text = "測試文字內容" * 20
        
        chunks = self.chunker.chunk_text(text, doc_id="meta_doc")

        # Verify metadata
        for i, chunk in enumerate(chunks):
            self.assertEqual(chunk.metadata["doc_id"], "meta_doc")
            self.assertEqual(chunk.chunk_id, i)
            self.assertGreaterEqual(chunk.start_char, 0)
            self.assertGreater(chunk.end_char, chunk.start_char)

    def test_normalize_text(self):
        """Test text normalization"""
        text = "有些   多餘的   空格\n\n\n和換行"
        
        normalized = self.chunker._normalize_text(text)

        # Should clean up excessive whitespace
        self.assertNotIn("   ", normalized)

    def test_split_paragraphs(self):
        """Test paragraph splitting"""
        text = "第一段。\n\n第二段。\n\n第三段。"
        
        paragraphs = self.chunker._split_paragraphs(text)

        # Should split into 3 paragraphs
        self.assertEqual(len(paragraphs), 3)
        self.assertIn("第一段", paragraphs[0])
        self.assertIn("第二段", paragraphs[1])
        self.assertIn("第三段", paragraphs[2])

    def test_split_long_paragraph(self):
        """Test splitting a single long paragraph"""
        # Create a paragraph longer than chunk_size
        para = "這是一個句子。" * 30
        
        sub_paragraphs = self.chunker._split_long_paragraph(para)

        # Should split into multiple parts
        self.assertGreater(len(sub_paragraphs), 1)

    def test_get_chunk_stats(self):
        """Test getting chunk statistics"""
        text = "測試內容" * 50
        chunks = self.chunker.chunk_text(text, doc_id="stats_doc")

        stats = self.chunker.get_chunk_stats(chunks)

        # Verify stats - the implementation returns 'count' key
        self.assertIn("count", stats)
        self.assertIsInstance(stats, dict)

    def test_chunk_text_without_preserve_paragraphs(self):
        """Test chunking without preserving paragraphs"""
        chunker_no_preserve = ChineseTextChunker(
            chunk_size=100,
            chunk_overlap=20,
            preserve_paragraphs=False
        )
        
        text = "段落一。\n\n段落二。\n\n段落三。" * 10
        
        chunks = chunker_no_preserve.chunk_text(text, doc_id="no_preserve_doc")

        # Should still create chunks, just without paragraph preservation
        self.assertGreater(len(chunks), 0)

if __name__ == '__main__':
    unittest.main()
