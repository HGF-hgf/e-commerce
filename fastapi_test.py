from typing import List, Union
from pymongo import MongoClient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
from chatbot import get_response, get_mentioned, agent2, agent1
import uvicorn
import uuid
import re

load_dotenv()

app = FastAPI()

class Message(BaseModel):
    message: str
    sender: str

class UserIdRequest(BaseModel):
    user_id: str

# Khởi tạo client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mongo_client = MongoClient(os.getenv("MONGODB_URl"))
db = mongo_client["HoangHaMobile"]
collection = db["chat-history"]

# Danh sách clients để quản lý các WebSocket
clients: List[WebSocket] = []

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*", "OPTIONS"],
    allow_headers=["*"],
)

# Hàm lấy lịch sử chat từ MongoDB
async def load_chat_history(user_id: str) -> List[Message]:
    chat_doc = collection.find_one({"user_id": user_id})
    if chat_doc and "chat_history" in chat_doc:
        return [Message(**msg) for msg in chat_doc["chat_history"]]
    return []

# Hàm lưu lịch sử chat vào MongoDB
async def save_chat_history(user_id: str, chat_history: List[Message]):
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"chat_history": [msg.dict() for msg in chat_history]}},
        upsert=True
    )
    

@app.websocket("/api/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    # Tạo hoặc sử dụng user_id
    user_id = str(uuid.uuid4())
    websocket.user_id = user_id

    # Tải lịch sử chat từ MongoDB
    websocket.chat_history = await load_chat_history(user_id)

    try:
        # Gửi user_id và lịch sử chat ban đầu
        await websocket.send_text(json.dumps({
            "user_id": user_id,
            "chat_history": [msg.dict() for msg in websocket.chat_history]
        }))

        while True:
            message = await websocket.receive_text()

            # Xử lý tin nhắn
            if message == "refresh":
                websocket.chat_history = []  # Xóa lịch sử chat
                await save_chat_history(user_id, websocket.chat_history)
                await websocket.send_text(json.dumps({
                    "user_id": user_id,
                    "chat_history": [],
                    "mentioned_products": []
                }))
            else:
                # Thêm tin nhắn của người dùng

                user_message = Message(message=message, sender="You")
                websocket.chat_history.append(user_message)

                # Lấy phản hồi từ bot
                response = get_response(message, agent1)  # Giả sử trả về chuỗi
                bot_message = Message(message=response, sender="Bot")
                websocket.chat_history.append(bot_message)

                # Xử lý mentioned products
                try:
                    mentioned_data = get_mentioned(message, agent2)
                    mentioned_json = json.loads(mentioned_data)
                except Exception as e:
                    mentioned_json = {"mentioned_products": [], "error": str(e)}

                # Lưu lịch sử chat vào MongoDB
                await save_chat_history(user_id, websocket.chat_history)

                # Gửi lịch sử chat mới nhất và mentioned products
                await websocket.send_text(json.dumps({
                    "user_id": user_id,
                    "chat_history": [msg.dict() for msg in websocket.chat_history],
                    "mentioned_products": mentioned_json.get("mentioned_products", [])
                }))

                # Broadcast tin nhắn đến các client khác (nếu cần chat nhóm)
                for client in clients:
                    if client != websocket:
                        await client.send_text(json.dumps({
                            "user_id": user_id,
                            "message": message,
                            "sender": "You"
                        }))

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {websocket.client}")
        clients.remove(websocket)
    except Exception as e:
        print(f"Error in WebSocket: {str(e)}")
        clients.remove(websocket)
        await websocket.close()

@app.get("/api/history/{user_id}")
async def get_chat_history(user_id: str):
    chat_history = await load_chat_history(user_id)
    if chat_history:
        return {"user_id": user_id, "chat_history": [msg.dict() for msg in chat_history]}
    raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử chat cho user_id này.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)