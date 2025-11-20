import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_history_table(db_path: str = "data/finagent.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_add = [
        ("query_analysis", "TEXT"),
        ("plan_data", "TEXT"),
        ("search_iterations", "INTEGER DEFAULT 0"),
        ("search_strategy", "TEXT"),
        ("vector_chunks_count", "INTEGER DEFAULT 0"),
        ("hard_chunks_count", "INTEGER DEFAULT 0"),
        ("total_chunks_count", "INTEGER DEFAULT 0"),
        ("citations_count", "INTEGER DEFAULT 0"),
        ("confidence_level", "TEXT"),
        ("validation_issues", "TEXT"),
        ("user_notes", "TEXT"),
        ("processing_steps", "TEXT"),
    ]

    for col_name, col_type in columns_to_add:
        try:
            logger.info(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE history ADD COLUMN {col_name} {col_type}")
            logger.info(f"  ✓ Added {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info(f"  - Column {col_name} already exists")
            else:
                logger.error(f"  ✗ Failed to add {col_name}: {e}")

    conn.commit()
    conn.close()
    logger.info("Finished patching history table.")

if __name__ == "__main__":
    fix_history_table()
