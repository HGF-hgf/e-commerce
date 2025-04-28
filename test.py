import websocket
import json

def on_message(ws, message):
    print(f"Received: {message}")
    try:
        data = json.loads(message)
        assert "message" in data, "Response không có key 'message'"
        print("Response format is correct!")
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except AssertionError as e:
        print(f"Error: {e}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Closed connection")

def on_open(ws):
    print("Connected to WebSocket")
    # Gửi một tin nhắn test
    ws.send("hello")
    # Gửi lệnh refresh
    ws.send("refresh")

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "ws://localhost:8000/api/chat",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()