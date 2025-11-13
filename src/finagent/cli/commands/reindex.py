"""
Reindex command for rebuilding the vector database.
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from finagent.document_processing import (
    DocumentIndexer,
    DocumentLoader,
)
from finagent.document_processing.metadata_store import DocumentMetadataStore
from finagent.document_processing.toc_generator import TableOfContents

console = Console()


def reindex_documents(clear_existing: bool = False, prompt_init: bool = True) -> tuple[int, int]:
    """
    Reindex all documents in the data/documents directory.

    Args:
        clear_existing: Whether to clear the existing collection first
        prompt_init: Whether to prompt for metadata initialization if not present

    Returns:
        Tuple of (total_documents, total_chunks)
    """
    try:
        # Get absolute paths
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        docs_path = base_dir / "data" / "documents"
        vector_db_path = base_dir / "data" / "vector_db"

        # Initialize loader, indexer, and metadata store
        loader = DocumentLoader(base_path=str(docs_path))
        indexer = DocumentIndexer(
            collection_name="legal_documents", persist_directory=str(vector_db_path)
        )
        metadata_store = DocumentMetadataStore()

        # Clear collection and metadata if requested
        if clear_existing:
            console.print("[yellow]🗑️  清空現有索引和元資料...[/yellow]")
            indexer.clear_collection()
            metadata_store.clear_all()
            console.print("[green]✅ 索引和元資料已清空[/green]\n")

        # Load all TXT files (recursively)
        console.print("[cyan]📄 載入文件...[/cyan]")
        documents = loader.load_directory(".", pattern="*.txt", recursive=True)

        if not documents:
            console.print("[yellow]⚠️  未找到任何文件[/yellow]")
            return 0, 0

        console.print(f"[green]✅ 找到 {len(documents)} 個文件[/green]\n")

        # Auto-initialize uninitialized documents with LLM
        if prompt_init:
            uninitialized_docs = []
            for doc in documents:
                if not metadata_store.get_metadata(doc.id):
                    uninitialized_docs.append(doc)

            if uninitialized_docs:
                console.print(f"[cyan]🤖 發現 {len(uninitialized_docs)} 個未初始化的文件[/cyan]")
                console.print("[dim]使用 LLM 自動分析並初始化元資料...[/dim]")
                console.print("[yellow]提示: 按 Ctrl+C 取消整個操作[/yellow]\n")

                from finagent.document_processing.metadata_generator import MetadataGenerator

                # Initialize with progress bar
                initialized_count = 0
                failed_count = 0

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    console=console,
                ) as progress:
                    init_task = progress.add_task(
                        "[cyan]🤖 初始化文件元資料...", total=len(uninitialized_docs)
                    )

                    generator = MetadataGenerator()

                    for doc in uninitialized_docs:
                        filename = doc.metadata.get("filename", "unknown")
                        progress.update(init_task, description=f"[cyan]🤖 分析: {filename[:40]}...")

                        try:
                            # Generate metadata with LLM
                            metadata = generator.generate_metadata(
                                doc_id=doc.id, filename=filename, content=doc.content
                            )

                            # Save metadata
                            metadata_store.add_metadata(metadata)
                            initialized_count += 1

                            progress.update(
                                init_task,
                                advance=1,
                                description=f"[green]✓ 已初始化: {filename[:40]}...",
                            )

                        except KeyboardInterrupt:
                            # User pressed Ctrl+C - cancel entire operation
                            console.print()
                            console.print("[yellow]⏸️  操作已中斷[/yellow]")
                            raise  # Re-raise to cancel entire operation

                        except Exception:
                            # LLM error - skip this document
                            failed_count += 1
                            progress.update(
                                init_task, advance=1, description=f"[red]✗ 失敗: {filename[:40]}..."
                            )
                            continue

                console.print()
                console.print(f"[green]✅ 初始化完成: {initialized_count} 個文件[/green]")
                if failed_count > 0:
                    console.print(f"[yellow]⚠️  跳過: {failed_count} 個文件[/yellow]")
                console.print()

                # Reload metadata store after initializations
                metadata_store = DocumentMetadataStore()

        # Index documents with progress bar
        total_chunks = 0
        skipped = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]🔍 建立索引...", total=len(documents))

            for doc in documents:
                filename = doc.metadata.get("filename", "unknown")

                # Check if already indexed
                if not clear_existing and indexer.document_exists(doc.id):
                    skipped += 1
                    progress.update(
                        task, advance=1, description=f"[yellow]⏭️  跳過: {filename[:40]}..."
                    )
                    continue

                # Load enhanced metadata if available
                enhanced_metadata = metadata_store.get_metadata(doc.id)
                if enhanced_metadata:
                    # Merge enhanced metadata into document metadata
                    doc.metadata.update(
                        {
                            "description": enhanced_metadata.description,
                            "document_type": enhanced_metadata.document_type,
                            "keywords": ", ".join(enhanced_metadata.keywords),
                            "date": enhanced_metadata.date or "",
                            "issuing_authority": enhanced_metadata.issuing_authority or "",
                            "related_institutions": ", ".join(
                                enhanced_metadata.related_institutions
                            ),
                            "penalty_amount": enhanced_metadata.penalty_amount or "",
                            "violation_types": ", ".join(enhanced_metadata.violation_types),
                        }
                    )

                # Index document
                try:
                    chunks = indexer.index_document(doc)
                    total_chunks += chunks

                    # Show if enhanced metadata was used
                    status_icon = "📋" if enhanced_metadata else "📄"
                    progress.update(
                        task,
                        advance=1,
                        description=f"[green]{status_icon} 已索引: {filename[:40]}... ({chunks} chunks)",
                    )
                except Exception as e:
                    progress.update(
                        task, advance=1, description=f"[red]❌ 錯誤: {filename[:40]}..."
                    )
                    console.print(f"[red]  錯誤詳情: {str(e)}[/red]")

        # Update table of contents after indexing
        console.print()
        console.print("[cyan]📖 更新文件目錄...[/cyan]")
        try:
            toc = TableOfContents()
            toc_path = toc.save()
            console.print(f"[green]✅ 文件目錄已更新: {toc_path.name}[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  目錄更新失敗: {str(e)}[/yellow]")

        return len(documents) - skipped, total_chunks

    except Exception as e:
        console.print(f"[red]❌ 索引失敗: {str(e)}[/red]")
        raise


def execute_reindex(clear: bool = False, skip_init: bool = False):
    """
    Execute reindex command from CLI.

    Args:
        clear: Whether to clear existing index first
        skip_init: Whether to skip initialization prompts
    """
    console.print()

    if clear:
        console.print(
            Panel(
                "[bold yellow]⚠️  警告：這將刪除所有現有索引並重新建立！[/bold yellow]\n\n"
                "是否繼續？(輸入 'yes' 確認)",
                title="確認清除索引",
                border_style="yellow",
            )
        )

        try:
            confirmation = console.input("[bold]> [/bold]")
            if confirmation.lower() != "yes":
                console.print("[cyan]已取消操作[/cyan]\n")
                return
        except KeyboardInterrupt:
            console.print("\n[cyan]已取消操作[/cyan]\n")
            return

    console.print("[bold cyan]🚀 開始重新索引文件...[/bold cyan]\n")

    try:
        indexed, chunks = reindex_documents(clear_existing=clear, prompt_init=not skip_init)

        # Show summary
        console.print()
        summary_text = f"""
[bold green]✨ 索引完成！[/bold green]

📊 統計資訊：
  • 索引文件數: {indexed}
  • 總片段數: {chunks}
  • 平均每份文件: {chunks/indexed if indexed > 0 else 0:.1f} 片段

💡 提示：現在可以使用 /query 命令查詢文件
        """

        console.print(Panel(summary_text.strip(), title="索引結果", border_style="green"))
        console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]⏸️  索引已中斷[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]❌ 索引失敗: {str(e)}[/red]\n")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
