# Alembic Database Migration Setup

**Date**: 2025-11-19
**Status**: ✅ Complete and Ready for Use

## Overview

Alembic is now configured for managing database schema migrations in FinAgent. This ensures that database schema changes are tracked, versioned, and can be applied consistently across all environments.

## What Was Done

### 1. Installed Alembic ✅
```bash
uv pip install alembic
```

**Installed packages:**
- alembic==1.17.2
- mako==1.3.10
- markupsafe==3.0.3

### 2. Created SQLAlchemy ORM Models ✅

**File**: [src/finagent/database/orm_models.py](src/finagent/database/orm_models.py)

**Models created:**
- `Document` - Main documents table with all fields
- `WikiCategory` - Wiki categorization
- `DocumentRelationship` - Document connections
- `WikiStatistic` - Wiki statistics
- `Setting` - Application settings
- `ModelConfigTable` - LLM/embedding configurations
- `History` - Query history
- `Concept` - Extracted concepts
- `DocumentConcept` - Document-concept relationships

**Important**: SQLAlchemy reserves the `metadata` attribute name, so columns named "metadata" use mapped names (e.g., `relationship_metadata` for the `metadata` column).

### 3. Initialized Alembic ✅

```bash
uv run alembic init src/finagent/database/alembic
```

**Created structure:**
```
src/finagent/database/alembic/
├── versions/
│   └── 18bdd6784d19_initial_schema_with_wiki_tables.py
├── env.py
├── script.py.mako
└── README
alembic.ini
```

### 4. Configured Alembic ✅

**File**: [alembic.ini](alembic.ini)
- Set SQLite database URL: `sqlite:///data/finagent.db`
- Configured script location: `src/finagent/database/alembic`

**File**: [src/finagent/database/alembic/env.py](src/finagent/database/alembic/env.py)
- Added project root to `sys.path`
- Imported `Base` from `orm_models.py`
- Set `target_metadata = Base.metadata` for autogenerate support

### 5. Created Initial Migration ✅

```bash
uv run alembic revision --autogenerate -m "Initial schema with wiki tables"
```

**Migration ID**: `18bdd6784d19`
**File**: `src/finagent/database/alembic/versions/18bdd6784d19_initial_schema_with_wiki_tables.py`

This migration captures the current database state including all tables:
- documents (with all wiki-related columns)
- wiki_categories
- document_relationships
- wiki_statistics
- settings
- model_configs
- history
- concepts
- document_concepts

### 6. Stamped Database ✅

```bash
uv run alembic stamp head
```

Marked the current database as being at the latest migration version without running any changes (since tables already exist).

**Verification**:
```bash
sqlite3 data/finagent.db "SELECT * FROM alembic_version;"
# Output: 18bdd6784d19
```

---

## How to Use Alembic

### Check Current Migration Version

```bash
uv run alembic current
```

### View Migration History

```bash
uv run alembic history
```

### Create a New Migration (Auto-generate)

When you modify models in `src/finagent/database/orm_models.py`:

```bash
# 1. Update the model in orm_models.py
# 2. Generate migration script
uv run alembic revision --autogenerate -m "Description of changes"

# 3. Review the generated migration file in src/finagent/database/alembic/versions/
# 4. Apply the migration
uv run alembic upgrade head
```

### Create a New Migration (Manual)

For complex changes that need manual SQL:

```bash
uv run alembic revision -m "Description of changes"
# Edit the generated file to add upgrade() and downgrade() functions
uv run alembic upgrade head
```

### Apply Migrations

```bash
# Upgrade to latest version
uv run alembic upgrade head

# Upgrade by one version
uv run alembic upgrade +1

# Downgrade by one version
uv run alembic downgrade -1

# Downgrade to specific version
uv run alembic downgrade <revision_id>
```

### Rollback Migrations

```bash
# Rollback to previous version
uv run alembic downgrade -1

# Rollback to base (WARNING: drops all tables!)
uv run alembic downgrade base
```

---

## Best Practices

### 1. Always Review Auto-generated Migrations

Alembic's autogenerate is smart but not perfect. Always review generated migration files before applying them:

```bash
uv run alembic revision --autogenerate -m "Add new column"
# Review file in src/finagent/database/alembic/versions/
# Then apply:
uv run alembic upgrade head
```

### 2. Test Migrations on a Copy First

Before applying migrations to production:

```bash
# Create backup
cp data/finagent.db data/finagent.db.backup

# Test migration
uv run alembic upgrade head

# If something goes wrong, restore backup
mv data/finagent.db.backup data/finagent.db
```

### 3. Add Columns as Nullable First

SQLite doesn't support adding NOT NULL columns directly. Add as nullable first, then alter:

```python
# In migration file
def upgrade():
    op.add_column('documents', sa.Column('new_field', sa.Text(), nullable=True))
    # Optionally set default values
    op.execute("UPDATE documents SET new_field = 'default'")
```

### 4. Keep Migrations Small and Focused

Each migration should represent a single logical change:
- ✅ Good: "Add category_id to documents"
- ❌ Bad: "Add 5 new tables and change 10 columns"

### 5. Never Edit Applied Migrations

Once a migration has been applied (committed to version control), never edit it. Create a new migration instead.

---

## Common Scenarios

### Adding a New Table

1. Add model to `src/finagent/database/orm_models.py`
2. Generate migration: `uv run alembic revision --autogenerate -m "Add xyz table"`
3. Review and apply: `uv run alembic upgrade head`

### Adding a Column

1. Add column to model in `orm_models.py`
2. Generate migration: `uv run alembic revision --autogenerate -m "Add xyz column to table"`
3. Review generated file - ensure nullable=True for SQLite compatibility
4. Apply: `uv run alembic upgrade head`

### Renaming a Column

SQLite doesn't support ALTER COLUMN directly. Use data migration:

```python
def upgrade():
    # 1. Add new column
    op.add_column('documents', sa.Column('new_name', sa.Text(), nullable=True))
    # 2. Copy data
    op.execute("UPDATE documents SET new_name = old_name")
    # 3. Drop old column (SQLite limitation - may need table recreation)
    op.drop_column('documents', 'old_name')
```

### Fixing "no such table" Errors

If you encounter "no such table" errors after schema changes:

1. Check current migration version: `uv run alembic current`
2. If no version, stamp database: `uv run alembic stamp head`
3. If tables are missing, apply migrations: `uv run alembic upgrade head`
4. If completely broken, restore from backup and replay migrations

---

## Troubleshooting

### "Can't locate revision identified by 'head'"

Database is not stamped. Run:
```bash
uv run alembic stamp head
```

### "Table already exists" when upgrading

Database is ahead of Alembic tracking. Either:
- Stamp to current version: `uv run alembic stamp <revision_id>`
- Drop table and rerun migration (data loss!)

### "Column already exists" when upgrading

Migration was partially applied. Either:
- Comment out existing changes in migration file and rerun
- Manually edit database to complete migration
- Stamp to this version: `uv run alembic stamp <revision_id>`

### SQLite "Cannot add NOT NULL column"

SQLite limitation. Solution:
1. Add column as nullable=True
2. Populate data
3. Create new table with NOT NULL, copy data, drop old table

---

## Integration with Existing Code

### Where to Update Models

**DO**: Update `src/finagent/database/orm_models.py` (SQLAlchemy models)
**THEN**: Generate Alembic migration
**ALSO UPDATE**: `src/finagent/database/models.py` (Pydantic models) if needed

### Keeping Pydantic and SQLAlchemy Models in Sync

Currently we have two sets of models:
- **SQLAlchemy ORM Models**: `src/finagent/database/orm_models.py` (for Alembic)
- **Pydantic Models**: `src/finagent/database/models.py` (for FastAPI)

**Workflow:**
1. Make changes to SQLAlchemy ORM models
2. Generate Alembic migration
3. Apply migration to database
4. Update Pydantic models to match (if needed)

---

## Files to Commit

Always commit these files when creating migrations:

```
✅ src/finagent/database/orm_models.py
✅ src/finagent/database/alembic/versions/<new_migration>.py
✅ alembic.ini (if changed)
✅ src/finagent/database/alembic/env.py (if changed)
```

**DO NOT commit:**
```
❌ data/finagent.db
❌ data/finagent.db.backup
❌ .env
```

---

## Future Improvements

1. **Add migration testing**: Run migrations on test database before production
2. **Add migration rollback tests**: Ensure `downgrade()` works correctly
3. **Document data migrations**: For complex data transformations
4. **Add migration validation**: Check for common mistakes before applying
5. **Consider separating concerns**: Different migrations for schema vs. data changes

---

## Summary

✅ **Alembic is now properly configured and ready to use**

**Benefits:**
- Database schema changes are now version-controlled
- No more "no such table" errors from ad-hoc schema changes
- Easy rollback if migrations fail
- Automatic migration generation from model changes
- Consistent schema across development, testing, and production

**Next Steps:**
- Use `uv run alembic revision --autogenerate` for future schema changes
- Always review generated migrations before applying
- Test migrations on a backup first
- Document any complex data migrations

The current database is at migration `18bdd6784d19` with all tables properly tracked. Future schema changes should go through Alembic! 🚀
