# CLI Scripts Test Guide

**Date:** 2025-01-21
**Version:** v1.1.1
**Test Coverage:** Research CLI + Retrieval CLI

---

## Overview

This guide documents the test cases for both CLI scripts:
- `cli_research.py` - Research workflow with query analysis and planning
- `cli_retrieval.py` - Direct document retrieval with tool selection

Test files are located in:
- [tests/test_cli_research.py](tests/test_cli_research.py)
- [tests/test_cli_retrieval.py](tests/test_cli_retrieval.py)

---

## Test Categories

### 1. Expected Cases (Happy Path)
Tests for normal, expected user behavior and system responses.

### 2. Boundary Cases (Edge Cases)
Tests for unusual inputs, error conditions, and system limits.

---

## Research CLI Test Cases

### Expected Cases

#### Test 1: Factual Query
**Purpose:** Verify factual query with specific entities and dates works correctly.

**Input:**
```python
query = "2020年玉山銀行洗錢防制裁罰"
```

**Expected Behavior:**
- Query analyzer identifies query as "factual"
- Key entities extracted: ["2020年", "玉山銀行", "洗錢防制", "裁罰"]
- Search strategy: "hybrid"
- Plan created with 2+ tasks
- Final response generated with citations

**Validates:**
- ✅ Query analysis working
- ✅ Plan creation
- ✅ Task execution
- ✅ Response generation

---

#### Test 2: Analytical Query
**Purpose:** Verify analytical query requiring synthesis works correctly.

**Input:**
```python
query = "分析銀行業洗錢防制的主要問題"
```

**Expected Behavior:**
- Query analyzer identifies query as "analytical"
- Search strategy: "semantic" (conceptual search)
- Complexity: "medium"
- Multiple sources synthesized in response

**Validates:**
- ✅ Analytical query detection
- ✅ Semantic search selection
- ✅ Multi-source synthesis

---

#### Test 3: Comparative Query
**Purpose:** Verify comparative query with multiple entities works correctly.

**Input:**
```python
query = "比較玉山銀行和台新銀行的裁罰案件"
```

**Expected Behavior:**
- Query analyzer identifies query as "comparative"
- Multiple entities extracted: ["玉山銀行", "台新銀行", "裁罰案件"]
- Multiple search tasks created (one per entity)
- Comparison synthesized in response

**Validates:**
- ✅ Comparative query detection
- ✅ Multi-entity extraction
- ✅ Parallel task execution
- ✅ Comparison synthesis

---

### Boundary Cases

#### Test 4: Empty Query
**Purpose:** Verify system handles empty query gracefully.

**Input:**
```python
query = ""
```

**Expected Behavior:**
- Query analyzer detects unclear query
- Plan may have no tasks or minimal tasks
- Response indicates unclear query or requests clarification
- No system crash

**Validates:**
- ✅ Graceful handling of empty input
- ✅ Appropriate user feedback
- ✅ No exceptions raised

---

#### Test 5: Very Long Query
**Purpose:** Verify system handles very long queries (>500 characters).

**Input:**
```python
query = "我想要查詢關於" + "玉山銀行洗錢防制裁罰案件" * 30  # ~300+ chars
```

**Expected Behavior:**
- Query analyzer processes long query
- Key entities still extracted correctly
- Query may be truncated in search args
- Response generated normally

**Validates:**
- ✅ Long query handling
- ✅ Entity extraction from long text
- ✅ Query truncation if needed

---

#### Test 6: Special Characters
**Purpose:** Verify system handles special characters and symbols.

**Input:**
```python
query = "玉山銀行@#$%裁罰！？（2020年）"
```

**Expected Behavior:**
- Special characters handled gracefully
- Key entities extracted (ignoring special chars)
- Search query cleaned/normalized
- Response generated normally

**Validates:**
- ✅ Special character handling
- ✅ Text normalization
- ✅ Entity extraction robustness

---

#### Test 7: RAG Not Available
**Purpose:** Verify system handles missing RAG system gracefully.

**Input:**
```python
query = "玉山銀行裁罰"
orchestrator.use_rag = False  # RAG unavailable
```

**Expected Behavior:**
- Error message displayed
- No crash
- User informed to index documents

**Validates:**
- ✅ Graceful degradation
- ✅ Clear error messaging
- ✅ User guidance provided

---

#### Test 8: Workflow Execution Error
**Purpose:** Verify system handles errors during workflow execution.

**Input:**
```python
query = "玉山銀行裁罰"
# Simulate exception during execution
```

**Expected Behavior:**
- Error caught and handled
- Partial results may be displayed
- Error message shown
- No system crash

**Validates:**
- ✅ Exception handling
- ✅ Partial result display
- ✅ Error recovery

---

#### Test 9: No Response Generated
**Purpose:** Verify system handles case when no response is generated.

**Input:**
```python
query = "玉山銀行裁罰"
# Reporter returns None
```

**Expected Behavior:**
- Warning message displayed
- User informed no response generated
- No crash

**Validates:**
- ✅ Null response handling
- ✅ User notification
- ✅ Graceful completion

---

#### Test 10: Unicode and Emoji
**Purpose:** Verify system handles unicode characters and emojis.

**Input:**
```python
query = "🏦 玉山銀行 💰 裁罰 📅 2020年"
```

**Expected Behavior:**
- Emojis handled gracefully
- Key entities extracted (ignoring emojis)
- Response generated normally

**Validates:**
- ✅ Unicode handling
- ✅ Emoji filtering
- ✅ Entity extraction robustness

---

#### Test 11: Multiple Tasks Progress
**Purpose:** Verify progress tracking with multiple parallel tasks.

**Input:**
```python
query = "銀行業裁罰案件"
# Plan with 3+ tasks
verbose = True
```

**Expected Behavior:**
- Progress bar displayed
- Each task completion tracked
- Final progress = 100%
- All tasks executed

**Validates:**
- ✅ Progress tracking
- ✅ Parallel task execution
- ✅ Progress bar accuracy
- ✅ Verbose mode output

---

## Retrieval CLI Test Cases

### Expected Cases

#### Test 1: Auto Mode Factual Query
**Purpose:** Verify auto mode selects hybrid search for factual query.

**Input:**
```python
query = "2020年玉山銀行洗錢防制裁罰"
tool_choice = "auto"
```

**Expected Behavior:**
- Query analyzer invoked
- Analysis shows: type=factual, strategy=hybrid
- Hybrid search tool selected automatically
- Results returned

**Validates:**
- ✅ Auto mode working
- ✅ Query analysis integration
- ✅ Correct tool selection
- ✅ Search execution

---

#### Test 2: Manual Semantic Search
**Purpose:** Verify manual semantic search selection works.

**Input:**
```python
query = "分析銀行業洗錢防制的主要問題"
tool_choice = "semantic"
```

**Expected Behavior:**
- Semantic search tool used
- Query analyzer NOT invoked (manual mode)
- Conceptual results returned
- Results formatted correctly

**Validates:**
- ✅ Manual tool selection
- ✅ Semantic search execution
- ✅ Result formatting

---

#### Test 3: Manual Keyword Search
**Purpose:** Verify manual keyword search selection works.

**Input:**
```python
query = "金管會 裁罰 玉山銀行"
tool_choice = "keyword"
```

**Expected Behavior:**
- Keyword search tool used
- Keywords extracted from query
- Boolean AND search performed
- Results with ALL keywords returned

**Validates:**
- ✅ Keyword extraction
- ✅ Boolean AND search
- ✅ Result filtering

---

#### Test 4: Manual Hybrid Search
**Purpose:** Verify manual hybrid search selection works.

**Input:**
```python
query = "2020年銀行洗錢防制"
tool_choice = "hybrid"
num_results = 7
```

**Expected Behavior:**
- Hybrid search tool used (60% semantic, 40% keyword)
- Query analyzer NOT invoked
- Combined results returned
- Correct number of results (7)

**Validates:**
- ✅ Hybrid search execution
- ✅ Weight distribution (60/40)
- ✅ Result count control

---

### Boundary Cases

#### Test 5: Empty Query
**Purpose:** Verify system handles empty query gracefully.

**Input:**
```python
query = ""
tool_choice = "hybrid"
```

**Expected Behavior:**
- No crash
- Empty results or error message
- Graceful handling

**Validates:**
- ✅ Empty input handling
- ✅ Error messaging

---

#### Test 6: Very Long Query
**Purpose:** Verify system handles very long queries (>1000 characters).

**Input:**
```python
query = "玉山銀行洗錢防制裁罰案件" * 100  # ~1000+ chars
```

**Expected Behavior:**
- Query processed (may be truncated)
- Search executed
- Results returned

**Validates:**
- ✅ Long query handling
- ✅ Query truncation if needed

---

#### Test 7: Single Character Query
**Purpose:** Verify system handles single character query.

**Input:**
```python
query = "銀"
```

**Expected Behavior:**
- Single character processed
- Search executed (may return many results)
- No crash

**Validates:**
- ✅ Minimal input handling
- ✅ Search execution

---

#### Test 8: Collection Not Exists
**Purpose:** Verify system handles missing vector database gracefully.

**Input:**
```python
query = "玉山銀行裁罰"
# collection_exists() returns False
```

**Expected Behavior:**
- Error message displayed
- User informed to run indexing
- No search attempted
- No crash

**Validates:**
- ✅ Collection existence check
- ✅ Error messaging
- ✅ User guidance

---

#### Test 9: Invalid Tool Choice
**Purpose:** Verify system handles invalid tool parameter.

**Input:**
```python
query = "玉山銀行裁罰"
tool_choice = "invalid_tool"
```

**Expected Behavior:**
- Error message displayed
- Available tools listed
- No crash

**Validates:**
- ✅ Input validation
- ✅ Error messaging
- ✅ Help information

---

#### Test 10: Num Results Edge Cases
**Purpose:** Verify system handles edge cases for num_results.

**Input:**
```python
# Test 1: num_results = 1 (minimum)
# Test 2: num_results = 100 (large)
```

**Expected Behavior:**
- Both cases handled correctly
- Correct number of results returned
- No crash

**Validates:**
- ✅ Parameter validation
- ✅ Result count control
- ✅ Edge value handling

---

#### Test 11: Search Tool Exception
**Purpose:** Verify system handles exceptions during search.

**Input:**
```python
query = "玉山銀行裁罰"
# Simulate search exception
```

**Expected Behavior:**
- Exception caught
- Error message displayed
- Stack trace shown (for debugging)
- No system crash

**Validates:**
- ✅ Exception handling
- ✅ Error reporting
- ✅ Graceful degradation

---

#### Test 12: Query with Only Stopwords
**Purpose:** Verify system handles query with only stopwords.

**Input:**
```python
query = "的 是 在 有 和"  # Common Chinese stopwords
```

**Expected Behavior:**
- Query processed
- Results may be limited/empty
- No crash

**Validates:**
- ✅ Stopword handling
- ✅ Empty result handling

---

#### Test 13: Mixed Languages
**Purpose:** Verify system handles mixed Chinese and English.

**Input:**
```python
query = "玉山銀行 anti-money laundering penalties 2020"
```

**Expected Behavior:**
- Both languages processed
- Bilingual search performed
- Results returned

**Validates:**
- ✅ Multilingual support
- ✅ Mixed language processing

---

### Auto Mode Selection Tests

#### Test 14: Auto Mode Selects Semantic
**Purpose:** Verify auto mode selects semantic for analytical queries.

**Input:**
```python
query = "分析金融業法規遵循的挑戰"
tool_choice = "auto"
```

**Expected Behavior:**
- Query analyzer invoked
- Analysis: type=analytical, strategy=semantic
- Semantic tool selected
- Conceptual results returned

**Validates:**
- ✅ Analytical query detection
- ✅ Semantic tool selection
- ✅ Auto mode intelligence

---

#### Test 15: Auto Mode Selects Keyword
**Purpose:** Verify auto mode selects keyword when explicitly requested.

**Input:**
```python
query = "找出包含「金管會」和「裁罰」的所有文件"
tool_choice = "auto"
```

**Expected Behavior:**
- Query analyzer invoked
- Analysis: type=keyword_search, strategy=keyword
- Keyword tool selected
- Exact match results returned

**Validates:**
- ✅ Explicit keyword request detection
- ✅ Keyword tool selection
- ✅ Boolean AND search

---

## Running the Tests

### Run All Tests
```bash
# Run all CLI tests
uv run pytest tests/test_cli_research.py tests/test_cli_retrieval.py -v

# Run with coverage
uv run pytest tests/test_cli_research.py tests/test_cli_retrieval.py --cov=scripts --cov-report=html
```

### Run Specific Test Categories
```bash
# Run only expected cases for research CLI
uv run pytest tests/test_cli_research.py::TestCLIResearchExpectedCases -v

# Run only boundary cases for retrieval CLI
uv run pytest tests/test_cli_retrieval.py::TestCLIRetrievalBoundaryCases -v

# Run specific test
uv run pytest tests/test_cli_research.py::TestCLIResearchExpectedCases::test_factual_query -v
```

### Run Tests with Output
```bash
# Show print statements
uv run pytest tests/test_cli_research.py -v -s

# Show detailed output
uv run pytest tests/test_cli_retrieval.py -v -s --tb=short
```

---

## Test Coverage Summary

### Research CLI Coverage

| Category | Test Cases | Coverage |
|----------|-----------|----------|
| **Expected Cases** | 3 | Factual, Analytical, Comparative queries |
| **Boundary Cases** | 8 | Empty, Long, Special chars, Errors, Unicode, Progress |
| **Total** | 11 | Full workflow coverage |

**Coverage Areas:**
- ✅ Query analysis integration
- ✅ Plan creation and display
- ✅ Progress tracking
- ✅ Error handling
- ✅ Response generation
- ✅ Verbose mode
- ✅ Edge cases

---

### Retrieval CLI Coverage

| Category | Test Cases | Coverage |
|----------|-----------|----------|
| **Expected Cases** | 4 | Auto, Semantic, Keyword, Hybrid modes |
| **Boundary Cases** | 9 | Empty, Long, Single char, Errors, Edge values |
| **Auto Mode** | 2 | Semantic/Keyword selection logic |
| **Total** | 15 | Full tool coverage |

**Coverage Areas:**
- ✅ Auto mode with query analyzer
- ✅ Manual tool selection (all 3 tools)
- ✅ Tool selection logic
- ✅ Error handling
- ✅ Collection existence check
- ✅ Parameter validation
- ✅ Edge cases
- ✅ Multilingual support

---

## Mock Strategy

Both test files use extensive mocking to isolate the CLI scripts from dependencies:

### Research CLI Mocks
1. **AgentOrchestrator** - Mocked to control workflow events
2. **Query Analyzer** - Returns predefined QueryInsight objects
3. **Plan** - Returns predefined Plan with tasks
4. **Stream Events** - Simulated async generator

### Retrieval CLI Mocks
1. **DocumentRetriever** - Mocked for collection checks
2. **HardSearcher** - Mocked for keyword search
3. **QueryAnalyzerAgent** - Returns predefined QueryInsight
4. **All Tool Classes** - Mocked for execution control
   - RetrieverTool (semantic)
   - HardSearchTool (keyword)
   - HybridRetrieverTool (hybrid)

---

## Expected Test Results

### Success Criteria
- ✅ All expected cases pass (100%)
- ✅ All boundary cases handled gracefully (no crashes)
- ✅ Appropriate error messages for invalid inputs
- ✅ Progress tracking works correctly
- ✅ Tool selection logic correct

### Known Limitations
- Tests use mocks, not real RAG system
- Integration tests needed for end-to-end validation
- Performance tests not included (focus on functionality)

---

## Adding New Tests

### Template for Expected Case
```python
@pytest.mark.asyncio
async def test_your_new_case(self):
    """Test description."""
    from scripts.cli_research import research_query

    query_text = "your test query"

    with patch("scripts.cli_research.AgentOrchestrator") as mock_orchestrator:
        # Setup mocks
        mock_instance = MagicMock()

        # Define expected behavior
        async def mock_stream():
            yield "query_analyzer", {"query_insight": ...}
            yield "planner", {"plan": ...}
            yield "reporter", {"response": ...}

        mock_instance.stream_query.return_value = mock_stream()
        mock_orchestrator.return_value = mock_instance

        # Execute
        await research_query(query_text, verbose=False)

        # Assert
        mock_orchestrator.assert_called_once()
```

### Template for Boundary Case
```python
@pytest.mark.asyncio
async def test_your_boundary_case(self):
    """Test edge case description."""
    from scripts.cli_retrieval import retrieval_search

    query_text = "edge case input"

    with patch("scripts.cli_retrieval.DocumentRetriever") as mock_retriever_class:
        # Setup for failure/edge condition
        mock_retriever = MagicMock()
        mock_retriever.collection_exists.return_value = False
        mock_retriever_class.return_value = mock_retriever

        # Should handle gracefully
        await retrieval_search(query_text, tool_choice="auto", num_results=5)

        # Verify graceful handling (no exceptions)
```

---

## Continuous Integration

### GitHub Actions (Recommended)
```yaml
- name: Run CLI Tests
  run: |
    uv run pytest tests/test_cli_research.py tests/test_cli_retrieval.py -v --cov=scripts
```

### Pre-commit Hook (Recommended)
```bash
#!/bin/bash
uv run pytest tests/test_cli_research.py tests/test_cli_retrieval.py --tb=short
```

---

## Troubleshooting Tests

### Issue: Tests Fail with Import Errors
**Solution:** Ensure `src` is in Python path
```python
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

### Issue: Async Tests Not Running
**Solution:** Ensure `pytest-asyncio` is installed
```bash
uv pip install pytest-asyncio
```

### Issue: Mock Not Working
**Solution:** Check patch path matches import path in script
```python
# Script uses: from scripts.cli_research import AgentOrchestrator
# Patch should be: @patch("scripts.cli_research.AgentOrchestrator")
```

---

## Next Steps

1. **Run Tests Locally** - Verify all tests pass
2. **Add Integration Tests** - Test with real RAG system
3. **Add Performance Tests** - Test with large queries/datasets
4. **Add E2E Tests** - Test full user workflows
5. **CI/CD Integration** - Add to GitHub Actions

---

## Changelog

**v1.1.1 (2025-01-21)**
- ✅ Created 11 test cases for Research CLI
- ✅ Created 15 test cases for Retrieval CLI
- ✅ Comprehensive coverage of expected and boundary cases
- ✅ Mock-based testing for isolation
- ✅ Test documentation created

---

**Need Help?**
- See test files for implementation details
- Check [CLI_TOOLS_GUIDE.md](CLI_TOOLS_GUIDE.md) for CLI usage
- Check [QUERY_ANALYZER_FEATURE.md](QUERY_ANALYZER_FEATURE.md) for feature details
