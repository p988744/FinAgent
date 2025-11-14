"""Run semantic concepts migration and seed data."""

import sqlite3
import time
from pathlib import Path


def run_migration(db_path: str = "data/finagent.db", retry_attempts: int = 5):
    """Run semantic concepts migration with retry logic."""
    print(f"Running migration on {db_path}...")

    migration_sql = Path("src/finagent/database/migrations/003_add_semantic_concepts.sql").read_text()

    for attempt in range(retry_attempts):
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()

            # Execute migration in transaction
            cursor.executescript(migration_sql)
            conn.commit()
            conn.close()

            print("✓ Migration completed successfully")
            return

        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < retry_attempts - 1:
                print(f"  Database locked, retrying in 2 seconds... (attempt {attempt + 1}/{retry_attempts})")
                time.sleep(2)
            else:
                print(f"✗ Migration failed: {e}")
                raise
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            raise


if __name__ == "__main__":
    # Run migration
    run_migration()

    # Seed concepts
    from src.finagent.database.seed_semantic_concepts import seed_semantic_concepts

    seed_semantic_concepts()
