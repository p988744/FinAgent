#!/usr/bin/env python3
"""
Database migration runner for FinAgent.

Applies SQL migration scripts in order.
"""

import sqlite3
from pathlib import Path


def get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    """Get list of already applied migrations."""
    cursor = conn.cursor()

    # Create migrations tracking table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    cursor.execute("SELECT filename FROM _migrations")
    return {row[0] for row in cursor.fetchall()}


def apply_migration(conn: sqlite3.Connection, migration_file: Path) -> None:
    """Apply a single migration file."""
    print(f"Applying migration: {migration_file.name}")

    sql = migration_file.read_text(encoding="utf-8")

    # Execute migration
    cursor = conn.cursor()
    cursor.executescript(sql)

    # Record migration
    cursor.execute(
        "INSERT INTO _migrations (filename) VALUES (?)",
        (migration_file.name,)
    )
    conn.commit()

    print(f"  ✓ {migration_file.name} applied successfully")


def run_migrations(db_path: str = "./data/finagent.db") -> None:
    """Run all pending migrations."""
    db_file = Path(db_path)
    migrations_dir = Path(__file__).parent

    # Ensure database directory exists
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(str(db_file))

    try:
        # Get already applied migrations
        applied = get_applied_migrations(conn)

        # Get all migration files
        migration_files = sorted(migrations_dir.glob("*.sql"))

        if not migration_files:
            print("No migration files found.")
            return

        # Apply pending migrations
        pending = [f for f in migration_files if f.name not in applied]

        if not pending:
            print("All migrations already applied.")
            return

        print(f"Found {len(pending)} pending migration(s)")

        for migration_file in pending:
            apply_migration(conn, migration_file)

        print(f"\n✓ All migrations applied successfully!")

    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
