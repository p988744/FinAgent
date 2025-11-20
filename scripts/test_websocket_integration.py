import asyncio
import json
import websockets
import sys

async def test_websocket_integration():
    uri = "ws://localhost:8000/ws/query"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send query with use_plan_execute=True
            query = {
                "type": "query",
                "text": "玉山銀行 2020 裁罰",
                "use_plan_execute": True
            }
            print(f"Sending query: {json.dumps(query, ensure_ascii=False)}")
            await websocket.send(json.dumps(query))
            
            # Listen for messages
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    print(f"Received: {msg_type}")
                    
                    if msg_type == "query_complete":
                        print("Query complete!")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        break
                    
                    if msg_type == "query_failed":
                        print("Query failed!")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        break
                        
                    if msg_type == "error":
                        print("Error received!")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        break
                        
                    if msg_type == "plan_created":
                        print("Plan created received!")
                        # print(json.dumps(data, indent=2, ensure_ascii=False))

                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
                    
    except Exception as e:
        print(f"Connection failed: {e}")
        # If connection fails, it might be because the server is not running.
        # In this environment, I cannot start the server easily if it's not already running.
        # But I can try to run this script assuming the user or environment has the server up.
        # If not, I will rely on unit tests or the previous integration test.

if __name__ == "__main__":
    # Check if websockets is installed
    try:
        import websockets
        asyncio.run(test_websocket_integration())
    except ImportError:
        print("websockets package not installed. Please install it to run this test.")
