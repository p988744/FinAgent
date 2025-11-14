"""Full rebuild of semantic concepts system.

This script performs a complete rebuild:
1. Drops all semantic concept tables
2. Recreates schema from migration file
3. Seeds concepts and synonyms
4. Reassigns concepts to all documents
5. Verifies rebuild success

CAUTION: This will DELETE all existing semantic concept data!
Always backup before running!
"""

import sqlite3
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

console = Console()


def drop_semantic_tables(db_path: str = "data/finagent.db"):
    """Drop all semantic concept tables."""
    console.print("\n[yellow]⚠️  Dropping semantic concept tables...[/yellow]")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop in correct order (FTS first, then tables with foreign keys)
    tables = [
        "concept_synonyms_fts",
        "document_semantic_concepts",
        "concept_synonyms",
        "semantic_concepts",
    ]

    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            console.print(f"  [dim]✓ Dropped {table}[/dim]")
        except Exception as e:
            console.print(f"  [red]✗ Error dropping {table}: {e}[/red]")

    conn.commit()
    conn.close()
    console.print("[green]✓ All semantic tables dropped[/green]\n")


def recreate_schema(db_path: str = "data/finagent.db"):
    """Recreate semantic concept schema."""
    console.print("[yellow]Creating semantic concept schema...[/yellow]")

    migration_file = Path("src/finagent/database/migrations/003_add_semantic_concepts.sql")

    if not migration_file.exists():
        console.print(f"[red]✗ Migration file not found: {migration_file}[/red]")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read and execute migration
    with open(migration_file, "r", encoding="utf-8") as f:
        migration_sql = f.read()

    try:
        cursor.executescript(migration_sql)
        conn.commit()
        console.print("[green]✓ Schema created successfully[/green]\n")
        return True
    except Exception as e:
        console.print(f"[red]✗ Error creating schema: {e}[/red]")
        return False
    finally:
        conn.close()


def seed_concepts(db_path: str = "data/finagent.db"):
    """Seed semantic concepts and synonyms."""
    console.print("[yellow]Seeding concepts and synonyms...[/yellow]")

    try:
        from seed_semantic_concepts import seed_database

        stats = seed_database(db_path)
        console.print(f"[green]✓ Seeded {stats['concepts']} concepts[/green]")
        console.print(f"[green]✓ Seeded {stats['synonyms']} synonyms[/green]\n")
        return True
    except Exception as e:
        console.print(f"[red]✗ Error seeding: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def reassign_all_documents(db_path: str = "data/finagent.db"):
    """Reassign concepts to all documents."""
    console.print("[yellow]Reassigning concepts to documents...[/yellow]")

    try:
        from assign_semantic_concepts import main as assign_main

        assign_main(db_path=db_path, verbose=False)
        console.print("[green]✓ Document assignment complete[/green]\n")
        return True
    except Exception as e:
        console.print(f"[red]✗ Error assigning documents: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def verify_rebuild(db_path: str = "data/finagent.db"):
    """Verify rebuild was successful."""
    console.print("[cyan]Verifying rebuild...[/cyan]\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    checks = [
        ("Concepts", "SELECT COUNT(*) FROM semantic_concepts"),
        ("Synonyms", "SELECT COUNT(*) FROM concept_synonyms"),
        ("FTS entries", "SELECT COUNT(*) FROM concept_synonyms_fts"),
        ("Document mappings", "SELECT COUNT(*) FROM document_semantic_concepts"),
    ]

    all_ok = True
    for name, query in checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]

            if count > 0:
                console.print(f"  [green]✓[/green] {name}: {count}")
            else:
                console.print(f"  [yellow]○[/yellow] {name}: {count} [dim](may be empty)[/dim]")
                if name == "Document mappings":
                    all_ok = False
        except Exception as e:
            console.print(f"  [red]✗[/red] {name}: Error - {e}")
            all_ok = False

    conn.close()

    if all_ok:
        console.print("\n[green bold]✓ Rebuild verification passed![/green bold]\n")
    else:
        console.print("\n[yellow]⚠️  Some checks failed (review above)[/yellow]\n")

    return all_ok


def main():
    """Full rebuild of semantic concepts system."""
    console.print("\n[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]")
    console.print("[cyan bold]     Semantic Concepts System - Full Rebuild          [/cyan bold]")
    console.print("[cyan bold]═══════════════════════════════════════════════════════[/cyan bold]\n")

    # Warning
    console.print("[red bold]⚠️  WARNING: This will DELETE all semantic concept data![/red bold]")
    console.print("[yellow]This includes:[/yellow]")
    console.print("  • All semantic concepts")
    console.print("  • All concept synonyms")
    console.print("  • All document-concept mappings")
    console.print("  • FTS search index\n")

    # Confirm backup
    if not Confirm.ask("[yellow]Have you backed up the database?[/yellow]", default=False):
        console.print("\n[red]⚠️  Backup first![/red]")
        console.print("[yellow]Run this command:[/yellow]")
        console.print("  cp data/finagent.db data/finagent.db.backup.$(date +%Y%m%d_%H%M%S)\n")
        sys.exit(1)

    # Confirm rebuild
    if not Confirm.ask("[red bold]Proceed with full rebuild?[/red bold]", default=False):
        console.print("\n[yellow]Rebuild cancelled[/yellow]\n")
        sys.exit(0)

    # Execute rebuild steps
    db_path = "data/finagent.db"

    steps = [
        ("Drop tables", lambda: drop_semantic_tables(db_path)),
        ("Recreate schema", lambda: recreate_schema(db_path)),
        ("Seed concepts", lambda: seed_concepts(db_path)),
        ("Reassign documents", lambda: reassign_all_documents(db_path)),
        ("Verify rebuild", lambda: verify_rebuild(db_path)),
    ]

    for step_name, step_func in steps:
        console.print(f"[cyan]═══ Step: {step_name} ═══[/cyan]")
        success = step_func()

        if not success and step_name != "Verify rebuild":
            console.print(f"\n[red bold]✗ Rebuild failed at step: {step_name}[/red bold]\n")
            console.print("[yellow]To recover, restore from backup:[/yellow]")
            console.print("  ls -lh data/finagent.db.backup.*")
            console.print("  cp data/finagent.db.backup.<timestamp> data/finagent.db\n")
            sys.exit(1)

    console.print("[green bold]✓ Full rebuild complete![/green bold]\n")
    console.print("[cyan]Next steps:[/cyan]")
    console.print("  1. Test query expansion: uv run python test_query_expansion.py")
    console.print("  2. Test 6 queries: uv run python test_6_queries.py")
    console.print("  3. Verify in database: sqlite3 data/finagent.db\n")


if __name__ == "__main__":
    main()
