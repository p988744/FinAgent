import asyncio
import json
import websockets
import sys

async def test_websocket():
    uri = "ws://localhost:8000/ws/query"
    query = "玉山銀行洗錢防制裁罰案件"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri, origin="http://localhost:3000") as websocket:
            print("Connected!")
            
            # Send query
            payload = {
                "type": "query",
                "text": query,
                "model": "gpt-4o",
                "search_strategy": "comprehensive"
            }
            print(f"Sending query: {json.dumps(payload, ensure_ascii=False)}")
            await websocket.send(json.dumps(payload))
            
            # Receive messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    data = json.loads(message)
                    msg_type = data.get("type")
                    print(f"Received: {msg_type}")
                    
                    if msg_type == "error":
                        print(f"Error: {data.get('payload')}")
                        break
                    elif msg_type == "query_complete":
                        print("Query complete!")
                        print(json.dumps(data.get("payload"), indent=2, ensure_ascii=False))
                        break
                    elif msg_type == "query_failed":
                        print(f"Query failed: {data.get('payload')}")
                        break
                    elif msg_type == "step_update":
                        payload = data.get("payload", {})
                        print(f"Step: {payload.get('step')} - {payload.get('status')} - {payload.get('description')}")
                    elif msg_type == "plan_created":
                        print("Plan created!")
                        print(json.dumps(data.get("payload"), indent=2, ensure_ascii=False))
                    
                except asyncio.TimeoutError:
                    print("Timeout waiting for message")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
                    
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
