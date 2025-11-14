#!/usr/bin/env python3
"""Verify database data after reindex - check documents and concepts."""

import sqlite3
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from finagent.database.db import Database

console = Console()


def verify_database():
    """Verify database contents after reindex."""

    console.print()
    console.print("=" * 100, style="bold cyan")
    console.print("DATABASE VERIFICATION REPORT", style="bold cyan")
    console.print("=" * 100, style="bold cyan")
    console.print()

    db = Database()
    base_dir = Path(__file__).parent
    db_path = base_dir / "data" / "finagent.db"
    vector_db_path = base_dir / "data" / "vector_db" / "chroma.sqlite3"

    # ========================================
    # 1. DOCUMENTS TABLE
    # ========================================
    console.print(Panel.fit("📄 DOCUMENTS TABLE", style="bold yellow"))
    console.print()

    all_docs = db.get_all_documents()
    indexed_docs = [d for d in all_docs if d.indexed]
    unindexed_docs = [d for d in all_docs if not d.indexed]

    # Summary
    summary_table = Table(title="Document Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_column("Details", style="yellow")

    summary_table.add_row("Total documents", str(len(all_docs)), "All documents in database")
    summary_table.add_row("Indexed", str(len(indexed_docs)), "indexed=1, ready for queries")
    summary_table.add_row("Not indexed", str(len(unindexed_docs)), "indexed=0, metadata only")

    if all_docs:
        total_chunks = sum(d.chunk_count for d in all_docs)
        avg_chunks = total_chunks / len(all_docs)
        summary_table.add_row("Total chunks", str(total_chunks), f"Avg: {avg_chunks:.1f} per doc")

    console.print(summary_table)
    console.print()

    # Document types breakdown
    doc_types = {}
    for doc in all_docs:
        dtype = doc.document_type or "未分類"
        doc_types[dtype] = doc_types.get(dtype, 0) + 1

    types_table = Table(title="Document Types", show_header=True)
    types_table.add_column("Type", style="cyan")
    types_table.add_column("Count", style="green")
    types_table.add_column("Percentage", style="yellow")

    for dtype, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(all_docs) * 100) if all_docs else 0
        types_table.add_row(dtype, str(count), f"{pct:.1f}%")

    console.print(types_table)
    console.print()

    # Authorities breakdown
    authorities = {}
    for doc in all_docs:
        auth = doc.issuing_authority or "未指定"
        authorities[auth] = authorities.get(auth, 0) + 1

    auth_table = Table(title="Issuing Authorities", show_header=True)
    auth_table.add_column("Authority", style="cyan")
    auth_table.add_column("Count", style="green")
    auth_table.add_column("Percentage", style="yellow")

    for auth, count in sorted(authorities.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = (count / len(all_docs) * 100) if all_docs else 0
        auth_table.add_row(auth, str(count), f"{pct:.1f}%")

    console.print(auth_table)
    console.print()

    # Sample documents
    console.print("[bold]Sample Documents (first 5):[/bold]")
    console.print()

    sample_table = Table(show_header=True)
    sample_table.add_column("Filename", style="cyan", width=40)
    sample_table.add_column("Type", style="yellow", width=12)
    sample_table.add_column("Authority", style="green", width=15)
    sample_table.add_column("Chunks", style="magenta", width=8)
    sample_table.add_column("Indexed", style="blue", width=8)

    for doc in all_docs[:5]:
        filename = doc.filename[:37] + "..." if len(doc.filename) > 40 else doc.filename
        dtype = (doc.document_type or "未分類")[:10]
        auth = (doc.issuing_authority or "未指定")[:13]
        sample_table.add_row(
            filename,
            dtype,
            auth,
            str(doc.chunk_count),
            "✓" if doc.indexed else "✗"
        )

    console.print(sample_table)
    console.print()

    # ========================================
    # 2. CONCEPTS TABLE
    # ========================================
    console.print(Panel.fit("🔗 CONCEPTS TABLE", style="bold yellow"))
    console.print()

    all_concepts = db.get_all_concepts()

    # Concept summary
    concept_summary = Table(title="Concept Summary", show_header=True)
    concept_summary.add_column("Metric", style="cyan")
    concept_summary.add_column("Count", style="green")

    concept_summary.add_row("Total concepts", str(len(all_concepts)))

    if all_concepts:
        total_links = sum(c.document_count for c in all_concepts)
        avg_docs_per_concept = total_links / len(all_concepts)
        concept_summary.add_row("Total document links", str(total_links))
        concept_summary.add_row("Avg docs per concept", f"{avg_docs_per_concept:.1f}")

    console.print(concept_summary)
    console.print()

    # Concept types breakdown
    concept_types = {}
    for concept in all_concepts:
        ctype = concept.concept_type or "未分類"
        concept_types[ctype] = concept_types.get(ctype, 0) + 1

    ctypes_table = Table(title="Concept Types", show_header=True)
    ctypes_table.add_column("Type", style="cyan")
    ctypes_table.add_column("Count", style="green")
    ctypes_table.add_column("Percentage", style="yellow")

    for ctype, count in sorted(concept_types.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(all_concepts) * 100) if all_concepts else 0
        ctypes_table.add_row(ctype, str(count), f"{pct:.1f}%")

    console.print(ctypes_table)
    console.print()

    # Top concepts by document count
    top_concepts = db.get_top_concepts(20)

    top_table = Table(title="Top 20 Concepts by Document Count", show_header=True)
    top_table.add_column("#", style="dim", width=4)
    top_table.add_column("Concept Name", style="cyan", width=40)
    top_table.add_column("Type", style="yellow", width=15)
    top_table.add_column("Docs", style="green", width=8)
    top_table.add_column("Keywords", style="blue", width=30)

    for i, concept in enumerate(top_concepts, 1):
        name = concept.concept_name[:37] + "..." if len(concept.concept_name) > 40 else concept.concept_name
        ctype = (concept.concept_type or "未分類")[:13]
        keywords = ", ".join(concept.keywords[:2]) if concept.keywords else ""
        keywords = keywords[:27] + "..." if len(keywords) > 30 else keywords

        top_table.add_row(
            str(i),
            name,
            ctype,
            str(concept.document_count),
            keywords
        )

    console.print(top_table)
    console.print()

    # Concepts by type
    console.print("[bold]Concepts by Type:[/bold]")
    console.print()

    for ctype in ["violation_type", "authority", "institution", "topic"]:
        concepts_of_type = db.get_concepts_by_type(ctype)
        if concepts_of_type:
            console.print(f"  [cyan]{ctype}[/cyan]: {len(concepts_of_type)} concepts")
            # Show top 5
            for concept in sorted(concepts_of_type, key=lambda c: c.document_count, reverse=True)[:5]:
                console.print(f"    • {concept.concept_name} ({concept.document_count} docs)")
            console.print()

    # ========================================
    # 3. DOCUMENT-CONCEPT LINKS
    # ========================================
    console.print(Panel.fit("🔗 DOCUMENT-CONCEPT MAPPINGS", style="bold yellow"))
    console.print()

    # Sample document with its concepts
    if indexed_docs:
        sample_doc = indexed_docs[0]
        doc_concepts = db.get_document_concepts(sample_doc.doc_id)

        console.print(f"[bold]Sample Document:[/bold] {sample_doc.filename}")
        console.print(f"[dim]Doc ID: {sample_doc.doc_id}[/dim]")
        console.print(f"[dim]Type: {sample_doc.document_type}, Authority: {sample_doc.issuing_authority}[/dim]")
        console.print()
        console.print(f"[bold]Linked Concepts ({len(doc_concepts)}):[/bold]")

        for concept in doc_concepts[:10]:
            console.print(f"  • {concept.concept_name} [{concept.concept_type}]")

        if len(doc_concepts) > 10:
            console.print(f"  ... and {len(doc_concepts) - 10} more")
        console.print()

    # Sample concept with its documents
    if top_concepts:
        sample_concept = top_concepts[0]
        concept_docs = db.get_concept_documents(sample_concept.id)

        console.print(f"[bold]Sample Concept:[/bold] {sample_concept.concept_name}")
        console.print(f"[dim]Type: {sample_concept.concept_type}, Document count: {sample_concept.document_count}[/dim]")
        console.print()
        console.print(f"[bold]Linked Documents ({len(concept_docs)}):[/bold]")

        for doc in concept_docs[:10]:
            console.print(f"  • {doc.filename}")

        if len(concept_docs) > 10:
            console.print(f"  ... and {len(concept_docs) - 10} more")
        console.print()

    # ========================================
    # 4. VECTOR DATABASE
    # ========================================
    console.print(Panel.fit("🔢 VECTOR DATABASE", style="bold yellow"))
    console.print()

    if vector_db_path.exists():
        try:
            with sqlite3.connect(vector_db_path) as conn:
                # Count embeddings
                cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
                embedding_count = cursor.fetchone()[0]

                # Count collections
                cursor = conn.execute("SELECT COUNT(*) FROM collections")
                collection_count = cursor.fetchone()[0]

                vector_table = Table(show_header=True)
                vector_table.add_column("Metric", style="cyan")
                vector_table.add_column("Value", style="green")

                vector_table.add_row("Total embeddings (chunks)", str(embedding_count))
                vector_table.add_row("Collections", str(collection_count))

                if indexed_docs:
                    avg_chunks = embedding_count / len(indexed_docs)
                    vector_table.add_row("Avg chunks per doc", f"{avg_chunks:.1f}")

                console.print(vector_table)
                console.print()

        except Exception as e:
            console.print(f"[red]Error reading vector DB: {e}[/red]")
            console.print()
    else:
        console.print("[yellow]Vector database not found[/yellow]")
        console.print()

    # ========================================
    # 5. DATA QUALITY CHECKS
    # ========================================
    console.print(Panel.fit("✅ DATA QUALITY CHECKS", style="bold yellow"))
    console.print()

    checks = []

    # Check 1: All indexed documents have chunks
    docs_without_chunks = [d for d in indexed_docs if d.chunk_count == 0]
    if docs_without_chunks:
        checks.append(("❌", f"Found {len(docs_without_chunks)} indexed documents with 0 chunks"))
    else:
        checks.append(("✅", f"All {len(indexed_docs)} indexed documents have chunks"))

    # Check 2: Documents have metadata
    docs_without_type = [d for d in all_docs if not d.document_type or d.document_type == "未分類"]
    if len(docs_without_type) > len(all_docs) * 0.5:  # More than 50% unclassified
        checks.append(("⚠️ ", f"{len(docs_without_type)} documents have no type (may need LLM reindex)"))
    else:
        checks.append(("✅", f"Most documents have proper types ({len(all_docs) - len(docs_without_type)}/{len(all_docs)})"))

    # Check 3: Concepts have reasonable document counts
    orphan_concepts = [c for c in all_concepts if c.document_count == 0]
    if orphan_concepts:
        checks.append(("⚠️ ", f"Found {len(orphan_concepts)} concepts with 0 documents"))
    else:
        checks.append(("✅", "All concepts are linked to documents"))

    # Check 4: Top concepts are meaningful
    if top_concepts:
        top_concept_names = [c.concept_name for c in top_concepts[:5]]
        expected_names = ["金管會", "中央銀行", "洗錢防制", "內線交易"]
        if any(name in top_concept_names for name in expected_names):
            checks.append(("✅", "Top concepts look meaningful (金管會, etc.)"))
        else:
            checks.append(("⚠️ ", "Top concepts may need review"))

    # Check 5: Vector DB matches document count
    if vector_db_path.exists():
        try:
            with sqlite3.connect(vector_db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
                embedding_count = cursor.fetchone()[0]

                total_chunks_db = sum(d.chunk_count for d in indexed_docs)

                if embedding_count == total_chunks_db:
                    checks.append(("✅", f"Vector DB matches document chunks ({embedding_count})"))
                else:
                    checks.append(("⚠️ ", f"Vector DB mismatch: {embedding_count} embeddings vs {total_chunks_db} chunks"))
        except:
            pass

    # Print checks
    check_table = Table(show_header=False, box=None)
    check_table.add_column("Status", style="bold", width=4)
    check_table.add_column("Check", style="white")

    for status, message in checks:
        check_table.add_row(status, message)

    console.print(check_table)
    console.print()

    # ========================================
    # 6. STATISTICS
    # ========================================
    console.print(Panel.fit("📊 STATISTICS", style="bold yellow"))
    console.print()

    doc_stats = db.get_document_statistics()
    concept_stats = db.get_concept_statistics()

    stats_table = Table(show_header=True)
    stats_table.add_column("Category", style="cyan", width=30)
    stats_table.add_column("Value", style="green")

    # Document stats
    stats_table.add_row("[bold]Documents[/bold]", "")
    stats_table.add_row("  Total", str(doc_stats.get("total_documents", 0)))
    stats_table.add_row("  Indexed", str(doc_stats.get("indexed_documents", 0)))
    stats_table.add_row("  Total chunks", str(doc_stats.get("total_chunks", 0)))

    # Concept stats
    stats_table.add_row("[bold]Concepts[/bold]", "")
    stats_table.add_row("  Total", str(concept_stats.get("total_concepts", 0)))
    stats_table.add_row("  Total mappings", str(concept_stats.get("total_mappings", 0)))

    if concept_stats.get("avg_documents_per_concept"):
        stats_table.add_row("  Avg docs per concept", f"{concept_stats['avg_documents_per_concept']:.1f}")

    if doc_stats.get("total_documents", 0) > 0 and concept_stats.get("total_mappings", 0) > 0:
        avg_concepts_per_doc = concept_stats["total_mappings"] / doc_stats["total_documents"]
        stats_table.add_row("  Avg concepts per doc", f"{avg_concepts_per_doc:.1f}")

    console.print(stats_table)
    console.print()

    # ========================================
    # 7. RECOMMENDATIONS
    # ========================================
    console.print(Panel.fit("💡 RECOMMENDATIONS", style="bold yellow"))
    console.print()

    recommendations = []

    if len(unindexed_docs) > 0:
        recommendations.append(f"• Run reindex to process {len(unindexed_docs)} unindexed documents")

    if len(docs_without_type) > len(all_docs) * 0.3:
        recommendations.append(f"• Run full reindex with LLM to improve metadata quality ({len(docs_without_type)} docs need types)")

    if len(all_concepts) < 50:
        recommendations.append("• Consider running full LLM reindex to extract more concepts")

    if not indexed_docs:
        recommendations.append("• No indexed documents found! Run: uv run finagent reindex --skip-init")

    if not recommendations:
        recommendations.append("✅ Database looks good! No recommendations.")

    for rec in recommendations:
        console.print(f"  {rec}")

    console.print()
    console.print("=" * 100, style="bold cyan")
    console.print()

    return {
        "total_documents": len(all_docs),
        "indexed_documents": len(indexed_docs),
        "total_concepts": len(all_concepts),
        "total_embeddings": embedding_count if vector_db_path.exists() else 0,
        "checks_passed": sum(1 for status, _ in checks if status == "✅"),
        "total_checks": len(checks),
    }


if __name__ == "__main__":
    try:
        results = verify_database()

        # Exit code based on checks
        if results["checks_passed"] == results["total_checks"]:
            console.print("[bold green]✅ All checks passed![/bold green]")
            console.print()
            exit(0)
        else:
            console.print(f"[bold yellow]⚠️  {results['checks_passed']}/{results['total_checks']} checks passed[/bold yellow]")
            console.print()
            exit(1)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        exit(1)
