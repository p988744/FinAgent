# CLI Database Integration Summary

## Overview

Successfully integrated SQLite database with FinAgent CLI for persistent configuration management. Users can now save, load, and switch between configuration presets without editing files or restarting the CLI.

## Features Implemented

### 1. Enhanced `/config` Command

**Default behavior** (no args):
```bash
finagent> /config
```
- Displays current configuration from database
- Shows whether using a saved preset or default settings
- Indicates count of saved presets
- Lists available subcommands

**Configuration Wizard** (`/config llm`):
```bash
finagent> /config llm
```
- Interactive LLM configuration wizard
- Saves to both .env file AND database
- Auto-reloads configuration (no restart needed)

### 2. New Configuration Management Commands

#### Save Current Config as Preset
```bash
finagent> /config save Production
```
- Saves current LLM configuration as a named preset
- Returns preset ID for future loading
- Does not set as active automatically

#### Load Saved Preset
```bash
finagent> /config load 1
```
- Loads preset by ID and sets as active
- Resets query orchestrator with new config
- No restart required

#### List All Presets
```bash
finagent> /config list        # List all presets
finagent> /config list llm     # List LLM presets only
finagent> /config list embedding  # List embedding presets only
```
- Shows table with:
  - ID (for loading/deleting)
  - Name
  - Type (LLM / 嵌入)
  - Model
  - Status (● 使用中 / ○ 未使用)
- Color-coded status indicators

#### Delete Preset
```bash
finagent> /config delete 2
```
- Deletes a saved preset by ID
- Asks for confirmation
- Cannot delete active preset (by design safety)

#### Reload from Files
```bash
finagent> /config reload
```
- Reloads .env and model_config.yml
- Resets query orchestrator
- Useful after manual file edits

## Configuration Priority

The system follows this priority order:

1. **Active Model Config** (from database) - Highest priority
2. **Database Settings** (settings table)
3. **.env File** (fallback)

When you load a preset with `/config load`, it becomes the active configuration and overrides default settings.

## Database Integration Details

### Updated Functions

**show_config()**
- Now reads from `get_config_manager().get_active_llm_config()`
- Displays source (preset name or "settings file")
- Shows count of saved presets

**save_to_env()**
- Saves to database first via `config_manager.set_setting()`
- Then writes to .env file for backup
- Dual persistence ensures reliability

**New Functions Added:**
- `save_config_preset(name)` - Save current config as preset
- `load_config_preset(config_id)` - Load and activate preset
- `list_config_presets(config_type)` - Display presets table
- `delete_config_preset(config_id)` - Delete preset with confirmation

**Updated handle_config_command():**
- Parse subcommands (save, load, list, delete)
- Extract arguments (name, ID, type)
- Route to appropriate handler

## User Experience Improvements

### Visual Feedback

**Configuration Display:**
```
┌──────────────────── LLM 設定 ────────────────────┐
│ 資料來源              已儲存預設 (Production)      │
│                                                  │
│ 聊天 LLM 提供者        ● OpenAI                   │
│   ├─ 模型             gpt-4o-mini               │
│   └─ API Key          ***                       │
│                                                  │
│ 嵌入模型提供者         ● OpenAI                   │
│   ├─ 模型             text-embedding-3-small    │
│   └─ API Key          ***                       │
│                                                  │
│ 溫度 (Temperature)     0.0                       │
└──────────────────────────────────────────────────┘

已儲存的預設:
  • LLM: 3 個預設 (使用 /config list llm 查看)

提示:
  • 使用 /config llm 修改 LLM 設定
  • 使用 /config save <名稱> 儲存目前設定為預設
  • 使用 /config load <ID> 載入已儲存的預設
  • 使用 /config reload 重新載入設定檔
```

**Presets Table:**
```
┌────────── LLM 預設 ──────────┐
│ ID  名稱         類型  模型              狀態     │
├─────────────────────────────────────────────────┤
│ 1   Production  LLM   gpt-4o           ● 使用中 │
│ 2   Development LLM   gpt-4o-mini      ○ 未使用 │
│ 3   Local Test  LLM   qwen2.5:7b       ○ 未使用 │
└─────────────────────────────────────────────────┘

提示:
  • 使用 /config load <ID> 載入預設
  • 使用 /config delete <ID> 刪除預設
```

### Status Indicators

- **[green]●[/green]** - Active preset (currently in use)
- **[dim]○[/dim]** - Inactive preset (saved but not active)
- **[magenta]已儲存預設[/magenta]** - Configuration source is database
- **[dim]設定檔[/dim]** - Configuration source is .env/database settings

### Error Handling

Clear error messages for common mistakes:
- `✗ 請提供預設名稱: /config save <名稱>`
- `✗ 請提供預設 ID: /config load <ID>`
- `✗ 預設 ID 必須是數字`
- `✗ 找不到預設 ID: 5`
- `✗ 類型必須是 'llm' 或 'embedding'`

## Example Workflow

### Scenario: Switch Between Environments

**1. Save production config:**
```bash
finagent> /config save Production
✓ 已儲存預設 'Production' (ID: 1)
使用 /config load 1 來載入此預設
```

**2. Configure for development:**
```bash
finagent> /config llm
# ... configure with different model ...
✓ 設定已儲存到 .env 檔案
✓ 設定已套用，無需重新啟動 CLI
```

**3. Save development config:**
```bash
finagent> /config save Development
✓ 已儲存預設 'Development' (ID: 2)
```

**4. List all presets:**
```bash
finagent> /config list llm
┌────────── LLM 預設 ──────────┐
│ 1   Production  LLM   gpt-4o        ○ 未使用 │
│ 2   Development LLM   gpt-4o-mini   ● 使用中 │
└─────────────────────────────────────────────┘
```

**5. Switch back to production:**
```bash
finagent> /config load 1
✓ 已載入預設 'Production'
✓ 已重置查詢引擎
✅ 預設已載入！無需重啟 CLI
```

**6. Verify active config:**
```bash
finagent> /config
資料來源: 已儲存預設 (Production)
聊天 LLM 提供者: OpenAI
  ├─ 模型: gpt-4o
```

## Technical Implementation

### Database Schema Used

**settings table:**
- Stores individual settings (llm_model, llm_api_key, etc.)
- Category-based organization (llm, embedding, general)
- Auto-updated timestamps

**model_configs table:**
- Stores complete configuration presets
- Fields: name, config_type, api_key, base_url, model, temperature, is_active
- Only one active config per type (enforced by triggers)

### Integration Points

**ConfigManager** ([src/finagent/config_manager.py](../../src/finagent/config_manager.py)):
```python
config_manager = get_config_manager()

# Get active configuration
llm_config = config_manager.get_active_llm_config()
# Returns: {'api_key': '...', 'base_url': '...', 'model': '...',
#           'temperature': 0.0, 'source': 'database', 'config_name': 'Production'}

# Save preset
config_manager.save_model_config(
    name="Production",
    config_type="llm",
    api_key="sk-...",
    base_url="",
    model="gpt-4o",
    temperature=0.0,
    set_active=False
)

# Load preset
config_manager.set_active_model_config(config_id=1)

# List presets
presets = config_manager.get_all_model_configs("llm")
```

**Config Commands** ([src/finagent/cli/commands/config.py](../../src/finagent/cli/commands/config.py)):
- Integrated with `get_config_manager()`
- All configuration reads go through database
- All configuration writes update both database and .env

## Backwards Compatibility

The system remains fully backwards compatible:

1. **Existing .env files** - Still work exactly as before
2. **Manual .env edits** - Synced to database on next `/config reload`
3. **No database** - Auto-creates on first run
4. **Legacy workflows** - `/config llm` wizard works identically

## Benefits

### For Users

✅ **Quick switching** - Change configs with single command, no editing
✅ **Named presets** - Meaningful names instead of remembering settings
✅ **No restart** - Changes apply immediately
✅ **History preserved** - All saved configs available anytime
✅ **Visual management** - See all presets in table format

### For Development

✅ **Multiple environments** - Easily switch between dev/staging/prod
✅ **Team collaboration** - Share preset configurations
✅ **Testing** - Quickly test different models/endpoints
✅ **Rollback** - Instantly revert to previous config

### For Operations

✅ **Audit trail** - Database tracks all config changes with timestamps
✅ **Consistency** - Database ensures config integrity
✅ **Recovery** - .env file serves as backup
✅ **Monitoring** - Can query database for active configurations

## Files Modified

- [src/finagent/cli/commands/config.py](../../src/finagent/cli/commands/config.py) - Main changes
  - `show_config()` - Read from database
  - `save_to_env()` - Write to database + .env
  - `save_config_preset()` - New
  - `load_config_preset()` - New
  - `list_config_presets()` - New
  - `delete_config_preset()` - New
  - `handle_config_command()` - Extended with subcommands

## Next Steps (Not Implemented)

1. **History Logging**
   - Add `/history` command to view query history
   - Add `/stats` command to view usage statistics
   - Integrate history logging in query orchestrator

2. **Export/Import**
   - Export presets to YAML/JSON
   - Import presets from files
   - Share presets between team members

3. **Advanced Features**
   - Preset groups (dev, staging, prod)
   - Auto-switch based on time/day
   - Cost tracking per preset
   - Performance metrics per preset

## Testing

To test the integration:

```bash
# Start CLI
uv run finagent

# Show current config
/config

# Save as preset
/config save MyPreset

# List presets
/config list

# Load preset
/config load 1

# Delete preset
/config delete 2
```

## Database Location

- **Path**: `./data/finagent.db`
- **Format**: SQLite 3
- **Access**: `sqlite3 ./data/finagent.db`

## Summary

✅ Complete CLI integration with database
✅ Save/load/list/delete configuration presets
✅ Visual preset management with Rich tables
✅ Instant configuration switching (no restart)
✅ Backwards compatible with existing workflows
✅ Database + .env dual persistence
✅ Auto-initialization on first run
✅ Comprehensive error handling

The configuration management system is now production-ready with full database integration!
