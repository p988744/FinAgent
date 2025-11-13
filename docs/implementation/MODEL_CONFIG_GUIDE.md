# Model Configuration Guide

## Overview

FinAgent allows you to customize LLM model choices through the `model_config.yml` file. This gives you full control over which models appear in the `/config llm` wizard without modifying code.

## Quick Start

1. **View current configuration**:
   ```bash
   finagent> /config
   ```

2. **Edit model choices**:
   ```bash
   # Edit backend/model_config.yml
   vim backend/model_config.yml
   ```

3. **Reload configuration** (no restart needed):
   ```bash
   finagent> /config reload
   ```

## Configuration File

Location: `backend/model_config.yml`

### Structure

```yaml
# OpenAI Chat Models
openai_chat_models:
  - id: "gpt-4o-mini"
    name: "GPT-4o Mini (Fast & Cheap)"
    description: "Affordable and fast, suitable for most tasks"
    recommended: true
    default: true  # This will be the default selection

# OpenAI Embedding Models
openai_embedding_models:
  - id: "text-embedding-3-small"
    name: "Text Embedding 3 Small"
    description: "Best performance/cost ratio"
    recommended: true
    default: true
    dimensions: 1536

# Local LLM Presets
local_llm_presets:
  - name: "Ollama (Qwen 2.5)"
    base_url: "http://localhost:11434/v1"
    model: "qwen2.5:7b"
    api_key: "ollama"
    description: "Qwen 2.5 7B via Ollama"
    recommended: true

# Settings
settings:
  fetch_openai_models_dynamically: true
  use_static_model_list: false
  max_models_to_display: 10
  show_only_recommended: false
```

## Adding Custom Models

### OpenAI Chat Model

```yaml
openai_chat_models:
  - id: "gpt-4o"                           # Model ID (required)
    name: "GPT-4o (Latest)"                # Display name (required)
    description: "Most capable model"      # Description (optional)
    recommended: true                      # Show in recommended list (optional)
    default: false                         # Set as default choice (optional)
```

### OpenAI Embedding Model

```yaml
openai_embedding_models:
  - id: "text-embedding-3-large"
    name: "Text Embedding 3 Large"
    description: "Highest quality embeddings"
    recommended: true
    default: false
    dimensions: 3072                       # Embedding dimensions (optional)
```

### Local LLM Preset

```yaml
local_llm_presets:
  - name: "Custom Local Model"             # Preset name (required)
    base_url: "http://localhost:8080/v1"   # OpenAI-compatible endpoint (required)
    model: "my-model-name"                 # Model name (required)
    api_key: "custom-key"                  # API key (required, can be any string)
    description: "My custom model"         # Description (optional)
    recommended: true                      # Show in recommended list (optional)
```

## Settings Explained

### `fetch_openai_models_dynamically`

**Default**: `true`

When `true`, the system will fetch the latest model list from OpenAI API and merge it with your static list.

When `false`, only models defined in `model_config.yml` will be shown.

```yaml
settings:
  fetch_openai_models_dynamically: false  # Use only static list
```

### `use_static_model_list`

**Default**: `false`

When `true`, completely disables API fetching and uses only models from `model_config.yml`.

```yaml
settings:
  use_static_model_list: true  # Never fetch from API
```

### `max_models_to_display`

**Default**: `10`

Maximum number of models to show in the selection menu.

```yaml
settings:
  max_models_to_display: 5  # Show only top 5 models
```

### `show_only_recommended`

**Default**: `false`

When `true`, only shows models marked with `recommended: true`.

```yaml
settings:
  show_only_recommended: true  # Filter to recommended only
```

### `temperature_presets`

Predefined temperature values for different use cases:

```yaml
settings:
  temperature_presets:
    deterministic: 0.0    # For factual tasks (default)
    balanced: 0.3         # Slightly creative
    creative: 0.7         # More variety
    very_creative: 1.0    # Maximum creativity
```

## Use Cases

### Use Case 1: Limit to Specific Models

**Scenario**: You only want to use `gpt-4o-mini` and `gpt-3.5-turbo`.

**Solution**:
```yaml
openai_chat_models:
  - id: "gpt-4o-mini"
    name: "GPT-4o Mini"
    description: "Fast and cheap"
    recommended: true
    default: true

  - id: "gpt-3.5-turbo"
    name: "GPT-3.5 Turbo"
    description: "Legacy model"
    recommended: false

settings:
  use_static_model_list: true  # Don't fetch from API
```

Then run `/config reload` to apply.

### Use Case 2: Add Custom Local Model

**Scenario**: You're running a custom model on LM Studio.

**Solution**:
```yaml
local_llm_presets:
  - name: "My LM Studio Model"
    base_url: "http://localhost:1234/v1"
    model: "my-custom-llama-3"
    api_key: "lm-studio"
    description: "Custom fine-tuned Llama 3"
    recommended: true
```

Then:
1. Run `/config reload`
2. Run `/config llm`
3. Select "Local LLM" provider
4. Choose "My LM Studio Model" from presets

### Use Case 3: Show Only Recommended Models

**Scenario**: Simplify choices by hiding legacy models.

**Solution**:
```yaml
settings:
  show_only_recommended: true

openai_chat_models:
  - id: "gpt-4o"
    recommended: true    # Will be shown

  - id: "gpt-4"
    recommended: false   # Will be hidden

  - id: "gpt-4o-mini"
    recommended: true    # Will be shown
```

### Use Case 4: Always Fetch Latest Models

**Scenario**: You want to automatically get new models as OpenAI releases them.

**Solution**:
```yaml
settings:
  fetch_openai_models_dynamically: true  # Fetch from API
  use_static_model_list: false           # Don't limit to static list
  max_models_to_display: 15              # Show up to 15 models
```

## Commands

### View Current Configuration

```bash
finagent> /config
```

Shows your current LLM settings including provider, model, and API key status.

### Configure LLM Interactively

```bash
finagent> /config llm
```

Launches interactive wizard to:
- Choose provider (OpenAI or Local LLM)
- Select model from available options
- Configure API keys
- Choose embedding model

**Note**: Model choices in the wizard come from `model_config.yml`.

### Reload Configuration

```bash
finagent> /config reload
```

Reloads both:
- `.env` file (API keys, settings)
- `model_config.yml` (model choices)

No restart required! The CLI will immediately use the new configuration.

## Best Practices

### 1. Keep Recommended Models Updated

Mark your most-used models as `recommended: true`:

```yaml
openai_chat_models:
  - id: "gpt-4o-mini"
    recommended: true  # Your go-to model
    default: true      # Default selection

  - id: "gpt-4o"
    recommended: true  # For complex tasks

  - id: "gpt-3.5-turbo"
    recommended: false # Rarely used
```

### 2. Document Custom Presets

Add clear descriptions for custom local models:

```yaml
local_llm_presets:
  - name: "Legal RAG Model"
    description: "Fine-tuned on Taiwan legal documents (Qwen 2.5 14B)"
    base_url: "http://192.168.1.100:8000/v1"
    model: "qwen2.5-14b-legal"
    api_key: "custom"
```

### 3. Use Static List for Production

For consistency in production, disable dynamic fetching:

```yaml
settings:
  use_static_model_list: true
  show_only_recommended: true
```

This ensures the same models are always available.

### 4. Version Control

Commit `model_config.yml` to your repository:

```bash
git add backend/model_config.yml
git commit -m "chore: update model configuration"
```

This allows team members to share the same model choices.

### 5. Test After Changes

After editing `model_config.yml`:

1. Reload: `/config reload`
2. Verify: `/config` (check settings)
3. Test: `/config llm` (see if models appear correctly)

## Troubleshooting

### Issue: "model_config.yml not found"

**Solution**: Make sure the file exists in one of these locations:
- `./model_config.yml` (project root)
- `./backend/model_config.yml` (backend directory)

Create it if missing:
```bash
cp backend/model_config.yml.example backend/model_config.yml
```

### Issue: YAML Syntax Error

**Solution**: Check YAML syntax. Common mistakes:
- Missing colons (`:`)
- Inconsistent indentation (use 2 spaces)
- Forgot to quote strings with special characters

Validate with:
```bash
python -c "import yaml; yaml.safe_load(open('backend/model_config.yml'))"
```

### Issue: Models Not Appearing

**Symptoms**: After reload, models don't show in `/config llm`

**Solutions**:
1. Check `use_static_model_list` setting
2. Verify model IDs are correct
3. Check if `show_only_recommended` is hiding models
4. Look for error messages in `/config reload` output

### Issue: Reload Failed

**Symptoms**: `/config reload` shows errors

**Solutions**:
1. Check `.env` file syntax
2. Validate `model_config.yml` YAML
3. Check file permissions
4. Look at full error traceback

## Example Configurations

### Minimal Configuration (OpenAI Only)

```yaml
openai_chat_models:
  - id: "gpt-4o-mini"
    name: "GPT-4o Mini"
    description: "Default model"
    default: true

openai_embedding_models:
  - id: "text-embedding-3-small"
    name: "Text Embedding 3 Small"
    default: true

settings:
  use_static_model_list: true
  fetch_openai_models_dynamically: false
```

### Local-Only Configuration

```yaml
local_llm_presets:
  - name: "Ollama Qwen"
    base_url: "http://localhost:11434/v1"
    model: "qwen2.5:7b"
    api_key: "ollama"
    description: "Local Qwen model"
    recommended: true

# Still need embedding model from OpenAI
openai_embedding_models:
  - id: "text-embedding-3-small"
    name: "OpenAI Embeddings"
    default: true

settings:
  use_static_model_list: true
```

### Hybrid Configuration (OpenAI + Local)

```yaml
openai_chat_models:
  - id: "gpt-4o"
    name: "GPT-4o (Cloud)"
    recommended: true

  - id: "gpt-4o-mini"
    name: "GPT-4o Mini (Cloud)"
    recommended: true
    default: true

local_llm_presets:
  - name: "Local Qwen"
    base_url: "http://localhost:11434/v1"
    model: "qwen2.5:7b"
    api_key: "ollama"
    recommended: true

  - name: "Local Llama"
    base_url: "http://localhost:11434/v1"
    model: "llama3.1:8b"
    api_key: "ollama"
    recommended: false

openai_embedding_models:
  - id: "text-embedding-3-small"
    name: "OpenAI Embeddings"
    default: true

settings:
  fetch_openai_models_dynamically: false
  use_static_model_list: true
  show_only_recommended: true
```

## Migration from Old Configuration

If you previously configured models directly in code:

1. Create `backend/model_config.yml`
2. Add your custom models to the file
3. Run `/config reload`
4. Test with `/config llm`

The new system is fully backward compatible - if `model_config.yml` doesn't exist, the system falls back to the previous behavior.

## Summary

- **Edit**: `backend/model_config.yml`
- **Reload**: `/config reload` (no restart!)
- **View**: `/config`
- **Configure**: `/config llm`

For more help, see:
- [Config Command Documentation](CLI_GUIDE.md#config-command)
- [Configuration Settings](../backend/.env.example)
