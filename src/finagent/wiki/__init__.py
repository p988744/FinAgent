"""
Wiki Generation System for FinAgent

This module provides functionality for organizing documents into a wiki-style
hierarchy with categories, statistics, and relationship detection.

Components:
- CategoryBuilder: Builds hierarchical categories from document metadata
- StatisticsEngine: Calculates statistics and metrics
- RelationshipMapper: Detects relationships between documents
- WikiGenerator: Orchestrates wiki generation process
"""

from finagent.wiki.category_builder import CategoryBuilder
from finagent.wiki.generator import WikiGenerator
from finagent.wiki.relationship_mapper import RelationshipMapper
from finagent.wiki.statistics import StatisticsEngine

__all__ = [
    "CategoryBuilder",
    "StatisticsEngine",
    "RelationshipMapper",
    "WikiGenerator",
]
