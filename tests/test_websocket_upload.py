#!/usr/bin/env python3
"""
Test WebSocket upload endpoint with progress monitoring.

Usage:
    uv run python tests/test_websocket_upload.py
"""

import asyncio
import base64
import json
import websockets


async def test_websocket_upload():
    """Test uploading a document via WebSocket with progress tracking."""

    # Create test document content
    test_content = """測試文件：台新銀行洗錢防制缺失

金管會於2024年對台新銀行進行洗錢防制檢查，發現以下缺失：
1. 客戶資料審查不確實
2. 疑似洗錢交易通報延遲
3. 內部控制制度執行不力

裁罰金額：新台幣500萬元
裁罰日期：2024年11月18日
"""

    # Encode content to base64
    content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')

    uri = "ws://localhost:8000/api/v1/ws/upload"

    print("🔌 Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        print("✅ Connected!")

        # Send upload request
        upload_request = {
            "type": "upload_start",
            "filename": "test_websocket_upload.txt",
            "content": content_b64,
            "auto_index": True,
            "extract_metadata": False,
        }

        print(f"\n📤 Sending upload request for: {upload_request['filename']}")
        await websocket.send(json.dumps(upload_request))

        # Receive progress updates
        print("\n📊 Progress updates:")
        print("-" * 60)

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                msg_type = data.get("type")
                payload = data.get("payload", {})

                if msg_type == "progress":
                    stage = payload.get("stage", "unknown")
                    message_text = payload.get("message", "")
                    progress = payload.get("progress", 0)

                    # Progress bar
                    bar_length = 30
                    filled = int(bar_length * progress / 100)
                    bar = "█" * filled + "░" * (bar_length - filled)

                    print(f"[{bar}] {progress:3d}% | {stage:15s} | {message_text}")

                elif msg_type == "upload_complete":
                    document = payload.get("document", {})
                    message_text = payload.get("message", "")

                    print("-" * 60)
                    print(f"\n✅ {message_text}")
                    print(f"\n📄 Document Details:")
                    print(f"   ID: {document.get('id')}")
                    print(f"   Name: {document.get('name')}")
                    print(f"   Status: {document.get('status')}")
                    print(f"   Chunks: {document.get('chunk_count')}")
                    print(f"   Indexed: {document.get('indexed')}")

                    break

                elif msg_type == "error":
                    error_message = payload.get("message", "Unknown error")
                    print(f"\n❌ Error: {error_message}")
                    break

            except websockets.exceptions.ConnectionClosed:
                print("\n⚠️  Connection closed")
                break

    print("\n🏁 Test complete!")


if __name__ == "__main__":
    asyncio.run(test_websocket_upload())
