"""Celery tasks for FinAgent."""

from finagent.tasks.document_processing import process_document_upload

__all__ = ["process_document_upload"]
