"""Configuration command handlers."""

import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from finagent.config import settings

console = Console()


# OpenAI model choices
OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
]

OPENAI_EMBEDDING_MODELS = [
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
]


def show_config():
    """Display current LLM configuration."""
    table = Table(title="LLM 設定", show_header=True, header_style="bold cyan")
    table.add_column("設定項目", style="white", width=25)
    table.add_column("目前值", style="cyan")

    # LLM provider
    if settings.use_local_llm:
        table.add_row("LLM 提供者", "[yellow]本地 LLM[/yellow]")
        table.add_row("本地 LLM URL", settings.local_llm_base_url)
        table.add_row("本地 LLM 模型", settings.local_llm_model)
        table.add_row("本地 LLM API Key", "***" if settings.local_llm_api_key else "[red]未設定[/red]")
    else:
        table.add_row("LLM 提供者", "[green]OpenAI[/green]")
        table.add_row("OpenAI 模型", settings.openai_model)
        table.add_row("OpenAI API Key", "***" if settings.openai_api_key else "[red]未設定[/red]")

    table.add_row("嵌入模型", settings.openai_embedding_model)
    table.add_row("溫度 (Temperature)", str(settings.openai_temperature))

    console.print()
    console.print(table)
    console.print()

    # Show hints
    console.print("[dim]提示: 使用 [cyan]/config llm[/cyan] 修改 LLM 設定[/dim]")
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

        # OpenAI model
        console.print()
        console.print("[bold]可用的 OpenAI 模型:[/bold]")
        for idx, model in enumerate(OPENAI_MODELS, 1):
            current = " [green](目前)[/green]" if model == settings.openai_model else ""
            console.print(f"  {idx}. {model}{current}")
        console.print()

        model_choice = Prompt.ask(
            "請選擇模型",
            choices=[str(i) for i in range(1, len(OPENAI_MODELS) + 1)],
            default="2"  # gpt-4o-mini
        )
        llm_model = OPENAI_MODELS[int(model_choice) - 1]

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

    console.print("[bold]可用的嵌入模型:[/bold]")
    for idx, model in enumerate(OPENAI_EMBEDDING_MODELS, 1):
        current = " [green](目前)[/green]" if model == settings.openai_embedding_model else ""
        console.print(f"  {idx}. {model}{current}")
    console.print()

    embedding_choice = Prompt.ask(
        "請選擇嵌入模型",
        choices=[str(i) for i in range(1, len(OPENAI_EMBEDDING_MODELS) + 1)],
        default="1"  # text-embedding-3-small
    )
    embedding_model = OPENAI_EMBEDDING_MODELS[int(embedding_choice) - 1]

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
    console.print()
    console.print("[yellow]⚠ 請重新啟動 CLI 以套用新設定[/yellow]")
    console.print()


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


def handle_config_command(args: str):
    """
    Handle /config command.

    Args:
        args: Command arguments ("llm" to configure, empty to show)
    """
    args = args.strip().lower()

    if args == "llm":
        configure_llm()
    else:
        show_config()
