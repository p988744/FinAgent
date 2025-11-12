"""Configuration command handlers."""

import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from finagent.config import settings, reload_settings
from finagent.model_config_loader import get_model_config, reload_model_config

console = Console()


# Default OpenAI model choices (fallback if API call fails)
DEFAULT_OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
]

DEFAULT_OPENAI_EMBEDDING_MODELS = [
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
]


def get_available_openai_models(api_key: str) -> list:
    """
    Fetch available OpenAI models from API or model_config.yml.

    Args:
        api_key: OpenAI API key

    Returns:
        List of available model IDs
    """
    # Check if should use static list from model_config.yml
    try:
        model_config = get_model_config()
        if model_config.use_static_model_list():
            # Use models from model_config.yml only
            models = model_config.get_openai_chat_models(
                recommended_only=model_config.show_only_recommended()
            )
            return [m.id for m in models[:model_config.get_max_models_to_display()]]

        # Check if should skip dynamic fetching
        if not model_config.should_fetch_openai_models_dynamically():
            models = model_config.get_openai_chat_models()
            return [m.id for m in models[:model_config.get_max_models_to_display()]]
    except FileNotFoundError:
        # model_config.yml not found, use legacy behavior
        pass
    except Exception as e:
        console.print(f"[dim]無法載入 model_config.yml: {e}[/dim]")

    if not api_key or api_key == "":
        try:
            model_config = get_model_config()
            models = model_config.get_openai_chat_models()
            return [m.id for m in models[:10]]
        except:
            return DEFAULT_OPENAI_MODELS

    try:
        import httpx

        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5.0
        )

        if response.status_code == 200:
            data = response.json()
            all_models = [model["id"] for model in data.get("data", [])]

            # Filter for chat models (gpt-*)
            chat_models = [
                m for m in all_models
                if m.startswith("gpt-") and not m.startswith("gpt-3.5-turbo-instruct")
            ]

            # Remove dated versions (e.g., gpt-4o-2024-08-06 → gpt-4o)
            # Keep only canonical model names without date suffixes
            canonical_models = {}
            for model in chat_models:
                # Check if model has date suffix (YYYY-MM-DD)
                import re
                # Remove date pattern like -2024-08-06, -0125, etc.
                canonical = re.sub(r'-\d{4}(-\d{2}){0,2}$', '', model)

                # Prefer shorter canonical names (e.g., gpt-4o over gpt-4o-2024-08-06)
                if canonical not in canonical_models or len(model) < len(canonical_models[canonical]):
                    canonical_models[canonical] = model

            # Use the canonical names
            chat_models = list(canonical_models.keys())

            # Sort by preference: gpt-4o variants first, then gpt-4, then gpt-3.5
            priority_order = ["gpt-4o", "gpt-4", "gpt-3.5"]

            def sort_key(model):
                for i, prefix in enumerate(priority_order):
                    if model.startswith(prefix):
                        return (i, model)
                return (len(priority_order), model)

            chat_models.sort(key=sort_key)

            # Limit to top 10 most relevant models
            return chat_models[:10] if chat_models else DEFAULT_OPENAI_MODELS
        else:
            console.print(f"[dim]無法取得模型列表（使用預設列表）[/dim]")
            return DEFAULT_OPENAI_MODELS

    except Exception as e:
        console.print(f"[dim]無法連接 OpenAI API（使用預設列表）[/dim]")
        return DEFAULT_OPENAI_MODELS


def get_available_embedding_models(api_key: str) -> list:
    """
    Fetch available OpenAI embedding models from API or model_config.yml.

    Args:
        api_key: OpenAI API key

    Returns:
        List of available embedding model IDs
    """
    # Check if should use static list from model_config.yml
    try:
        model_config = get_model_config()
        if model_config.use_static_model_list():
            models = model_config.get_openai_embedding_models(
                recommended_only=model_config.show_only_recommended()
            )
            return [m.id for m in models]

        if not model_config.should_fetch_openai_models_dynamically():
            models = model_config.get_openai_embedding_models()
            return [m.id for m in models]
    except FileNotFoundError:
        pass
    except Exception as e:
        console.print(f"[dim]無法載入 model_config.yml: {e}[/dim]")

    if not api_key or api_key == "":
        try:
            model_config = get_model_config()
            models = model_config.get_openai_embedding_models()
            return [m.id for m in models]
        except:
            return DEFAULT_OPENAI_EMBEDDING_MODELS

    try:
        import httpx

        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5.0
        )

        if response.status_code == 200:
            data = response.json()
            all_models = [model["id"] for model in data.get("data", [])]

            # Filter for embedding models
            embedding_models = [
                m for m in all_models
                if "embedding" in m
            ]

            # Remove dated versions (e.g., text-embedding-3-small-2024-01 → text-embedding-3-small)
            import re
            canonical_embeddings = {}
            for model in embedding_models:
                # Remove date pattern
                canonical = re.sub(r'-\d{4}(-\d{2}){0,2}$', '', model)

                # Prefer shorter canonical names
                if canonical not in canonical_embeddings or len(model) < len(canonical_embeddings[canonical]):
                    canonical_embeddings[canonical] = model

            embedding_models = list(canonical_embeddings.keys())

            # Sort: text-embedding-3 first, then text-embedding-ada
            def sort_key(model):
                if "text-embedding-3" in model:
                    return (0, model)
                elif "text-embedding-ada" in model:
                    return (1, model)
                else:
                    return (2, model)

            embedding_models.sort(key=sort_key)

            return embedding_models if embedding_models else DEFAULT_OPENAI_EMBEDDING_MODELS
        else:
            return DEFAULT_OPENAI_EMBEDDING_MODELS

    except Exception:
        return DEFAULT_OPENAI_EMBEDDING_MODELS


def show_config():
    """Display current LLM configuration."""
    table = Table(title="LLM 設定", show_header=True, header_style="bold cyan")
    table.add_column("設定項目", style="white", width=25)
    table.add_column("目前值", style="cyan")

    # Chat/Completion LLM provider
    if settings.use_local_llm:
        table.add_row("聊天 LLM 提供者", "[yellow]本地 LLM[/yellow]")
        table.add_row("  ├─ URL", settings.local_llm_base_url)
        table.add_row("  ├─ 模型", settings.local_llm_model)
        table.add_row("  └─ API Key", "***" if settings.local_llm_api_key else "[red]未設定[/red]")
    else:
        table.add_row("聊天 LLM 提供者", "[green]OpenAI[/green]")
        table.add_row("  ├─ 模型", settings.openai_model)
        table.add_row("  └─ API Key", "***" if settings.openai_api_key else "[red]未設定[/red]")

    # Embedding provider
    table.add_row("", "")  # Spacer
    if settings.use_local_embedding:
        table.add_row("嵌入模型提供者", "[yellow]本地嵌入模型[/yellow]")
        table.add_row("  ├─ 模型", settings.local_embedding_model)

        # Show URL and API key if different from LLM
        embedding_url = settings.local_embedding_base_url or settings.local_llm_base_url
        embedding_key = settings.local_embedding_api_key or settings.local_llm_api_key

        if settings.local_embedding_base_url:
            table.add_row("  ├─ URL", embedding_url)
        else:
            table.add_row("  ├─ URL", f"{embedding_url} [dim](共用 LLM)[/dim]")

        if settings.local_embedding_api_key:
            table.add_row("  └─ API Key", "***")
        else:
            table.add_row("  └─ API Key", "[dim]*** (共用 LLM)[/dim]")
    else:
        table.add_row("嵌入模型提供者", "[green]OpenAI[/green]")
        table.add_row("  ├─ 模型", settings.openai_embedding_model)
        table.add_row("  └─ API Key", "***" if settings.openai_api_key else "[red]未設定[/red]")

    # Other settings
    table.add_row("", "")  # Spacer
    table.add_row("溫度 (Temperature)", str(settings.openai_temperature))

    console.print()
    console.print(table)
    console.print()

    # Show hints
    console.print("[dim]提示:[/dim]")
    console.print("[dim]  • 使用 [cyan]/config llm[/cyan] 修改 LLM 設定[/dim]")
    console.print("[dim]  • 使用 [cyan]/config reload[/cyan] 重新載入設定檔 (.env 和 model_config.yml)[/dim]")
    console.print("[dim]  • 編輯 [cyan]model_config.yml[/cyan] 來自訂模型列表[/dim]")
    console.print()


def configure_llm():
    """Interactive LLM configuration."""
    console.print()
    console.print(Panel("[bold cyan]LLM 設定精靈[/bold cyan]", border_style="cyan"))
    console.print()

    # Step 1: Choose provider
    console.print("[bold]步驟 1/3: 選擇 LLM 提供者[/bold]")
    console.print()
    console.print("1. OpenAI (需要 API 金鑰)")
    console.print("2. 本地 LLM (OpenAI 相容 API，例如 Ollama)")
    console.print()

    provider = Prompt.ask(
        "請選擇提供者",
        choices=["1", "2"],
        default="1"
    )

    use_local = provider == "2"

    # Step 2: Configure based on provider
    console.print()
    if use_local:
        console.print("[bold]步驟 2/3: 設定本地 LLM[/bold]")
        console.print()

        # Local LLM URL
        default_url = settings.local_llm_base_url
        llm_url = Prompt.ask(
            "本地 LLM URL (OpenAI 相容端點)",
            default=default_url
        )

        # Local LLM model
        default_model = settings.local_llm_model
        console.print()
        console.print("[dim]範例: qwen2.5:7b, llama3.1:8b, mistral:7b[/dim]")
        llm_model = Prompt.ask(
            "本地 LLM 模型名稱",
            default=default_model
        )

        # Local LLM API key (optional)
        default_key = settings.local_llm_api_key or "ollama"
        console.print()
        console.print("[dim]本地 LLM 通常不需要實際的 API 金鑰，可使用任意字串[/dim]")
        llm_api_key = Prompt.ask(
            "本地 LLM API Key",
            default=default_key
        )

    else:
        console.print("[bold]步驟 2/3: 設定 OpenAI[/bold]")
        console.print()

        # OpenAI API key
        current_key = settings.openai_api_key
        if current_key:
            console.print(f"[dim]目前 API Key: {current_key[:10]}...{current_key[-4:]}[/dim]")
            console.print()
            update_key = Confirm.ask("是否更新 API Key?", default=False)
            if update_key:
                llm_api_key = Prompt.ask("OpenAI API Key", password=True)
            else:
                llm_api_key = current_key
        else:
            llm_api_key = Prompt.ask("OpenAI API Key", password=True)

        # Fetch available OpenAI models
        console.print()
        console.print("[cyan]正在取得可用模型列表...[/cyan]")
        available_models = get_available_openai_models(llm_api_key)

        # OpenAI model
        console.print()
        console.print("[bold]可用的 OpenAI 模型:[/bold]")
        for idx, model in enumerate(available_models, 1):
            current = " [green](目前)[/green]" if model == settings.openai_model else ""
            console.print(f"  {idx}. {model}{current}")
        console.print()

        model_choice = Prompt.ask(
            "請選擇模型",
            choices=[str(i) for i in range(1, len(available_models) + 1)],
            default="2"  # gpt-4o-mini usually at index 2
        )
        llm_model = available_models[int(model_choice) - 1]

        # Dummy values for local LLM (not used)
        llm_url = settings.local_llm_base_url

    # Step 3: Embedding model
    console.print()
    console.print("[bold]步驟 3/3: 設定嵌入模型[/bold]")
    console.print()

    if use_local:
        console.print("[yellow]注意: 本地 LLM 目前僅支援 OpenAI 嵌入模型[/yellow]")
        console.print("[dim]未來版本將支援本地嵌入模型[/dim]")
        console.print()

    # Fetch available embedding models (use existing API key)
    embedding_api_key = llm_api_key if not use_local else settings.openai_api_key
    console.print("[cyan]正在取得可用嵌入模型列表...[/cyan]")
    available_embeddings = get_available_embedding_models(embedding_api_key)

    console.print()
    console.print("[bold]可用的嵌入模型:[/bold]")
    for idx, model in enumerate(available_embeddings, 1):
        current = " [green](目前)[/green]" if model == settings.openai_embedding_model else ""
        console.print(f"  {idx}. {model}{current}")
    console.print()

    embedding_choice = Prompt.ask(
        "請選擇嵌入模型",
        choices=[str(i) for i in range(1, len(available_embeddings) + 1)],
        default="1"  # text-embedding-3-small usually at index 1
    )
    embedding_model = available_embeddings[int(embedding_choice) - 1]

    # Summary
    console.print()
    console.print(Panel("[bold]設定摘要[/bold]", border_style="cyan"))
    console.print()

    if use_local:
        console.print(f"LLM 提供者: [yellow]本地 LLM[/yellow]")
        console.print(f"本地 LLM URL: [cyan]{llm_url}[/cyan]")
        console.print(f"本地 LLM 模型: [cyan]{llm_model}[/cyan]")
        console.print(f"本地 LLM API Key: [cyan]***[/cyan]")
    else:
        console.print(f"LLM 提供者: [green]OpenAI[/green]")
        console.print(f"OpenAI 模型: [cyan]{llm_model}[/cyan]")
        console.print(f"OpenAI API Key: [cyan]***[/cyan]")

    console.print(f"嵌入模型: [cyan]{embedding_model}[/cyan]")
    console.print()

    # Confirm
    confirm = Confirm.ask("確認儲存設定?", default=True)

    if not confirm:
        console.print("[yellow]設定已取消。[/yellow]")
        return

    # Save to .env file
    save_to_env(
        use_local=use_local,
        llm_url=llm_url if use_local else None,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        embedding_model=embedding_model
    )

    console.print()
    console.print("[green]✓ 設定已儲存到 .env 檔案[/green]")

    # Reload configuration
    console.print("[cyan]正在重新載入設定...[/cyan]")
    reload_settings()

    # Reset orchestrator to use new config
    from finagent.cli.commands.query import reset_orchestrator
    reset_orchestrator()

    console.print("[green]✓ 設定已套用，無需重新啟動 CLI[/green]")
    console.print()

    # Show new config
    console.print("[bold]新的設定：[/bold]")
    show_config()


def save_to_env(
    use_local: bool,
    llm_url: Optional[str],
    llm_model: str,
    llm_api_key: str,
    embedding_model: str
):
    """Save LLM configuration to .env file."""
    # Find .env file
    env_path = Path.cwd() / ".env"

    # Read existing .env content
    existing_config = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    existing_config[key.strip()] = value.strip()

    # Update configuration
    if use_local:
        existing_config["USE_LOCAL_LLM"] = "true"
        existing_config["LOCAL_LLM_BASE_URL"] = llm_url
        existing_config["LOCAL_LLM_MODEL"] = llm_model
        existing_config["LOCAL_LLM_API_KEY"] = llm_api_key
    else:
        existing_config["USE_LOCAL_LLM"] = "false"
        existing_config["OPENAI_MODEL"] = llm_model
        existing_config["OPENAI_API_KEY"] = llm_api_key

    existing_config["OPENAI_EMBEDDING_MODEL"] = embedding_model

    # Write back to .env
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# FinAgent Configuration\n")
        f.write("# Auto-generated by /config command\n\n")

        # Group by category
        f.write("# LLM Configuration\n")
        llm_keys = ["USE_LOCAL_LLM", "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_EMBEDDING_MODEL",
                    "LOCAL_LLM_BASE_URL", "LOCAL_LLM_MODEL", "LOCAL_LLM_API_KEY"]
        for key in llm_keys:
            if key in existing_config:
                f.write(f"{key}={existing_config[key]}\n")

        # Write remaining config
        f.write("\n# Other Configuration\n")
        for key, value in existing_config.items():
            if key not in llm_keys:
                f.write(f"{key}={value}\n")


def reload_config():
    """Reload configuration from .env and model_config.yml."""
    console.print()
    console.print("[cyan]正在重新載入設定...[/cyan]")

    try:
        # Reload .env settings
        reload_settings()
        console.print("[green]✓ 已重新載入 .env 設定[/green]")

        # Reload model_config.yml
        reload_model_config()
        console.print("[green]✓ 已重新載入 model_config.yml[/green]")

        # Reset orchestrator to use new config
        try:
            from finagent.cli.commands.query import reset_orchestrator
            reset_orchestrator()
            console.print("[green]✓ 已重置查詢引擎[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  無法重置查詢引擎: {e}[/yellow]")

        console.print()
        console.print("[bold green]✅ 設定已重新載入！無需重啟 CLI[/bold green]")
        console.print()

        # Show new config
        show_config()

    except FileNotFoundError as e:
        console.print(f"[red]✗ 找不到設定檔: {e}[/red]")
    except Exception as e:
        console.print(f"[red]✗ 重新載入失敗: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def handle_config_command(args: str):
    """
    Handle /config command.

    Args:
        args: Command arguments
          - "llm": Configure LLM settings interactively
          - "reload": Reload configuration from files
          - empty: Show current configuration
    """
    args = args.strip().lower()

    if args == "llm":
        configure_llm()
    elif args == "reload":
        reload_config()
    else:
        show_config()
