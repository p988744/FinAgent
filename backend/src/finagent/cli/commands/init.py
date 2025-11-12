"""Initialize document metadata command."""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from finagent.document_processing.loader import DocumentLoader
from finagent.document_processing.metadata_store import (
    DocumentMetadataStore,
    DocumentMetadata,
)
from finagent.document_processing.toc_generator import TableOfContents

console = Console()


# Common document types for quick selection
DOCUMENT_TYPES = [
    "裁罰書",
    "判決書",
    "法規條文",
    "新聞報導",
    "監管公告",
    "銀行聲明",
    "分析報告",
    "其他",
]

# Common authorities
AUTHORITIES = [
    "金管會",
    "中央銀行",
    "公平會",
    "最高法院",
    "高等法院",
    "地方法院",
    "其他",
]

# Common violation types
VIOLATION_TYPES = [
    "洗錢防制",
    "內線交易",
    "資訊揭露",
    "法規遵循",
    "作業風險",
    "信用風險",
    "市場操縱",
    "消費者保護",
    "其他",
]


def show_document_list():
    """Show list of all documents with metadata."""
    console.print()
    console.print(Panel("[bold cyan]文件清單[/bold cyan]", border_style="cyan"))
    console.print()

    # Load documents and metadata
    base_dir = Path.cwd()
    docs_path = base_dir / "data" / "documents"
    loader = DocumentLoader(base_path=str(docs_path))
    metadata_store = DocumentMetadataStore()

    try:
        # Get all TXT files
        documents = loader.load_directory(".", pattern="*.txt", recursive=True)

        if not documents:
            console.print("[yellow]未找到任何文件[/yellow]")
            console.print(f"[dim]請將文件放置在: {docs_path}[/dim]")
            console.print()
            return

        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("檔名", style="white", width=40)
        table.add_column("描述", style="cyan", width=50)
        table.add_column("類型", style="green")
        table.add_column("狀態", style="yellow")

        for doc in documents:
            filename = doc.metadata.get("filename", "unknown")
            metadata = metadata_store.get_metadata(doc.id)

            if metadata:
                description = metadata.description[:47] + "..." if len(metadata.description) > 50 else metadata.description
                doc_type = metadata.document_type
                status = "[green]✓ 已初始化[/green]"
            else:
                description = "[dim]尚未設定[/dim]"
                doc_type = "[dim]-[/dim]"
                status = "[yellow]待初始化[/yellow]"

            table.add_row(filename, description, doc_type, status)

        console.print(table)
        console.print()

        # Show statistics
        stats = metadata_store.get_statistics()
        console.print(f"[dim]總文件數: {len(documents)} | 已初始化: {stats['total_documents']}[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]錯誤: {str(e)}[/red]")
        console.print()


def init_document_interactive(filename: Optional[str] = None):
    """
    Initialize document metadata interactively.

    Args:
        filename: Optional filename to initialize (if None, prompts user to select)
    """
    console.print()
    console.print(Panel("[bold cyan]文件初始化精靈[/bold cyan]", border_style="cyan"))
    console.print()

    # Setup paths
    base_dir = Path.cwd()
    docs_path = base_dir / "data" / "documents"
    loader = DocumentLoader(base_path=str(docs_path))
    metadata_store = DocumentMetadataStore()

    try:
        # Step 1: Select document
        if filename:
            # Try to load specified file
            try:
                doc = loader.load_txt(filename)
            except FileNotFoundError:
                console.print(f"[red]錯誤: 找不到文件 '{filename}'[/red]")
                console.print(f"[dim]請確認文件位於: {docs_path}[/dim]")
                console.print()
                return
        else:
            # List available documents
            documents = loader.load_directory(".", pattern="*.txt", recursive=True)

            if not documents:
                console.print("[yellow]未找到任何文件[/yellow]")
                console.print(f"[dim]請將文件放置在: {docs_path}[/dim]")
                console.print()
                return

            console.print("[bold]可用的文件:[/bold]")
            for idx, doc in enumerate(documents, 1):
                filename_display = doc.metadata.get("filename", "unknown")
                metadata = metadata_store.get_metadata(doc.id)
                status = "✓" if metadata else " "
                console.print(f"  {idx}. [{status}] {filename_display}")
            console.print()

            # Prompt for selection
            choice = Prompt.ask(
                "請選擇要初始化的文件",
                choices=[str(i) for i in range(1, len(documents) + 1)],
            )
            doc = documents[int(choice) - 1]

        filename_display = doc.metadata.get("filename", "unknown")

        # Check if already has metadata
        existing_metadata = metadata_store.get_metadata(doc.id)
        if existing_metadata:
            console.print(f"\n[yellow]文件 '{filename_display}' 已有初始化資料[/yellow]")
            console.print(f"描述: {existing_metadata.description}")
            console.print()

            update = Confirm.ask("是否要更新？", default=False)
            if not update:
                console.print("[cyan]已取消[/cyan]\n")
                return

        # Step 2: Document description
        console.print(f"\n[bold]步驟 1/6: 文件描述[/bold]")
        console.print("[dim]請用 1-2 句話描述此文件的內容（這將幫助系統更準確地檢索）[/dim]")
        description = Prompt.ask("文件描述")

        # Step 3: Document type
        console.print(f"\n[bold]步驟 2/6: 文件類型[/bold]")
        for idx, doc_type in enumerate(DOCUMENT_TYPES, 1):
            console.print(f"  {idx}. {doc_type}")
        console.print()

        type_choice = Prompt.ask(
            "請選擇文件類型",
            choices=[str(i) for i in range(1, len(DOCUMENT_TYPES) + 1)],
            default="1",
        )
        document_type = DOCUMENT_TYPES[int(type_choice) - 1]

        if document_type == "其他":
            document_type = Prompt.ask("請輸入文件類型")

        # Step 4: Keywords
        console.print(f"\n[bold]步驟 3/6: 關鍵字[/bold]")
        console.print("[dim]輸入關鍵字（用逗號分隔，例如：玉山銀行,洗錢防制,裁罰）[/dim]")
        keywords_input = Prompt.ask("關鍵字")
        keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]

        # Step 5: Optional fields (date, authority, institutions)
        console.print(f"\n[bold]步驟 4/6: 日期與機關[/bold]")

        # Document date
        date_str = Prompt.ask(
            "文件日期 (格式: YYYY-MM-DD，留空跳過)",
            default="",
        )
        date = date_str if date_str else None

        # Issuing authority
        console.print("\n[dim]發布機關:[/dim]")
        for idx, authority in enumerate(AUTHORITIES, 1):
            console.print(f"  {idx}. {authority}")
        console.print()

        authority_choice = Prompt.ask(
            "請選擇發布機關（留空跳過）",
            choices=[str(i) for i in range(1, len(AUTHORITIES) + 1)] + [""],
            default="",
        )

        if authority_choice:
            issuing_authority = AUTHORITIES[int(authority_choice) - 1]
            if issuing_authority == "其他":
                issuing_authority = Prompt.ask("請輸入發布機關")
        else:
            issuing_authority = None

        # Related institutions
        console.print(f"\n[bold]步驟 5/6: 相關機構[/bold]")
        console.print("[dim]輸入相關銀行或機構（用逗號分隔，例如：玉山銀行,國泰世華銀行）[/dim]")
        institutions_input = Prompt.ask("相關機構（留空跳過）", default="")
        related_institutions = [
            inst.strip() for inst in institutions_input.split(",") if inst.strip()
        ]

        # Step 6: Penalty-specific fields
        penalty_amount = None
        violation_types_list: List[str] = []

        if document_type == "裁罰書":
            console.print(f"\n[bold]步驟 6/6: 裁罰資訊[/bold]")

            # Penalty amount
            penalty_amount = Prompt.ask(
                "裁罰金額（例如：2.5億元，留空跳過）",
                default="",
            )
            penalty_amount = penalty_amount if penalty_amount else None

            # Violation types
            console.print("\n[dim]違規類型（可複選，用逗號分隔選項編號）:[/dim]")
            for idx, violation in enumerate(VIOLATION_TYPES, 1):
                console.print(f"  {idx}. {violation}")
            console.print()

            violations_choice = Prompt.ask(
                "請選擇違規類型（例如：1,2，留空跳過）",
                default="",
            )

            if violations_choice:
                violation_indices = [
                    int(idx.strip()) - 1
                    for idx in violations_choice.split(",")
                    if idx.strip().isdigit()
                ]
                violation_types_list = [
                    VIOLATION_TYPES[idx]
                    for idx in violation_indices
                    if idx < len(VIOLATION_TYPES)
                ]

                # Handle "其他"
                if "其他" in violation_types_list:
                    other_violation = Prompt.ask("請輸入其他違規類型")
                    violation_types_list = [
                        v for v in violation_types_list if v != "其他"
                    ]
                    violation_types_list.append(other_violation)
        else:
            console.print(f"\n[bold]步驟 6/6: 完成[/bold]")

        # Create metadata
        now = datetime.now().isoformat()
        metadata = DocumentMetadata(
            doc_id=doc.id,
            filename=filename_display,
            description=description,
            document_type=document_type,
            keywords=keywords,
            date=date,
            issuing_authority=issuing_authority,
            related_institutions=related_institutions,
            penalty_amount=penalty_amount,
            violation_types=violation_types_list,
            created_at=now,
            updated_at=now,
        )

        # Save metadata
        metadata_store.add_metadata(metadata)

        # Show summary
        console.print()
        console.print(Panel("[bold green]✓ 文件初始化完成[/bold green]", border_style="green"))
        console.print()
        console.print(f"[bold]文件:[/bold] {filename_display}")
        console.print(f"[bold]描述:[/bold] {description}")
        console.print(f"[bold]類型:[/bold] {document_type}")
        console.print(f"[bold]關鍵字:[/bold] {', '.join(keywords)}")

        if date:
            console.print(f"[bold]日期:[/bold] {date}")
        if issuing_authority:
            console.print(f"[bold]發布機關:[/bold] {issuing_authority}")
        if related_institutions:
            console.print(f"[bold]相關機構:[/bold] {', '.join(related_institutions)}")
        if penalty_amount:
            console.print(f"[bold]裁罰金額:[/bold] {penalty_amount}")
        if violation_types_list:
            console.print(f"[bold]違規類型:[/bold] {', '.join(violation_types_list)}")

        console.print()
        console.print("[dim]提示: 這些資訊將在文件索引時加入，幫助提升檢索準確度[/dim]")
        console.print()

        # Update table of contents
        try:
            console.print("[cyan]📖 更新文件目錄...[/cyan]")
            toc = TableOfContents()
            toc_path = toc.save()
            console.print(f"[green]✅ 文件目錄已更新: {toc_path.name}[/green]")
            console.print()
        except Exception as e:
            console.print(f"[yellow]⚠️  目錄更新失敗: {str(e)}[/yellow]")
            console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]已取消[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]錯誤: {str(e)}[/red]\n")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def handle_init_command(args: str):
    """
    Handle /init command.

    Args:
        args: Command arguments
            - Empty: Show document list
            - Filename: Initialize specific document
            - "list": Show document list
    """
    args = args.strip()

    if not args or args == "list":
        show_document_list()
    else:
        init_document_interactive(filename=args)
