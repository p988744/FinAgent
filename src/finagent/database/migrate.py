"""Database migration utility."""

import logging
import sqlite3
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database migrations."""

    def __init__(self, db_path: str | Path):
        """Initialize migration runner.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.migrations_dir = Path(__file__).parent / "migrations"

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        """Get current schema version.

        Args:
            conn: SQLite connection

        Returns:
            Current schema version (0 if no migrations applied)
        """
        cursor = conn.cursor()

        # Check if migration table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        )
        if not cursor.fetchone():
            # Create migrations table
            cursor.execute("""
                CREATE TABLE schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    migration_name TEXT NOT NULL
                )
            """)
            conn.commit()
            return 0

        # Get latest version
        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def _get_pending_migrations(self, current_version: int) -> List[tuple[int, Path]]:
        """Get list of pending migrations.

        Args:
            current_version: Current schema version

        Returns:
            List of (version, file_path) tuples for pending migrations
        """
        migrations = []

        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return migrations

        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            # Extract version from filename (e.g., "001_add_metadata_status.sql" -> 1)
            try:
                version = int(migration_file.stem.split("_")[0])
                if version > current_version:
                    migrations.append((version, migration_file))
            except (ValueError, IndexError):
                logger.warning(f"Invalid migration filename: {migration_file.name}")

        return sorted(migrations, key=lambda x: x[0])

    def _apply_migration(
        self, conn: sqlite3.Connection, version: int, migration_file: Path
    ):
        """Apply a single migration.

        Args:
            conn: SQLite connection
            version: Migration version
            migration_file: Path to migration SQL file
        """
        logger.info(f"Applying migration {version}: {migration_file.name}")

        # Read migration SQL
        sql = migration_file.read_text()

        # Execute migration
        try:
            conn.executescript(sql)

            # Record migration
            conn.execute(
                "INSERT INTO schema_migrations (version, migration_name) VALUES (?, ?)",
                (version, migration_file.name),
            )
            conn.commit()

            logger.info(f"✅ Migration {version} applied successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Migration {version} failed: {e}")
            raise

    def run(self, target_version: int | None = None):
        """Run pending migrations.

        Args:
            target_version: Target version to migrate to (None = latest)
        """
        if not self.db_path.exists():
            logger.error(f"Database not found: {self.db_path}")
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        conn = sqlite3.connect(self.db_path)

        try:
            current_version = self._get_schema_version(conn)
            logger.info(f"Current schema version: {current_version}")

            pending_migrations = self._get_pending_migrations(current_version)

            if not pending_migrations:
                logger.info("✅ Database is up to date")
                return

            # Filter by target version if specified
            if target_version is not None:
                pending_migrations = [
                    (v, f) for v, f in pending_migrations if v <= target_version
                ]

            if not pending_migrations:
                logger.info(
                    f"✅ Database is already at version {current_version} (target: {target_version})"
                )
                return

            logger.info(f"Found {len(pending_migrations)} pending migration(s)")

            for version, migration_file in pending_migrations:
                self._apply_migration(conn, version, migration_file)

            final_version = self._get_schema_version(conn)
            logger.info(f"✅ Migrations complete. Schema version: {final_version}")

        finally:
            conn.close()

    def status(self):
        """Show migration status."""
        if not self.db_path.exists():
            logger.error(f"Database not found: {self.db_path}")
            return

        conn = sqlite3.connect(self.db_path)

        try:
            current_version = self._get_schema_version(conn)
            print(f"Current schema version: {current_version}")

            # Show applied migrations
            cursor = conn.cursor()
            cursor.execute(
                "SELECT version, migration_name, applied_at FROM schema_migrations ORDER BY version"
            )
            applied = cursor.fetchall()

            if applied:
                print("\nApplied migrations:")
                for version, name, applied_at in applied:
                    print(f"  {version:03d}: {name} (applied: {applied_at})")
            else:
                print("\nNo migrations applied yet")

            # Show pending migrations
            pending = self._get_pending_migrations(current_version)
            if pending:
                print(f"\nPending migrations ({len(pending)}):")
                for version, migration_file in pending:
                    print(f"  {version:03d}: {migration_file.name}")
            else:
                print("\n✅ Database is up to date")

        finally:
            conn.close()


if __name__ == "__main__":
    import sys

    # Simple CLI for migrations
    if len(sys.argv) < 2:
        print("Usage: python -m finagent.database.migrate <command> [db_path]")
        print("Commands: run, status")
        sys.exit(1)

    command = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "data/finagent.db"

    logging.basicConfig(level=logging.INFO)

    runner = MigrationRunner(db_path)

    if command == "run":
        runner.run()
    elif command == "status":
        runner.status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
