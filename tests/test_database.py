"""Test database functionality."""

import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.database import Database, Setting, ModelConfig, History
from finagent.config_manager import ConfigManager


def test_database_creation():
    """Test database creation and schema initialization."""
    print("Testing database creation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Check that database file was created
        assert db_path.exists(), "Database file should exist"
        print("✅ Database created successfully")


def test_settings_operations():
    """Test settings CRUD operations."""
    print("\nTesting settings operations...")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create setting
        setting = db.set_setting(
            key="test_key",
            value="test_value",
            category="test",
            description="Test setting",
        )
        assert setting.key == "test_key"
        assert setting.value == "test_value"
        print("✅ Setting created")

        # Read setting
        retrieved = db.get_setting("test_key")
        assert retrieved is not None
        assert retrieved.value == "test_value"
        print("✅ Setting retrieved")

        # Update setting
        updated = db.set_setting("test_key", "new_value", category="test")
        assert updated.value == "new_value"
        print("✅ Setting updated")

        # Get all settings
        all_settings = db.get_all_settings()
        assert len(all_settings) == 1
        print("✅ All settings retrieved")

        # Get settings by category
        category_settings = db.get_all_settings(category="test")
        assert len(category_settings) == 1
        print("✅ Settings filtered by category")

        # Delete setting
        deleted = db.delete_setting("test_key")
        assert deleted == True
        assert db.get_setting("test_key") is None
        print("✅ Setting deleted")


def test_model_config_operations():
    """Test model configuration CRUD operations."""
    print("\nTesting model config operations...")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create LLM config
        config = db.save_model_config(
            name="Test LLM",
            config_type="llm",
            api_key="test-key",
            base_url="http://localhost:11434/v1",
            model="qwen2.5:7b",
            temperature=0.0,
            is_active=True,
        )
        assert config.name == "Test LLM"
        assert config.is_active == True
        print("✅ Model config created")

        # Get active config
        active = db.get_active_model_config("llm")
        assert active is not None
        assert active.name == "Test LLM"
        print("✅ Active model config retrieved")

        # Create another config and set it active (should deactivate the first)
        config2 = db.save_model_config(
            name="Test LLM 2",
            config_type="llm",
            api_key="test-key-2",
            base_url="http://localhost:11434/v1",
            model="llama3.1:8b",
            temperature=0.3,
            is_active=True,
        )
        print("✅ Second model config created")

        # Check that first config is now inactive
        config1_updated = db.get_model_config(config.id)
        assert config1_updated.is_active == False
        print("✅ Only one config can be active per type")

        # Get all configs
        all_configs = db.get_all_model_configs("llm")
        assert len(all_configs) == 2
        print("✅ All model configs retrieved")

        # Update config
        updated = db.update_model_config(config.id, temperature=0.5)
        assert updated.temperature == 0.5
        print("✅ Model config updated")

        # Delete config
        deleted = db.delete_model_config(config.id)
        assert deleted == True
        print("✅ Model config deleted")


def test_history_operations():
    """Test history logging operations."""
    print("\nTesting history operations...")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Add history entry
        history = db.add_history(
            query="玉山銀行洗錢防制裁罰",
            response="找到5筆相關記錄",
            session_id="test-session",
            model_used="gpt-4o-mini",
            tokens_used=1500,
            cost_usd=0.0015,
            processing_time_seconds=5.2,
            success=True,
            metadata={"sources": 5, "citations": 3},
        )
        assert history.query == "玉山銀行洗錢防制裁罰"
        print("✅ History entry created")

        # Get history
        all_history = db.get_history(limit=10)
        assert len(all_history) == 1
        print("✅ History retrieved")

        # Get history by session
        session_history = db.get_history(session_id="test-session")
        assert len(session_history) == 1
        print("✅ History filtered by session")

        # Get history stats
        stats = db.get_history_stats()
        assert stats["total_queries"] == 1
        assert stats["successful_queries"] == 1
        assert stats["total_tokens"] == 1500
        print("✅ History statistics calculated")
        print(f"   Stats: {stats}")

        # Clear history
        deleted_count = db.clear_history()
        assert deleted_count == 1
        print("✅ History cleared")


def test_config_manager():
    """Test ConfigManager integration."""
    print("\nTesting ConfigManager...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up temporary database
        db_path = Path(tmpdir) / "test.db"
        os.environ["FINAGENT_DB_PATH"] = str(db_path)

        # Create ConfigManager (will initialize from env)
        config_manager = ConfigManager()

        # Test getting active LLM config
        llm_config = config_manager.get_active_llm_config()
        assert "api_key" in llm_config
        assert "model" in llm_config
        print("✅ LLM config retrieved")
        print(f"   LLM: {llm_config}")

        # Test getting active embedding config
        embedding_config = config_manager.get_active_embedding_config()
        assert "api_key" in embedding_config
        assert "model" in embedding_config
        print("✅ Embedding config retrieved")
        print(f"   Embedding: {embedding_config}")

        # Test saving model config
        saved_config = config_manager.save_model_config(
            name="Test Config",
            config_type="llm",
            api_key="test-key",
            base_url="http://localhost:11434/v1",
            model="qwen2.5:7b",
            temperature=0.0,
            set_active=True,
        )
        assert saved_config.name == "Test Config"
        print("✅ Model config saved via ConfigManager")

        # Test getting model choices (from YAML)
        try:
            choices = config_manager.get_model_choices()
            print("✅ Model choices loaded from YAML")
            print(f"   OpenAI chat models: {len(choices['openai_chat_models'])}")
            print(f"   OpenAI embedding models: {len(choices['openai_embedding_models'])}")
            print(f"   Local presets: {len(choices['local_llm_presets'])}")
        except Exception as e:
            print(f"⚠️  Model choices not loaded (model_config.yml not found): {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Database Functionality Tests")
    print("=" * 60)

    try:
        test_database_creation()
        test_settings_operations()
        test_model_config_operations()
        test_history_operations()
        test_config_manager()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
