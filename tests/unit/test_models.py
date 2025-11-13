"""Tests for Pydantic models."""

import pytest
from datetime import date

from finagent.models.citations import LegalCitation, CitationAuthority, CitationType
from finagent.models.queries import Query, Task, TaskType
from finagent.models.answers import LegalAnswer, ConfidenceLevel


def test_legal_citation_model():
    """Test LegalCitation model."""
    citation = LegalCitation(
        id=1,
        type=CitationType.ENFORCEMENT_DOCUMENT,
        authority=CitationAuthority.PRIMARY,
        title="測試裁罰書",
        formatted_citation="金管會，金管銀法字第123號裁罰書（民國110年1月1日）",
        issuing_authority="金管會",
    )

    assert citation.id == 1
    assert citation.type == CitationType.ENFORCEMENT_DOCUMENT
    assert citation.authority == CitationAuthority.PRIMARY
    assert citation.title == "測試裁罰書"


def test_query_model():
    """Test Query model."""
    query = Query(
        text="玉山銀行在2020年的裁罰記錄",
        max_results=5,
        include_full_documents=False,
    )

    assert query.text == "玉山銀行在2020年的裁罰記錄"
    assert query.max_results == 5
    assert query.include_full_documents is False


def test_query_validation():
    """Test Query model validation."""
    # Test empty text
    with pytest.raises(Exception):
        Query(text="")

    # Test max_results range - should fail validation if above 50
    with pytest.raises(Exception):
        Query(text="test", max_results=100)

    # Test valid max_results
    query = Query(text="test", max_results=50)
    assert query.max_results == 50


def test_task_model():
    """Test Task model."""
    task = Task(
        id=1,
        description="搜尋金管會裁罰案件",
        task_type=TaskType.SEARCH,
        jurisdiction="金管會",
    )

    assert task.id == 1
    assert task.task_type == TaskType.SEARCH
    assert task.jurisdiction == "金管會"
    assert task.done is False


def test_legal_answer_model():
    """Test LegalAnswer model."""
    citation = LegalCitation(
        id=1,
        type=CitationType.ENFORCEMENT_DOCUMENT,
        authority=CitationAuthority.PRIMARY,
        title="測試",
        formatted_citation="測試引用",
    )

    answer = LegalAnswer(
        executive_summary="測試摘要",
        key_findings=["發現1", "發現2"],
        detailed_analysis="詳細分析內容",
        citations=[citation],
        confidence_score=ConfidenceLevel.HIGH,
        confidence_explanation="測試說明",
    )

    assert answer.executive_summary == "測試摘要"
    assert len(answer.key_findings) == 2
    assert len(answer.citations) == 1
    assert answer.confidence_score == ConfidenceLevel.HIGH
