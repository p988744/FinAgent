"""WebSocket client to test dynamic planning display in frontend."""

import asyncio
import json
import websockets


async def test_dynamic_planning_client():
    """
    Test client that demonstrates dynamic planning by sending mock data.

    This simulates what the backend would send during query processing.
    """
    uri = "ws://localhost:8000/ws/query"

    print("Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        print("Connected!")

        # Test query
        query = "玉山銀行與國泰世華銀行的裁罰紀錄比較"
        print(f"\n📤 Sending query: {query}")

        await websocket.send(json.dumps({
            "type": "query",
            "text": query
        }))

        # Listen for responses
        print("\n📥 Receiving responses:")
        print("=" * 80)

        async for message in websocket:
            data = json.loads(message)
            msg_type = data["type"]

            print(f"\n[{msg_type}]")

            if msg_type == "dynamic_plan_analysis":
                print(json.dumps(data["payload"], indent=2, ensure_ascii=False))
            elif msg_type == "activity_log":
                level = data["payload"]["level"]
                msg = data["payload"]["message"]
                print(f"  [{level.upper()}] {msg}")
            elif msg_type == "step_update":
                step = data["payload"]["step"]
                status = data["payload"]["status"]
                desc = data["payload"]["description"]
                print(f"  Step: {step} | Status: {status} | {desc}")
            elif msg_type == "query_complete":
                print("  ✅ Query complete!")
                break
            elif msg_type == "query_failed":
                print(f"  ❌ Query failed: {data['payload']['error']}")
                break


if __name__ == "__main__":
    try:
        asyncio.run(test_dynamic_planning_client())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
