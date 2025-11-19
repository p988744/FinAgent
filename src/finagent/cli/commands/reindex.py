"""
Reindex command for rebuilding the vector database.
"""

import asyncio
import sys
from datetime import datetime
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
from finagent.document_processing.concept_extractor import (
    analyze_toc_for_concepts,
    extract_document_concepts,
    infer_concept_type,
)
from finagent.document_processing.metadata_store import (
    DocumentMetadata,
    DocumentMetadataStore,
)
from finagent.document_processing.toc_generator import TableOfContents
from finagent.database.db import Database
from finagent.database.models import Concept

console = Console()


async def reindex_documents_sequential(
    clear_existing: bool = False,
    skip_metadata: bool = False,
    skip_concepts: bool = False,
) -> tuple[int, int]:
    """
    Reindex documents sequentially with per-document processing.

    Each document goes through ALL steps before moving to next:
    1. Load file
    2. Index to vector DB
    3. Generate metadata (LLM or minimal)
    4. Save to database
    5. Update TABLE_OF_CONTENTS.md
    6. Link concepts

    Args:
        clear_existing: Clear all indexes before starting
        skip_metadata: Skip LLM metadata generation (use minimal metadata)
        skip_concepts: Skip concept analysis at end

    Returns:
        Tuple of (total_indexed, total_chunks)
    """
    try:
        # Get absolute paths
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        docs_path = base_dir / "data" / "documents"
        vector_db_path = base_dir / "data" / "vector_db"

        # Initialize components
        loader = DocumentLoader(base_path=str(docs_path))
        indexer = DocumentIndexer(
            collection_name="legal_documents", persist_directory=str(vector_db_path)
        )
        metadata_store = DocumentMetadataStore()
        toc = TableOfContents()
        db = Database()

        # Clear if requested
        if clear_existing:
            console.print("[yellow]🗑️  清空現有索引和元資料...[/yellow]")
            indexer.clear_collection()
            metadata_store.clear_all()
            console.print("[green]✅ 索引和元資料已清空[/green]\n")

        # Load documents
        console.print("[cyan]📄 載入文件...[/cyan]")
        documents = loader.load_directory(".", pattern="*.txt", recursive=True)

        if not documents:
            console.print("[yellow]⚠️  未找到任何文件[/yellow]")
            return 0, 0

        console.print(f"[green]✅ 找到 {len(documents)} 個文件[/green]\n")

        # Initialize metadata generator if needed
        metadata_generator = None
        if not skip_metadata:
            from finagent.document_processing.metadata_generator import MetadataGenerator

            metadata_generator = MetadataGenerator()
            console.print(
                "[cyan]🤖 將使用 LLM 生成文件元資料[/cyan]"
            )
        else:
            console.print("[yellow]⏭️  跳過 LLM 元資料生成（使用基本元資料）[/yellow]")

        console.print()

        # Sequential per-document processing
        total_indexed = 0
        total_chunks = 0
        skipped = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]處理文件...", total=len(documents))

            for i, doc in enumerate(documents, 1):
                filename = doc.metadata.get("filename", "unknown")

                try:
                    # Step 1: Check if already processed
                    progress.update(task, description=f"[cyan]🔍 檢查: {filename[:35]}...")
                    existing_meta = metadata_store.get_metadata(doc.id)

                    if existing_meta and existing_meta.indexed and not clear_existing:
                        skipped += 1
                        progress.update(
                            task,
                            advance=1,
                            description=f"[yellow]⏭️  已索引: {filename[:35]}...",
                        )
                        continue

                    # Step 2: Index to vector DB
                    progress.update(task, description=f"[blue]📊 索引: {filename[:35]}...")
                    chunks = await indexer.index_document(doc)
                    total_chunks += chunks

                    # Step 3: Generate or create metadata
                    if not skip_metadata and metadata_generator:
                        progress.update(
                            task, description=f"[magenta]🤖 分析: {filename[:35]}..."
                        )
                        metadata = metadata_generator.generate_metadata(
                            doc_id=doc.id, filename=filename, content=doc.content
                        )
                    else:
                        # Create minimal metadata
                        metadata = DocumentMetadata(
                            doc_id=doc.id,
                            filename=filename,
                            description=f"Auto-indexed document: {filename}",
                            document_type="未分類",
                            keywords=[],
                            indexed=False,  # Will be set to True below
                            chunk_count=0,  # Will be set below
                            created_at=datetime.now().isoformat(),
                            updated_at=datetime.now().isoformat(),
                        )

                    # Step 4: Save metadata to database
                    progress.update(task, description=f"[green]💾 儲存: {filename[:35]}...")
                    file_path = doc.metadata.get("file_path") or doc.source or ""
                    metadata.indexed = True
                    metadata.chunk_count = chunks
                    metadata_store.add_metadata(metadata, file_path=file_path)

                    # Step 5: Update TABLE_OF_CONTENTS.md periodically (every 50 docs)
                    # Note: TOC regenerates entire index from metadata_store
                    if total_indexed % 50 == 0 or i == len(documents):
                        progress.update(task, description=f"[cyan]📝 TOC: {filename[:35]}...")
                        toc.save()

                    # Step 6: Link document concepts
                    progress.update(task, description=f"[yellow]🔗 概念: {filename[:35]}...")
                    doc_concepts = extract_document_concepts(metadata)

                    for concept_name in doc_concepts:
                        # Get or create concept
                        concept = db.get_concept_by_name(concept_name)
                        if not concept:
                            concept = Concept(
                                concept_name=concept_name,
                                concept_type=infer_concept_type(concept_name, metadata),
                                description=f"從文件元資料提取的概念",
                                keywords=[],
                            )
                            concept = db.add_concept(concept)

                        # Link to document
                        db.link_document_concept(doc.id, concept.id, relevance_score=1.0)

                    total_indexed += 1
                    status_icon = "📋" if not skip_metadata else "📄"
                    progress.update(
                        task,
                        advance=1,
                        description=f"[green]{status_icon} 完成: {filename[:35]}... ({chunks} chunks)",
                    )

                except KeyboardInterrupt:
                    console.print("\n[yellow]⏸️  使用者中斷處理[/yellow]")
                    raise
                except Exception as e:
                    progress.update(
                        task, advance=1, description=f"[red]❌ 錯誤: {filename[:35]}..."
                    )
                    console.print(f"\n[red]處理 {filename} 時發生錯誤: {str(e)}[/red]")
                    # Continue with next document

        # Final TOC update
        if total_indexed > 0:
            console.print("[cyan]📖 最終更新文件目錄...[/cyan]")
            toc.save()

        # Print summary
        console.print()
        console.print("[bold cyan]📊 索引摘要[/bold cyan]")
        console.print(f"  ✅ 已索引: {total_indexed} 份文件")
        console.print(f"  ⏭️  已跳過: {skipped} 份文件")
        console.print(f"  📦 總區塊: {total_chunks} 個")
        console.print()

        # Step 7-9: Global concept analysis (if not skipped)
        if not skip_concepts and total_indexed > 0:
            console.print("[bold cyan]🧠 全域概念分析[/bold cyan]")
            console.print("[dim]分析 TABLE_OF_CONTENTS.md 提取關鍵概念...[/dim]\n")

            try:
                toc_path = base_dir / "data" / "TABLE_OF_CONTENTS.md"
                global_concepts = analyze_toc_for_concepts(
                    toc_path, llm_generator=metadata_generator, max_concepts=50
                )

                if global_concepts:
                    console.print(f"[green]✅ 發現 {len(global_concepts)} 個全域概念[/green]")

                    # Save concepts to database
                    for concept_data in global_concepts:
                        concept = db.get_concept_by_name(concept_data["concept_name"])
                        if not concept:
                            # Create new concept
                            concept = Concept(
                                concept_name=concept_data["concept_name"],
                                concept_type=concept_data.get("concept_type", "topic"),
                                description=concept_data.get("description", ""),
                                keywords=concept_data.get("keywords", []),
                            )
                            db.add_concept(concept)
                        else:
                            # Update existing concept with LLM-generated description
                            if concept_data.get("description"):
                                concept.description = concept_data["description"]
                            if concept_data.get("keywords"):
                                concept.keywords = concept_data["keywords"]
                            db.add_concept(concept)  # Update via UPSERT

                    # Show top concepts
                    top_concepts = db.get_top_concepts(10)
                    console.print("\n[bold]前 10 大概念：[/bold]")
                    for concept in top_concepts:
                        console.print(
                            f"  • {concept.concept_name} "
                            f"[dim]({concept.document_count} 份文件)[/dim]"
                        )
                else:
                    console.print("[yellow]⚠️  未能提取全域概念[/yellow]")

            except Exception as e:
                console.print(f"[red]概念分析失敗: {str(e)}[/red]")
                console.print("[yellow]跳過概念分析，文件索引已完成[/yellow]")

        console.print()

        return total_indexed, total_chunks

    except KeyboardInterrupt:
        console.print("\n[yellow]⏸️  索引已中斷[/yellow]\n")
        raise
    except Exception as e:
        console.print(f"\n[red]❌ 索引失敗: {str(e)}[/red]\n")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise


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

                            # Save metadata (get file_path from doc.metadata or doc.source)
                            file_path = doc.metadata.get("file_path") or doc.source
                            metadata_store.add_metadata(metadata, file_path=file_path)
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

                # Load enhanced metadata if available (need it for indexed status check)
                enhanced_metadata = metadata_store.get_metadata(doc.id)

                # Check if already indexed (check database metadata first, then vector DB)
                if not clear_existing:
                    # Priority 1: Check database metadata (faster)
                    if enhanced_metadata and enhanced_metadata.indexed:
                        skipped += 1
                        progress.update(
                            task, advance=1, description=f"[yellow]⏭️  已索引: {filename[:40]}..."
                        )
                        continue
                    # Priority 2: Check vector DB (slower, for backwards compatibility)
                    elif indexer.document_exists(doc.id):
                        skipped += 1
                        # Update or create database record for future runs
                        from finagent.database.db import Database
                        from finagent.document_processing.metadata_store import DocumentMetadata
                        db = Database()
                        chunk_count = len(indexer.get_document_chunks(doc.id))

                        if enhanced_metadata:
                            # Update existing metadata
                            db.update_document_indexed_status(doc.id, indexed=True, chunk_count=chunk_count)
                        else:
                            # Create minimal metadata for backwards compatibility
                            file_path = doc.metadata.get("file_path") or doc.source or ""
                            minimal_metadata = DocumentMetadata(
                                doc_id=doc.id,
                                filename=filename,
                                description=f"Auto-indexed document: {filename}",
                                document_type="未分類",
                                keywords=[],
                                indexed=True,
                                chunk_count=chunk_count,
                                created_at=datetime.now().isoformat(),
                                updated_at=datetime.now().isoformat(),
                            )
                            metadata_store.add_metadata(minimal_metadata, file_path=file_path)

                        progress.update(
                            task, advance=1, description=f"[yellow]⏭️  已索引: {filename[:40]}..."
                        )
                        continue
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

                    # Update or create database record to mark document as indexed
                    from finagent.database.db import Database
                    from finagent.document_processing.metadata_store import DocumentMetadata
                    db = Database()

                    if enhanced_metadata:
                        # Update existing metadata
                        db.update_document_indexed_status(doc.id, indexed=True, chunk_count=chunks)
                    else:
                        # Create minimal metadata for documents without enhanced metadata
                        file_path = doc.metadata.get("file_path") or doc.source or ""
                        minimal_metadata = DocumentMetadata(
                            doc_id=doc.id,
                            filename=filename,
                            description=f"Auto-indexed document: {filename}",
                            document_type="未分類",
                            keywords=[],
                            indexed=True,
                            chunk_count=chunks,
                            created_at=datetime.now().isoformat(),
                            updated_at=datetime.now().isoformat(),
                        )
                        metadata_store.add_metadata(minimal_metadata, file_path=file_path)

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


def execute_reindex(clear: bool = False, skip_init: bool = False, use_sequential: bool = True):
    """
    Execute reindex command from CLI.

    Args:
        clear: Whether to clear existing index first
        skip_init: Whether to skip initialization prompts
        use_sequential: Whether to use sequential processing (default: True)
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
        # Use sequential mode by default (better UX, interruptible)
        if use_sequential:
            indexed, chunks = asyncio.run(reindex_documents_sequential(
                clear_existing=clear,
                skip_metadata=skip_init,
                skip_concepts=False,  # Always do concept analysis
            ))
        else:
            # Legacy batch mode
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
