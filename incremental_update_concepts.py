"""Incremental update - add new concepts/synonyms without dropping existing data.

This script:
1. Adds new concepts from seed_semantic_concepts.py
2. Adds new synonyms from seed_semantic_concepts.py
3. Skips existing data (INSERT OR IGNORE)
4. Updates FTS index automatically via triggers

Use this when:
- Adding 1-5 new concepts
- Adding new synonyms to existing concepts
- Making small incremental changes
- Don't want to lose existing document mappings
"""

import sqlite3

from rich.console import Console

from seed_semantic_concepts import CONCEPTS, SYNONYMS

console = Console()


def incremental_update(db_path: str = "data/finagent.db"):
    """Add new concepts/synonyms without dropping existing data."""
    console.print("\n[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]")
    console.print("[cyan bold]    Semantic Concepts - Incremental Update             [/cyan bold]")
    console.print("[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Insert new concepts (ignore if already exists)
    console.print("[yellow]Step 1: Adding new concepts...[/yellow]")
    concepts_added = 0
    concepts_skipped = 0

    for concept in CONCEPTS:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO semantic_concepts
                (concept_key, name_zh, name_en, description, parent_concept_key, concept_level)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    concept["concept_key"],
                    concept["name_zh"],
                    concept["name_en"],
                    concept.get("description", ""),
                    concept.get("parent_concept_key"),
                    concept.get("concept_level", 1),
                ),
            )
            if cursor.rowcount > 0:
                concepts_added += 1
                console.print(
                    f"  [green]✓[/green] Added concept: [cyan]{concept['concept_key']}[/cyan] ({concept['name_zh']})"
                )
            else:
                concepts_skipped += 1
        except Exception as e:
            console.print(f"  [red]✗[/red] Error adding concept {concept['concept_key']}: {e}")

    console.print(
        f"\n[green]✓ Added {concepts_added} new concepts, skipped {concepts_skipped} existing[/green]\n"
    )

    # Step 2: Insert new synonyms (ignore if already exists)
    console.print("[yellow]Step 2: Adding new synonyms...[/yellow]")
    synonyms_added = 0
    synonyms_skipped = 0

    for concept_key, synonym, weight in SYNONYMS:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO concept_synonyms
                (concept_key, synonym, weight)
                VALUES (?, ?, ?)
            """,
                (concept_key, synonym, weight),
            )
            if cursor.rowcount > 0:
                synonyms_added += 1
                if synonyms_added <= 10:  # Show first 10 only
                    console.print(
                        f"  [green]✓[/green] Added synonym: '{synonym}' → {concept_key} (weight: {weight})"
                    )
                elif synonyms_added == 11:
                    console.print(f"  [dim]... and {len(SYNONYMS) - 10} more ...[/dim]")
            else:
                synonyms_skipped += 1
        except Exception as e:
            console.print(f"  [red]✗[/red] Error adding synonym '{synonym}': {e}")

    console.print(
        f"\n[green]✓ Added {synonyms_added} new synonyms, skipped {synonyms_skipped} existing[/green]\n"
    )

    # Step 3: Verify FTS index
    console.print("[yellow]Step 3: Verifying FTS index...[/yellow]")

    cursor.execute("SELECT COUNT(*) FROM concept_synonyms")
    synonym_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM concept_synonyms_fts")
    fts_count = cursor.fetchone()[0]

    if synonym_count == fts_count:
        console.print(
            f"[green]✓ FTS index up to date ({fts_count} entries match {synonym_count} synonyms)[/green]\n"
        )
    else:
        console.print(
            f"[yellow]⚠️  FTS index mismatch: {fts_count} entries vs {synonym_count} synonyms[/yellow]"
        )
        console.print("[yellow]Rebuilding FTS index...[/yellow]")
        cursor.execute("INSERT INTO concept_synonyms_fts(concept_synonyms_fts) VALUES('rebuild')")
        console.print("[green]✓ FTS index rebuilt[/green]\n")

    # Commit all changes
    conn.commit()
    conn.close()

    # Summary
    console.print("[cyan]═══ Summary ═══[/cyan]")
    console.print(f"  Concepts added: [green]{concepts_added}[/green]")
    console.print(f"  Concepts skipped: [dim]{concepts_skipped}[/dim]")
    console.print(f"  Synonyms added: [green]{synonyms_added}[/green]")
    console.print(f"  Synonyms skipped: [dim]{synonyms_skipped}[/dim]\n")

    if concepts_added > 0 or synonyms_added > 0:
        console.print("[yellow]Next steps:[/yellow]")
        if concepts_added > 0:
            console.print(
                "  1. [cyan]Reassign documents:[/cyan] uv run python assign_semantic_concepts.py"
            )
        console.print("  2. [cyan]Test changes:[/cyan] uv run python test_query_expansion.py")
        console.print("  3. [cyan]Verify in database:[/cyan] sqlite3 data/finagent.db\n")
    else:
        console.print("[dim]No new data added. All concepts/synonyms already exist.[/dim]\n")

    return concepts_added, synonyms_added


def show_current_stats(db_path: str = "data/finagent.db"):
    """Show current database statistics."""
    console.print("[cyan]Current Database Statistics:[/cyan]\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Concept count
    cursor.execute("SELECT COUNT(*) FROM semantic_concepts")
    concept_count = cursor.fetchone()[0]
    console.print(f"  Concepts: {concept_count}")

    # Synonym count
    cursor.execute("SELECT COUNT(*) FROM concept_synonyms")
    synonym_count = cursor.fetchone()[0]
    console.print(f"  Synonyms: {synonym_count}")

    # Document mapping count
    cursor.execute("SELECT COUNT(*) FROM document_semantic_concepts")
    mapping_count = cursor.fetchone()[0]
    console.print(f"  Document mappings: {mapping_count}")

    # Top 5 concepts by usage
    cursor.execute(
        """
        SELECT sc.name_zh, COUNT(DISTINCT dsc.filename) as doc_count
        FROM semantic_concepts sc
        LEFT JOIN document_semantic_concepts dsc ON sc.concept_key = dsc.concept_key
        GROUP BY sc.concept_key, sc.name_zh
        ORDER BY doc_count DESC
        LIMIT 5
    """
    )

    console.print("\n  [cyan]Top 5 concepts by document usage:[/cyan]")
    for name_zh, doc_count in cursor.fetchall():
        console.print(f"    • {name_zh}: {doc_count} documents")

    conn.close()
    console.print()


if __name__ == "__main__":
    # Show current stats
    show_current_stats()

    # Run incremental update
    concepts_added, synonyms_added = incremental_update()

    # Show updated stats if changes made
    if concepts_added > 0 or synonyms_added > 0:
        console.print("[green]Updated Statistics:[/green]\n")
        show_current_stats()

    console.print("[green bold]✓ Incremental update complete![/green bold]\n")
