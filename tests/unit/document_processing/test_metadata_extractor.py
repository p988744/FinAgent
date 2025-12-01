import unittest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from finagent.document_processing.metadata_extractor import MetadataExtractor, MetadataExtractionResult

class TestMetadataExtractor(unittest.TestCase):
    def setUp(self):
        # Mock AsyncOpenAI client for new extractor
        with patch("finagent.document_processing.metadata_extractor.AsyncOpenAI") as MockAsyncOpenAI:
            self.mock_openai_client = MockAsyncOpenAI.return_value
            self.mock_chat = self.mock_openai_client.chat
            self.mock_completions = self.mock_chat.completions
            
            self.extractor = MetadataExtractor(use_new_model=True)

    async def test_extract_new_success(self):
        """Test metadata extraction with new model"""
        # Mock LLM response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "title": "測試裁罰案件",
            "description": "這是一個測試裁罰案件",
            "document_type": "裁罰書",
            "issuing_authority": "金管會銀行局",
            "penalty_amount": "新臺幣500萬元",
            "violation_date": "民國110年3月15日",
            "penalty_date": "民國110年6月20日",
            "related_institutions": ["測試銀行"],
            "violation_types": ["洗錢防制缺失"],
            "legal_basis": ["銀行法第61條"],
            "confidence_score": 0.9
        })
        mock_response.choices = [MagicMock(message=mock_message)]
        self.mock_completions.create.return_value = mock_response

        # Extract metadata
        result = await self.extractor.extract_new(
            doc_id="doc1",
            filename="test.txt",
            content="這是測試內容"
        )

        # Verify
        self.assertIsInstance(result, MetadataExtractionResult)
        self.assertEqual(result.title, "測試裁罰案件")
        self.assertEqual(result.document_type, "裁罰書")
        self.assertEqual(result.issuing_authority, "金管會銀行局")
        self.assertGreater(result.confidence_score, 0.8)

    async def test_extract_new_partial_data(self):
        """Test extraction with partial/incomplete metadata"""
        # Mock LLM response with minimal data
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "title": "未知文件",
            "description": "",
            "document_type": "unknown",
            "confidence_score": 0.3
        })
        mock_response.choices = [MagicMock(message=mock_message)]
        self.mock_completions.create.return_value = mock_response

        result = await self.extractor.extract_new(
            doc_id="doc1",
            filename="test.txt",
            content="內容不清楚"
        )

        # Verify
        self.assertEqual(result.title, "未知文件")
        self.assertLess(result.confidence_score, 0.5)

    async def test_extract_new_malformed_json(self):
        """Test handling of malformed JSON response"""
        # Mock malformed JSON response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Not valid JSON"
        mock_response.choices = [MagicMock(message=mock_message)]
        self.mock_completions.create.return_value = mock_response

        # Should handle gracefully
        with self.assertRaises(Exception):
            await self.extractor.extract_new(
                doc_id="doc1",
                filename="test.txt",
                content="測試"
            )

    async def test_extract_new_with_lists(self):
        """Test extraction with list fields (institutions, violations, etc.)"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "title": "多機構裁罰案",
            "related_institutions": ["機構A", "機構B", "機構C"],
            "violation_types": ["違規1", "違規2"],
            "legal_basis": ["法條1", "法條2", "法條3"],
            "confidence_score": 0.95
        })
        mock_response.choices = [MagicMock(message=mock_message)]
        self.mock_completions.create.return_value = mock_response

        result = await self.extractor.extract_new(
            doc_id="doc1",
            filename="test.txt",
            content="多機構內容"
        )

        # Verify lists are parsed correctly
        self.assertEqual(len(result.related_institutions), 3)
        self.assertEqual(len(result.violation_types), 2)
        self.assertEqual(len(result.legal_basis), 3)

    def test_parse_new_json_response_success(self):
        """Test JSON parsing from LLM response"""
        json_str = json.dumps({
            "title": "測試",
            "description": "測試描述",
            "document_type": "裁罰書",
            "extraction_confidence": 0.8
        })

        result = self.extractor._parse_new_json_response(f"```json\n{json_str}\n```")

        self.assertEqual(result["title"], "測試")
        self.assertEqual(result["extraction_confidence"], 0.8)

    def test_parse_new_json_response_with_markdown(self):
        """Test JSON parsing from markdown code block"""
        json_data = {
            "title": "測試",
            "description": "測試描述",
            "document_type": "裁罰書",
            "extraction_confidence": 0.9
        }
        markdown_response = f"Here is the result:\n```json\n{json.dumps(json_data)}\n```\nDone."

        result = self.extractor._parse_new_json_response(markdown_response)

        self.assertEqual(result["title"], "測試")

    def test_parse_new_json_response_plain_json(self):
        """Test JSON parsing from plain JSON (no markdown)"""
        json_data = {
            "title": "Plain",
            "description": "Plain description",
            "document_type": "裁罰書",
            "extraction_confidence": 0.7
        }
        plain_json = json.dumps(json_data)

        result = self.extractor._parse_new_json_response(plain_json)

        self.assertEqual(result["title"], "Plain")

    def test_parse_new_json_response_invalid(self):
        """Test JSON parsing with invalid input"""
        with self.assertRaises(Exception):
            self.extractor._parse_new_json_response("This is not JSON at all")

if __name__ == '__main__':
    unittest.main()
