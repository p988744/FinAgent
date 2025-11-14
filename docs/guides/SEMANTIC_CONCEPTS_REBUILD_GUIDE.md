# Semantic Concepts System - Rebuild Guide

**Purpose:** How to rebuild the semantic concepts system when you need to make changes
**Last Updated:** 2025-11-14
**Status:** Production Guide

---

## When to Rebuild

You should rebuild the semantic concepts system when:

1. **Adding new concepts** - New violation types or institution categories
2. **Adding new synonyms** - New terms for existing concepts
3. **Modifying concept hierarchy** - Changing parent-child relationships
4. **Adjusting synonym weights** - Fine-tuning relevance scores
5. **Fixing incorrect mappings** - Correcting wrong concept-synonym associations
6. **Database corruption** - Recovery from data issues

---

## Rebuild Options

### Option 1: Full Rebuild (Clean Slate)

**When to use:**
- Major structural changes to concepts
- Testing new concept taxonomy
- Database corruption
- Starting fresh after experiments

**What it does:**
- Drops all semantic concept tables
- Recreates schema from scratch
- Reseeds all concepts and synonyms
- Reassigns concepts to all documents

**Time:** ~2-3 minutes for 196 documents

### Option 2: Incremental Update (Add/Modify)

**When to use:**
- Adding new concepts without affecting existing ones
- Adding new synonyms to existing concepts
- Adjusting weights or metadata
- Small fixes

**What it does:**
- Keeps existing data intact
- Adds new concepts/synonyms
- Updates specific records
- Reassigns affected documents only

**Time:** ~10-30 seconds

### Option 3: Document Reassignment Only

**When to use:**
- Synonym changes affect document matching
- Testing different confidence thresholds
- Fixing document-concept mappings

**What it does:**
- Keeps concept/synonym tables unchanged
- Clears document_semantic_concepts table
- Reassigns all documents

**Time:** ~15 seconds for 196 documents

---

## Full Rebuild Process

### Step 1: Backup Current Database

**Always backup before rebuilding!**

```bash
# Backup database
cp data/finagent.db data/finagent.db.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup
ls -lh data/finagent.db.backup.*
```

### Step 2: Modify Concept Definitions

Edit the concept seed data in [seed_semantic_concepts.py](seed_semantic_concepts.py):

```python
# Example: Add new concept
CONCEPTS = [
    # ... existing concepts ...
    {
        "concept_key": "CYBERSECURITY_INCIDENT",
        "name_zh": "資安事件",
        "name_en": "Cybersecurity Incident",
        "description": "網路安全事件、資料外洩、駭客攻擊等",
        "parent_concept_key": None,
        "concept_level": 1,
    },
]

# Example: Add synonyms for new concept
SYNONYMS = [
    # ... existing synonyms ...
    # Cybersecurity Incident
    ("CYBERSECURITY_INCIDENT", "資安事件", 1.0),
    ("CYBERSECURITY_INCIDENT", "網路安全", 0.9),
    ("CYBERSECURITY_INCIDENT", "資料外洩", 0.95),
    ("CYBERSECURITY_INCIDENT", "駭客攻擊", 0.9),
    ("CYBERSECURITY_INCIDENT", "資安漏洞", 0.85),
]
```

### Step 3: Run Full Rebuild Script

Create or update [rebuild_semantic_concepts.py](rebuild_semantic_concepts.py):

```python
"""Full rebuild of semantic concepts system."""

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

    from seed_semantic_concepts import seed_database

    try:
        stats = seed_database(db_path)
        console.print(f"[green]✓ Seeded {stats['concepts']} concepts[/green]")
        console.print(f"[green]✓ Seeded {stats['synonyms']} synonyms[/green]\n")
        return True
    except Exception as e:
        console.print(f"[red]✗ Error seeding: {e}[/red]")
        return False


def reassign_all_documents(db_path: str = "data/finagent.db"):
    """Reassign concepts to all documents."""
    console.print("[yellow]Reassigning concepts to documents...[/yellow]")

    from assign_semantic_concepts import main as assign_main

    try:
        assign_main(db_path=db_path, verbose=False)
        console.print("[green]✓ Document assignment complete[/green]\n")
        return True
    except Exception as e:
        console.print(f"[red]✗ Error assigning documents: {e}[/red]")
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
        cursor.execute(query)
        count = cursor.fetchone()[0]

        if count > 0:
            console.print(f"  [green]✓[/green] {name}: {count}")
        else:
            console.print(f"  [red]✗[/red] {name}: {count} [dim](may be OK)[/dim]")
            if name == "Document mappings":
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

    # Confirm
    if not Confirm.ask("[yellow]Have you backed up the database?[/yellow]", default=False):
        console.print("\n[red]Backup first![/red] Run: cp data/finagent.db data/finagent.db.backup\n")
        sys.exit(1)

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
        console.print(f"[cyan]Step: {step_name}[/cyan]")
        success = step_func()
        if not success and step_name != "Verify rebuild":
            console.print(f"\n[red bold]✗ Rebuild failed at step: {step_name}[/red bold]\n")
            console.print("[yellow]To recover, restore from backup:[/yellow]")
            console.print("  cp data/finagent.db.backup.* data/finagent.db\n")
            sys.exit(1)

    console.print("[green bold]✓ Full rebuild complete![/green bold]\n")


if __name__ == "__main__":
    main()
```

### Step 4: Run Rebuild

```bash
# Run full rebuild
uv run python rebuild_semantic_concepts.py
```

**Expected output:**
```
═══════════════════════════════════════════════════════
     Semantic Concepts System - Full Rebuild
═══════════════════════════════════════════════════════

⚠️  WARNING: This will DELETE all semantic concept data!
This includes:
  • All semantic concepts
  • All concept synonyms
  • All document-concept mappings
  • FTS search index

Have you backed up the database? (y/N): y
Proceed with full rebuild? (y/N): y

Step: Drop tables
⚠️  Dropping semantic concept tables...
  ✓ Dropped concept_synonyms_fts
  ✓ Dropped document_semantic_concepts
  ✓ Dropped concept_synonyms
  ✓ Dropped semantic_concepts
✓ All semantic tables dropped

Step: Recreate schema
Creating semantic concept schema...
✓ Schema created successfully

Step: Seed concepts
Seeding concepts and synonyms...
✓ Seeded 23 concepts
✓ Seeded 145 synonyms

Step: Reassign documents
Reassigning concepts to documents...
[Processing 196 documents...]
✓ Document assignment complete

Step: Verify rebuild
Verifying rebuild...
  ✓ Concepts: 23
  ✓ Synonyms: 145
  ✓ FTS entries: 145
  ✓ Document mappings: 235

✓ Full rebuild complete!
```

---

## Incremental Update Process

### Step 1: Add New Concepts/Synonyms

Edit [seed_semantic_concepts.py](seed_semantic_concepts.py) and add your new data:

```python
# Add to CONCEPTS list
CONCEPTS.append({
    "concept_key": "CYBERSECURITY_INCIDENT",
    "name_zh": "資安事件",
    "name_en": "Cybersecurity Incident",
    "description": "網路安全事件、資料外洩、駭客攻擊等",
    "parent_concept_key": None,
    "concept_level": 1,
})

# Add to SYNONYMS list
SYNONYMS.extend([
    ("CYBERSECURITY_INCIDENT", "資安事件", 1.0),
    ("CYBERSECURITY_INCIDENT", "網路安全", 0.9),
    ("CYBERSECURITY_INCIDENT", "資料外洩", 0.95),
])
```

### Step 2: Run Incremental Update

```python
"""Incremental update - add new concepts/synonyms without dropping existing data."""

import sqlite3
from rich.console import Console
from seed_semantic_concepts import CONCEPTS, SYNONYMS

console = Console()


def incremental_update(db_path: str = "data/finagent.db"):
    """Add new concepts/synonyms without dropping existing data."""
    console.print("\n[cyan]Incremental Update[/cyan]\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert new concepts (ignore if already exists)
    concepts_added = 0
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
        except Exception as e:
            console.print(f"[red]Error adding concept {concept['concept_key']}: {e}[/red]")

    # Insert new synonyms (ignore if already exists)
    synonyms_added = 0
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
        except Exception as e:
            console.print(f"[red]Error adding synonym '{synonym}': {e}[/red]")

    conn.commit()
    conn.close()

    console.print(f"[green]✓ Added {concepts_added} new concepts[/green]")
    console.print(f"[green]✓ Added {synonyms_added} new synonyms[/green]\n")

    return concepts_added, synonyms_added


if __name__ == "__main__":
    incremental_update()
```

**Run:**
```bash
uv run python incremental_update_concepts.py
```

### Step 3: Reassign Affected Documents (Optional)

If new synonyms affect document matching:

```bash
# Reassign all documents
uv run python assign_semantic_concepts.py
```

Or reassign specific documents:

```python
from finagent.document_processing.semantic_mapper import assign_concepts_to_document
from finagent.database.db import get_document

# Reassign specific document
doc = get_document("filename.txt")
assign_concepts_to_document(
    filename=doc.filename,
    violation_types=doc.violation_types,
    related_institutions=doc.related_institutions,
    issuing_authority=doc.issuing_authority,
    keywords=doc.keywords,
)
```

---

## Document Reassignment Only

### When to Use

- Synonym changes affect document matching
- Testing different confidence thresholds
- Fixing incorrect document-concept mappings
- Concept/synonym data is correct, but mappings are wrong

### Process

```python
"""Reassign concepts to all documents without touching concept/synonym tables."""

import sqlite3
from rich.console import Console

console = Console()


def clear_document_mappings(db_path: str = "data/finagent.db"):
    """Clear all document-concept mappings."""
    console.print("[yellow]Clearing document-concept mappings...[/yellow]")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM document_semantic_concepts")
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    console.print(f"[green]✓ Cleared {deleted} mappings[/green]\n")


def reassign_all(db_path: str = "data/finagent.db"):
    """Reassign concepts to all documents."""
    from assign_semantic_concepts import main as assign_main

    console.print("[yellow]Reassigning concepts to all documents...[/yellow]")
    assign_main(db_path=db_path, verbose=False)
    console.print("[green]✓ Reassignment complete[/green]\n")


if __name__ == "__main__":
    console.print("\n[cyan]Document Reassignment Only[/cyan]\n")

    db_path = "data/finagent.db"

    clear_document_mappings(db_path)
    reassign_all(db_path)

    console.print("[green bold]✓ Document reassignment complete![/green bold]\n")
```

**Run:**
```bash
uv run python reassign_documents.py
```

---

## Quick Reference Commands

### Full Rebuild
```bash
# Backup
cp data/finagent.db data/finagent.db.backup.$(date +%Y%m%d_%H%M%S)

# Rebuild
uv run python rebuild_semantic_concepts.py

# Verify
uv run python test_query_expansion.py
```

### Incremental Update
```bash
# Edit seed_semantic_concepts.py first
vim seed_semantic_concepts.py

# Add new concepts/synonyms
uv run python incremental_update_concepts.py

# Reassign documents (if needed)
uv run python assign_semantic_concepts.py
```

### Document Reassignment Only
```bash
# Reassign all documents
uv run python assign_semantic_concepts.py

# Or use custom script
uv run python reassign_documents.py
```

### Test Changes
```bash
# Test query expansion
uv run python test_query_expansion.py

# Test 6 queries
uv run python test_6_queries.py

# Manual test
uv run python -c "
from finagent.document_processing.semantic_mapper import expand_query_with_concepts
result = expand_query_with_concepts('洗錢防制案件')
print(f'Concepts: {result[\"concepts\"]}')
print(f'Keywords: {len(result[\"search_keywords\"])}')
"
```

---

## Common Scenarios

### Scenario 1: Add New Violation Type

**Example:** Add "市場操縱" (Market Manipulation) as new concept

**Steps:**
1. Edit `seed_semantic_concepts.py`:
```python
CONCEPTS.append({
    "concept_key": "MARKET_MANIPULATION",
    "name_zh": "市場操縱",
    "name_en": "Market Manipulation",
    "description": "操縱市場價格、炒作股價等違規行為",
    "parent_concept_key": None,
    "concept_level": 1,
})

SYNONYMS.extend([
    ("MARKET_MANIPULATION", "市場操縱", 1.0),
    ("MARKET_MANIPULATION", "操縱市場", 0.95),
    ("MARKET_MANIPULATION", "炒作", 0.8),
    ("MARKET_MANIPULATION", "哄抬股價", 0.9),
])
```

2. Run incremental update:
```bash
uv run python incremental_update_concepts.py
```

3. Reassign documents:
```bash
uv run python assign_semantic_concepts.py
```

4. Test:
```bash
uv run python -c "
from finagent.document_processing.semantic_mapper import expand_query_with_concepts
result = expand_query_with_concepts('炒作股價案件')
print(result['concepts'])  # Should include MARKET_MANIPULATION
"
```

### Scenario 2: Fix Incorrect Synonym Weight

**Example:** "AML" weight is too low (0.7), should be 1.0

**Steps:**
1. Update directly in database:
```bash
sqlite3 data/finagent.db
```

```sql
-- Check current weight
SELECT concept_key, synonym, weight
FROM concept_synonyms
WHERE synonym = 'AML';

-- Update weight
UPDATE concept_synonyms
SET weight = 1.0
WHERE synonym = 'AML';

-- Verify
SELECT concept_key, synonym, weight
FROM concept_synonyms
WHERE synonym = 'AML';

.quit
```

2. Reassign documents (weight affects confidence):
```bash
uv run python assign_semantic_concepts.py
```

### Scenario 3: Remove Incorrect Concept

**Example:** Remove "FRAUD" concept (not used in current dataset)

**Steps:**
1. Manual deletion:
```bash
sqlite3 data/finagent.db
```

```sql
-- Check usage
SELECT COUNT(*) FROM document_semantic_concepts
WHERE concept_key = 'FRAUD';

-- If unused (count = 0), delete
DELETE FROM concept_synonyms WHERE concept_key = 'FRAUD';
DELETE FROM semantic_concepts WHERE concept_key = 'FRAUD';

.quit
```

2. Update `seed_semantic_concepts.py` to remove from CONCEPTS and SYNONYMS

3. No reassignment needed if concept wasn't used

### Scenario 4: Change Concept Hierarchy

**Example:** Make "COMMERCIAL_BANK" a child of "FINANCIAL_INSTITUTION"

**Steps:**
1. Update directly:
```bash
sqlite3 data/finagent.db
```

```sql
UPDATE semantic_concepts
SET parent_concept_key = 'FINANCIAL_INSTITUTION'
WHERE concept_key = 'COMMERCIAL_BANK';
```

2. Update `seed_semantic_concepts.py` for future rebuilds

3. No document reassignment needed (hierarchy doesn't affect current retrieval)

### Scenario 5: Test Different Threshold

**Example:** Test lower threshold (0.5 instead of 0.6) for more matches

**Steps:**
1. Test without permanent changes:
```python
from finagent.document_processing.semantic_mapper import expand_query_with_concepts

# Current threshold (0.6)
result_06 = expand_query_with_concepts("內部控制", threshold=0.6)
print(f"Threshold 0.6: {len(result_06['concepts'])} concepts")

# Lower threshold (0.5)
result_05 = expand_query_with_concepts("內部控制", threshold=0.5)
print(f"Threshold 0.5: {len(result_05['concepts'])} concepts")
```

2. If better results, update default in `semantic_mapper.py`:
```python
def expand_query_with_concepts(
    query_text: str, db_path: str = "data/finagent.db", threshold: float = 0.5  # Changed
) -> dict:
```

3. Reassign documents with new threshold:
Edit `assign_semantic_concepts.py` to use new threshold:
```python
matches = lookup_concepts_by_synonym(violation, db_path, threshold=0.5)  # Changed
```

Then reassign:
```bash
uv run python assign_semantic_concepts.py
```

---

## Troubleshooting

### Issue 1: "table already exists" error during rebuild

**Symptom:**
```
Error: table semantic_concepts already exists
```

**Solution:**
Drop tables manually first:
```bash
sqlite3 data/finagent.db
```
```sql
DROP TABLE IF EXISTS concept_synonyms_fts;
DROP TABLE IF EXISTS document_semantic_concepts;
DROP TABLE IF EXISTS concept_synonyms;
DROP TABLE IF EXISTS semantic_concepts;
.quit
```

### Issue 2: FTS index not updating

**Symptom:** New synonyms not found via fuzzy search

**Solution:**
Rebuild FTS index:
```bash
sqlite3 data/finagent.db
```
```sql
-- Rebuild FTS index
INSERT INTO concept_synonyms_fts(concept_synonyms_fts) VALUES('rebuild');

-- Verify
SELECT COUNT(*) FROM concept_synonyms_fts;
.quit
```

### Issue 3: Document assignments disappeared

**Symptom:** `document_semantic_concepts` table is empty after update

**Cause:** Accidentally dropped table or foreign key cascade

**Solution:**
Reassign all documents:
```bash
uv run python assign_semantic_concepts.py
```

### Issue 4: Incorrect concept matching after changes

**Symptom:** Query "洗錢" no longer matches AML concept

**Diagnosis:**
```python
from finagent.document_processing.semantic_mapper import lookup_concepts_by_synonym

matches = lookup_concepts_by_synonym("洗錢")
print(matches)  # Should show ANTI_MONEY_LAUNDERING
```

**Solutions:**
1. Check synonym exists:
```sql
SELECT * FROM concept_synonyms WHERE synonym = '洗錢';
```

2. Check FTS index:
```sql
SELECT * FROM concept_synonyms_fts WHERE synonym MATCH '洗錢';
```

3. Rebuild FTS if empty

### Issue 5: Database locked during rebuild

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Check for background processes
ps aux | grep finagent

# Kill if found
kill <PID>

# Or restart and try again
```

---

## Database Backup Best Practices

### Before Every Rebuild
```bash
# Timestamped backup
cp data/finagent.db data/finagent.db.backup.$(date +%Y%m%d_%H%M%S)

# Keep last 5 backups only
ls -t data/finagent.db.backup.* | tail -n +6 | xargs rm -f
```

### Automated Backup Script
```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="data/backups"
DB_FILE="data/finagent.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/finagent_$TIMESTAMP.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup
cp "$DB_FILE" "$BACKUP_FILE"

# Compress (optional)
gzip "$BACKUP_FILE"

# Keep only last 10 backups
ls -t "$BACKUP_DIR"/*.db.gz | tail -n +11 | xargs rm -f

echo "Backup created: $BACKUP_FILE.gz"
```

### Restore from Backup
```bash
# List backups
ls -lh data/finagent.db.backup.*

# Restore specific backup
cp data/finagent.db.backup.20251114_153045 data/finagent.db

# Or restore latest
cp $(ls -t data/finagent.db.backup.* | head -1) data/finagent.db

# Verify
sqlite3 data/finagent.db "SELECT COUNT(*) FROM semantic_concepts;"
```

---

## Verification After Rebuild

### Step 1: Check Table Counts

```bash
sqlite3 data/finagent.db
```

```sql
-- Should be > 0
SELECT COUNT(*) as concept_count FROM semantic_concepts;
SELECT COUNT(*) as synonym_count FROM concept_synonyms;
SELECT COUNT(*) as fts_count FROM concept_synonyms_fts;
SELECT COUNT(*) as mapping_count FROM document_semantic_concepts;

-- Should match synonym count
SELECT
  (SELECT COUNT(*) FROM concept_synonyms) as synonyms,
  (SELECT COUNT(*) FROM concept_synonyms_fts) as fts,
  CASE WHEN (SELECT COUNT(*) FROM concept_synonyms) = (SELECT COUNT(*) FROM concept_synonyms_fts)
    THEN 'MATCH ✓'
    ELSE 'MISMATCH ✗'
  END as status;

.quit
```

### Step 2: Test Query Expansion

```bash
uv run python -c "
from finagent.document_processing.semantic_mapper import expand_query_with_concepts

queries = ['洗錢', '內部控制', '資訊揭露']
for q in queries:
    result = expand_query_with_concepts(q)
    print(f'{q}: {len(result[\"concepts\"])} concepts, {len(result[\"search_keywords\"])} keywords')
"
```

**Expected:**
```
洗錢: 1 concepts, 17 keywords
內部控制: 1 concepts, 30 keywords
資訊揭露: 1 concepts, 14 keywords
```

### Step 3: Run Full Test Suite

```bash
# Test query expansion
uv run python test_query_expansion.py

# Test 6 queries
uv run python test_6_queries.py
```

### Step 4: Verify Document Assignments

```bash
sqlite3 data/finagent.db
```

```sql
-- Check distribution
SELECT
  sc.name_zh,
  COUNT(DISTINCT dsc.filename) as doc_count,
  AVG(dsc.confidence) as avg_confidence
FROM semantic_concepts sc
LEFT JOIN document_semantic_concepts dsc ON sc.concept_key = dsc.concept_key
GROUP BY sc.concept_key, sc.name_zh
ORDER BY doc_count DESC;
```

**Expected:** Similar distribution as before rebuild

---

## Performance Considerations

### Full Rebuild Performance

| Step | Time | Notes |
|------|------|-------|
| Drop tables | ~100ms | Fast |
| Create schema | ~200ms | Includes indexes |
| Seed concepts | ~50ms | 23 concepts |
| Seed synonyms | ~150ms | 145 synonyms |
| Build FTS index | ~100ms | Automatic |
| Reassign 196 docs | ~15s | Main bottleneck |
| **Total** | **~16s** | Excluding user confirmation |

### Optimization Tips

**1. Batch Document Assignment**
```python
# Instead of one-by-one
for doc in docs:
    assign_concepts_to_document(doc)

# Use batch insert
concepts_batch = []
for doc in docs:
    concepts = compute_concepts(doc)
    concepts_batch.extend(concepts)

# Single transaction
cursor.executemany("INSERT INTO ...", concepts_batch)
```

**2. Disable Triggers During Bulk Operations**
```sql
PRAGMA defer_foreign_keys = ON;
-- bulk inserts
PRAGMA defer_foreign_keys = OFF;
```

**3. Use WAL Mode**
```sql
PRAGMA journal_mode=WAL;
```

---

## Summary

### Quick Decision Tree

```
Need to rebuild semantic concepts?
│
├─ Adding 1-2 concepts/synonyms?
│  └─> Use Incremental Update (30 seconds)
│
├─ Major restructuring (5+ concepts, hierarchy changes)?
│  └─> Use Full Rebuild (2 minutes)
│
├─ Only fixing document assignments?
│  └─> Document Reassignment Only (15 seconds)
│
└─ Testing changes?
   └─> Use test scripts, don't modify production DB
```

### Key Commands

```bash
# Backup
cp data/finagent.db data/finagent.db.backup.$(date +%Y%m%d_%H%M%S)

# Full rebuild
uv run python rebuild_semantic_concepts.py

# Incremental update
uv run python incremental_update_concepts.py

# Document reassignment
uv run python assign_semantic_concepts.py

# Test changes
uv run python test_query_expansion.py
uv run python test_6_queries.py

# Verify
sqlite3 data/finagent.db "SELECT COUNT(*) FROM semantic_concepts;"
```

### Best Practices

1. **Always backup before rebuild**
2. **Test changes with small dataset first**
3. **Verify counts after rebuild**
4. **Run test suite to confirm functionality**
5. **Document what you changed and why**
6. **Keep backup of working state**

---

**Last Updated:** 2025-11-14
**Related Documentation:**
- [SEMANTIC_CONCEPTS_IMPLEMENTATION.md](SEMANTIC_CONCEPTS_IMPLEMENTATION.md)
- [PHASE1_DOCUMENT_CONCEPT_ASSIGNMENT_COMPLETE.md](PHASE1_DOCUMENT_CONCEPT_ASSIGNMENT_COMPLETE.md)
- [PHASE2_QUERY_EXPANSION_COMPLETE.md](PHASE2_QUERY_EXPANSION_COMPLETE.md)
