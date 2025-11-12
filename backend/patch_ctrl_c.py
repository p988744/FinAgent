"""Patch reindex to make Ctrl+C cancel entire operation."""

# Read file
with open("src/finagent/cli/commands/reindex.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the KeyboardInterrupt handling
old_interrupt = '''                        except KeyboardInterrupt:
                            # User pressed ESC - skip this document
                            failed_count += 1
                            progress.update(
                                init_task,
                                advance=1,
                                description=f"[yellow]⏭️  已跳過: {filename[:40]}..."
                            )
                            continue'''

new_interrupt = '''                        except KeyboardInterrupt:
                            # User pressed Ctrl+C - cancel entire operation
                            console.print()
                            console.print("[yellow]⏸️  操作已中斷[/yellow]")
                            raise  # Re-raise to cancel entire operation'''

if old_interrupt in content:
    content = content.replace(old_interrupt, new_interrupt)
    print("✓ Patched KeyboardInterrupt handling")
else:
    print("✗ Could not find exact match")
    exit(1)

# Also update the hint message
old_hint = '''                console.print(f"[yellow]提示: 按 ESC 鍵取消當前文件的初始化[/yellow]\\n")'''
new_hint = '''                console.print(f"[yellow]提示: 按 Ctrl+C 取消整個操作[/yellow]\\n")'''

if old_hint in content:
    content = content.replace(old_hint, new_hint)
    print("✓ Updated hint message")

# Write back
with open("src/finagent/cli/commands/reindex.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✓ File updated successfully")
