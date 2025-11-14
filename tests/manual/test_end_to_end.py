#!/usr/bin/env python3
"""
End-to-End Test Scenario with Clear Expectations

This test verifies the entire FinAgent pipeline from document ingestion
to concept-based retrieval with specific success criteria for each step.
"""

import sqlite3
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class TestScenario:
    """End-to-end test scenario with expectations."""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.db_path = self.base_dir / "data" / "finagent.db"
        self.vector_db_path = self.base_dir / "data" / "vector_db" / "chroma.sqlite3"
        self.docs_path = self.base_dir / "data" / "documents"

        self.results = []
        self.total_tests = 0
        self.passed_tests = 0

    def log_test(self, step: str, expectation: str, actual: str, passed: bool):
        """Log test result."""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1

        self.results.append({
            "step": step,
            "expectation": expectation,
            "actual": actual,
            "passed": passed
        })

    def run_test(self, step_name: str, test_func, expectation: str):
        """Run a test step."""
        console.print(f"\n[cyan]Testing:[/cyan] {step_name}")
        console.print(f"[dim]Expected: {expectation}[/dim]")

        try:
            actual, passed = test_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            console.print(f"[dim]Actual: {actual}[/dim]")
            console.print(f"{status}")

            self.log_test(step_name, expectation, actual, passed)
            return passed

        except Exception as e:
            console.print(f"[red]❌ ERROR: {e}[/red]")
            self.log_test(step_name, expectation, f"Error: {str(e)}", False)
            return False

    def print_summary(self):
        """Print test summary."""
        console.print()
        console.print("=" * 100, style="bold cyan")
        console.print("TEST SUMMARY", style="bold cyan")
        console.print("=" * 100, style="bold cyan")
        console.print()

        # Summary table
        summary_table = Table(show_header=True)
        summary_table.add_column("#", style="dim", width=4)
        summary_table.add_column("Step", style="cyan", width=40)
        summary_table.add_column("Expected", style="yellow", width=25)
        summary_table.add_column("Actual", style="blue", width=25)
        summary_table.add_column("Result", style="bold", width=8)

        for i, result in enumerate(self.results, 1):
            status = "[green]✅ PASS[/green]" if result["passed"] else "[red]❌ FAIL[/red]"
            summary_table.add_row(
                str(i),
                result["step"][:37] + "..." if len(result["step"]) > 40 else result["step"],
                result["expectation"][:22] + "..." if len(result["expectation"]) > 25 else result["expectation"],
                result["actual"][:22] + "..." if len(result["actual"]) > 25 else result["actual"],
                status
            )

        console.print(summary_table)
        console.print()

        # Overall result
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        console.print(f"[bold]Overall Result:[/bold] {self.passed_tests}/{self.total_tests} tests passed ({pass_rate:.1f}%)")
        console.print()

        if self.passed_tests == self.total_tests:
            console.print("[bold green]✅ ALL TESTS PASSED[/bold green]")
        else:
            console.print(f"[bold yellow]⚠️  {self.total_tests - self.passed_tests} TEST(S) FAILED[/bold yellow]")

        console.print()
        console.print("=" * 100, style="bold cyan")
        console.print()


def test_step_1_database_exists(scenario: TestScenario) -> bool:
    """Step 1: Verify database files exist."""

    def test():
        db_exists = scenario.db_path.exists()
        vector_db_exists = scenario.vector_db_path.exists()
        passed = db_exists and vector_db_exists
        actual = f"finagent.db: {db_exists}, chroma.sqlite3: {vector_db_exists}"
        return actual, passed

    return scenario.run_test(
        "Database files exist",
        test,
        "Both databases exist"
    )


def test_step_2_documents_indexed(scenario: TestScenario) -> bool:
    """Step 2: Verify documents are indexed."""

    def test():
        from finagent.database.db import Database
        db = Database()
        all_docs = db.get_all_documents()
        indexed_docs = [d for d in all_docs if d.indexed]

        passed = len(indexed_docs) >= 10  # At least 10 docs from our test
        actual = f"{len(indexed_docs)} indexed (out of {len(all_docs)} total)"
        return actual, passed

    return scenario.run_test(
        "Documents indexed in database",
        test,
        ">= 10 documents indexed"
    )


def test_step_3_document_metadata(scenario: TestScenario) -> bool:
    """Step 3: Verify documents have proper metadata."""

    def test():
        from finagent.database.db import Database
        db = Database()
        all_docs = db.get_all_documents()

        # Check metadata quality
        docs_with_type = [d for d in all_docs if d.document_type and d.document_type != "未分類"]
        docs_with_authority = [d for d in all_docs if d.issuing_authority]
        docs_with_keywords = [d for d in all_docs if d.keywords and len(d.keywords) > 0]

        type_rate = len(docs_with_type) / len(all_docs) if all_docs else 0
        auth_rate = len(docs_with_authority) / len(all_docs) if all_docs else 0
        keyword_rate = len(docs_with_keywords) / len(all_docs) if all_docs else 0

        passed = type_rate > 0.8  # 80% should have proper type
        actual = f"Type: {type_rate*100:.0f}%, Auth: {auth_rate*100:.0f}%, Keywords: {keyword_rate*100:.0f}%"
        return actual, passed

    return scenario.run_test(
        "Documents have quality metadata",
        test,
        ">= 80% have document type"
    )


def test_step_4_vector_embeddings(scenario: TestScenario) -> bool:
    """Step 4: Verify vector embeddings created."""

    def test():
        with sqlite3.connect(scenario.vector_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
            embedding_count = cursor.fetchone()[0]

        passed = embedding_count >= 50  # At least 50 chunks from 10 docs
        actual = f"{embedding_count} embeddings"
        return actual, passed

    return scenario.run_test(
        "Vector embeddings created",
        test,
        ">= 50 embeddings"
    )


def test_step_5_chunks_match_metadata(scenario: TestScenario) -> bool:
    """Step 5: Verify chunk counts match between DB and vector DB."""

    def test():
        from finagent.database.db import Database
        db = Database()

        # Get chunk count from metadata
        stats = db.get_document_statistics()
        metadata_chunks = stats.get("total_chunks", 0)

        # Get chunk count from vector DB
        with sqlite3.connect(scenario.vector_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
            vector_chunks = cursor.fetchone()[0]

        # Allow small discrepancy (within 10%)
        difference = abs(metadata_chunks - vector_chunks)
        tolerance = metadata_chunks * 0.1
        passed = difference <= tolerance

        actual = f"Metadata: {metadata_chunks}, Vector: {vector_chunks} (diff: {difference})"
        return actual, passed

    return scenario.run_test(
        "Chunk counts are consistent",
        test,
        "Within 10% difference"
    )


def test_step_6_concepts_extracted(scenario: TestScenario) -> bool:
    """Step 6: Verify concepts extracted."""

    def test():
        from finagent.database.db import Database
        db = Database()
        concepts = db.get_all_concepts()

        passed = len(concepts) >= 20  # At least 20 concepts
        actual = f"{len(concepts)} concepts"
        return actual, passed

    return scenario.run_test(
        "Concepts extracted from documents",
        test,
        ">= 20 concepts"
    )


def test_step_7_concept_types(scenario: TestScenario) -> bool:
    """Step 7: Verify concept types are diverse."""

    def test():
        from finagent.database.db import Database
        db = Database()

        # Get concepts by type
        violation_concepts = db.get_concepts_by_type("violation_type")
        authority_concepts = db.get_concepts_by_type("authority")
        institution_concepts = db.get_concepts_by_type("institution")
        topic_concepts = db.get_concepts_by_type("topic")

        # Should have at least 2 types with content
        types_with_content = sum([
            len(violation_concepts) > 0,
            len(authority_concepts) > 0,
            len(institution_concepts) > 0,
            len(topic_concepts) > 0
        ])

        passed = types_with_content >= 2
        actual = f"V:{len(violation_concepts)}, A:{len(authority_concepts)}, I:{len(institution_concepts)}, T:{len(topic_concepts)}"
        return actual, passed

    return scenario.run_test(
        "Concept types are diverse",
        test,
        ">= 2 different types"
    )


def test_step_8_document_concept_links(scenario: TestScenario) -> bool:
    """Step 8: Verify documents linked to concepts."""

    def test():
        from finagent.database.db import Database
        db = Database()

        # Get concept statistics
        stats = db.get_concept_statistics()
        total_mappings = stats.get("total_document_concept_mappings", 0)

        passed = total_mappings >= 50  # At least 50 document-concept links
        actual = f"{total_mappings} document-concept links"
        return actual, passed

    return scenario.run_test(
        "Documents linked to concepts",
        test,
        ">= 50 links"
    )


def test_step_9_top_concepts_meaningful(scenario: TestScenario) -> bool:
    """Step 9: Verify top concepts are meaningful."""

    def test():
        from finagent.database.db import Database
        db = Database()

        top_concepts = db.get_top_concepts(5)

        # Check if top concepts include expected ones
        concept_names = [c.concept_name for c in top_concepts]
        meaningful_concepts = ["金管會", "法規遵循", "作業風險", "洗錢防制", "內線交易", "罰鍰"]

        matches = sum(1 for name in concept_names if any(mc in name for mc in meaningful_concepts))

        passed = matches >= 2  # At least 2 meaningful concepts in top 5
        actual = f"Top: {', '.join(concept_names[:3])} ({matches} meaningful)"
        return actual, passed

    return scenario.run_test(
        "Top concepts are meaningful",
        test,
        ">= 2 relevant concepts in top 5"
    )


def test_step_10_concept_retrieval_works(scenario: TestScenario) -> bool:
    """Step 10: Verify concept-based retrieval works."""

    def test():
        from finagent.retrieval import ConceptRetriever

        retriever = ConceptRetriever()

        # Test concept extraction
        query = "金管會洗錢防制"
        concepts = retriever.extract_query_concepts(query)

        passed = len(concepts) >= 1  # Should extract at least one concept
        actual = f"Extracted: {', '.join(concepts)}"
        return actual, passed

    return scenario.run_test(
        "Concept extraction from query",
        test,
        ">= 1 concept extracted"
    )


def test_step_11_candidate_retrieval(scenario: TestScenario) -> bool:
    """Step 11: Verify candidate document retrieval."""

    def test():
        from finagent.retrieval import ConceptRetriever

        retriever = ConceptRetriever()

        # Get candidates
        query = "金管會洗錢防制"
        candidates, matched_concepts = retriever.get_candidate_documents(query, max_candidates=100)

        passed = len(candidates) >= 5  # Should find at least 5 candidates
        actual = f"{len(candidates)} candidates, matched: {', '.join(matched_concepts[:2])}"
        return actual, passed

    return scenario.run_test(
        "Candidate document retrieval",
        test,
        ">= 5 candidates found"
    )


def test_step_12_concept_context(scenario: TestScenario) -> bool:
    """Step 12: Verify concept context generation."""

    def test():
        from finagent.retrieval import ConceptRetriever

        retriever = ConceptRetriever()

        # Get context
        query = "金管會洗錢防制"
        context = retriever.get_concept_context(query)

        has_concepts = len(context["matched_concepts"]) > 0
        has_types = len(context["concept_types"]) > 0
        has_counts = len(context["document_counts"]) > 0

        passed = has_concepts and has_types and has_counts
        actual = f"{len(context['matched_concepts'])} concepts, {context['total_candidates']} candidates"
        return actual, passed

    return scenario.run_test(
        "Concept context generation",
        test,
        "Context has concepts and metadata"
    )


def test_step_13_search_by_concept_tool(scenario: TestScenario) -> bool:
    """Step 13: Verify search by concept tool works."""

    def test():
        from finagent.retrieval import ConceptRetriever
        from finagent.database.db import Database

        retriever = ConceptRetriever()
        db = Database()

        # Search for a specific concept
        matching_concepts = db.search_concepts("洗錢防制")

        passed = len(matching_concepts) >= 1
        actual = f"Found {len(matching_concepts)} matching concepts"
        return actual, passed

    return scenario.run_test(
        "Search by concept tool",
        test,
        ">= 1 matching concept"
    )


def test_step_14_performance_improvement(scenario: TestScenario) -> bool:
    """Step 14: Verify performance improvement from concept pre-filtering."""

    def test():
        from finagent.retrieval import ConceptRetriever
        from finagent.database.db import Database

        retriever = ConceptRetriever()
        db = Database()

        # Get total documents
        stats = db.get_document_statistics()
        total_docs = stats.get("total_documents", 0)

        # Get candidate documents
        query = "金管會洗錢防制"
        candidates, _ = retriever.get_candidate_documents(query)

        if total_docs > 0 and len(candidates) > 0:
            reduction = (1 - len(candidates) / total_docs) * 100
            passed = reduction > 10  # At least 10% reduction
            actual = f"{reduction:.1f}% reduction ({len(candidates)}/{total_docs} docs)"
        else:
            passed = False
            actual = "Insufficient data"

        return actual, passed

    return scenario.run_test(
        "Performance improvement verified",
        test,
        ">= 10% search space reduction"
    )


def test_step_15_data_integrity(scenario: TestScenario) -> bool:
    """Step 15: Verify no orphaned data."""

    def test():
        from finagent.database.db import Database
        db = Database()

        # Check for orphaned concepts (no documents)
        all_concepts = db.get_all_concepts()
        orphan_concepts = [c for c in all_concepts if c.document_count == 0]

        # Some orphans are OK (from global concept analysis), but not too many
        orphan_rate = len(orphan_concepts) / len(all_concepts) if all_concepts else 0

        passed = orphan_rate < 0.1  # Less than 10% orphans
        actual = f"{len(orphan_concepts)}/{len(all_concepts)} orphans ({orphan_rate*100:.1f}%)"
        return actual, passed

    return scenario.run_test(
        "Data integrity check",
        test,
        "< 10% orphaned concepts"
    )


def main():
    """Run all test steps."""

    console.print()
    console.print("=" * 100, style="bold green")
    console.print("FINAGENT END-TO-END TEST SCENARIO", style="bold green")
    console.print("=" * 100, style="bold green")
    console.print()

    console.print(Panel(
        "[bold]Test Scenario Overview[/bold]\n\n"
        "This test verifies the complete FinAgent pipeline:\n"
        "  1. Database Setup (Steps 1-2)\n"
        "  2. Document Processing (Steps 3-5)\n"
        "  3. Concept Extraction (Steps 6-9)\n"
        "  4. Concept Retrieval (Steps 10-14)\n"
        "  5. Data Quality (Step 15)\n\n"
        "Each step has clear expectations and success criteria.",
        style="cyan"
    ))

    scenario = TestScenario()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running tests...", total=15)

        # Run all test steps
        test_step_1_database_exists(scenario)
        progress.update(task, advance=1)

        test_step_2_documents_indexed(scenario)
        progress.update(task, advance=1)

        test_step_3_document_metadata(scenario)
        progress.update(task, advance=1)

        test_step_4_vector_embeddings(scenario)
        progress.update(task, advance=1)

        test_step_5_chunks_match_metadata(scenario)
        progress.update(task, advance=1)

        test_step_6_concepts_extracted(scenario)
        progress.update(task, advance=1)

        test_step_7_concept_types(scenario)
        progress.update(task, advance=1)

        test_step_8_document_concept_links(scenario)
        progress.update(task, advance=1)

        test_step_9_top_concepts_meaningful(scenario)
        progress.update(task, advance=1)

        test_step_10_concept_retrieval_works(scenario)
        progress.update(task, advance=1)

        test_step_11_candidate_retrieval(scenario)
        progress.update(task, advance=1)

        test_step_12_concept_context(scenario)
        progress.update(task, advance=1)

        test_step_13_search_by_concept_tool(scenario)
        progress.update(task, advance=1)

        test_step_14_performance_improvement(scenario)
        progress.update(task, advance=1)

        test_step_15_data_integrity(scenario)
        progress.update(task, advance=1)

    # Print summary
    scenario.print_summary()

    # Return exit code
    return 0 if scenario.passed_tests == scenario.total_tests else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
