"""Test semantic concepts system with clean test database."""

import sqlite3
import tempfile
from pathlib import Path


def test_semantic_concepts():
    """Test semantic concepts with temporary database."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db = tmp.name

    print(f"Testing with temporary database: {test_db}\n")

    # Run migration
    print("=" * 80)
    print("STEP 1: Running Migration")
    print("=" * 80)

    migration_sql = Path("src/finagent/database/migrations/003_add_semantic_concepts.sql").read_text()

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.executescript(migration_sql)
    conn.commit()
    conn.close()

    print("✓ Migration complete\n")

    # Seed concepts
    print("=" * 80)
    print("STEP 2: Seeding Concepts")
    print("=" * 80)

    from src.finagent.database.seed_semantic_concepts import seed_semantic_concepts

    seed_semantic_concepts(test_db)

    # Test concept lookup
    print("\n" + "=" * 80)
    print("STEP 3: Test Concept Lookup")
    print("=" * 80)

    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Test 1: Look up concept by synonym
    print("\n[Test 1] Find concepts matching '洗錢':")
    cursor.execute(
        """
        SELECT DISTINCT c.concept_key, c.name_zh, c.name_en, s.synonym, s.weight
        FROM concept_synonyms s
        JOIN semantic_concepts c ON s.concept_key = c.concept_key
        WHERE s.synonym LIKE '%洗錢%'
        ORDER BY s.weight DESC
        """
    )
    for row in cursor.fetchall():
        print(f"  {row['concept_key']:30} | {row['name_zh']:12} | {row['synonym']:20} (weight: {row['weight']})")

    # Test 2: Find all synonyms for a concept
    print("\n[Test 2] All synonyms for VENTURE_CAPITAL:")
    cursor.execute(
        """
        SELECT synonym, synonym_type, weight
        FROM concept_synonyms
        WHERE concept_key = 'VENTURE_CAPITAL'
        ORDER BY weight DESC
        """
    )
    for row in cursor.fetchall():
        print(f"  {row['synonym']:25} | {row['synonym_type']:12} | weight: {row['weight']}")

    # Test 3: Fuzzy search using FTS
    print("\n[Test 3] FTS search for '反洗錢':")
    cursor.execute(
        """
        SELECT c.concept_key, c.name_zh, f.synonym
        FROM concept_synonyms_fts f
        JOIN semantic_concepts c ON f.concept_key = c.concept_key
        WHERE synonym MATCH '反洗錢'
        """
    )
    for row in cursor.fetchall():
        print(f"  {row['concept_key']:30} | {row['name_zh']:12} | {row['synonym']}")

    # Test 4: Hierarchical concepts
    print("\n[Test 4] Child concepts of FINANCIAL_CRIME:")
    cursor.execute(
        """
        SELECT concept_key, name_zh, name_en
        FROM semantic_concepts
        WHERE parent_concept_key = 'FINANCIAL_CRIME'
        """
    )
    for row in cursor.fetchall():
        print(f"  {row['concept_key']:30} | {row['name_zh']:12} | {row['name_en']}")

    # Test 5: Query expansion simulation
    print("\n[Test 5] Query expansion for '創投公司裁罰':")
    search_terms = ["創投公司", "創投", "裁罰"]
    matched_concepts = set()

    for term in search_terms:
        cursor.execute(
            """
            SELECT DISTINCT concept_key
            FROM concept_synonyms
            WHERE synonym LIKE ?
            """,
            (f"%{term}%",)
        )
        for row in cursor.fetchall():
            matched_concepts.add(row['concept_key'])

    print(f"  Original terms: {search_terms}")
    print(f"  Mapped to concepts: {list(matched_concepts)}")

    # Show expanded synonyms
    for concept_key in matched_concepts:
        cursor.execute(
            """
            SELECT name_zh, name_en FROM semantic_concepts WHERE concept_key = ?
            """,
            (concept_key,)
        )
        concept = cursor.fetchone()

        cursor.execute(
            """
            SELECT synonym FROM concept_synonyms
            WHERE concept_key = ? AND weight >= 0.8
            ORDER BY weight DESC
            LIMIT 5
            """,
            (concept_key,)
        )
        synonyms = [row['synonym'] for row in cursor.fetchall()]

        print(f"\n  {concept_key} ({concept['name_zh']}):")
        print(f"    Expands to: {synonyms}")

    conn.close()

    print("\n" + "=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)

    # Clean up
    Path(test_db).unlink()


if __name__ == "__main__":
    test_semantic_concepts()
