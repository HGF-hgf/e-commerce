from typing import List, Union
from pymongo import MongoClient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
from openai import OpenAI
app = FastAPI()
from dotenv import load_dotenv
import os
from core import Reflection
from chatbot import get_response, get_mentioned, agent2, agent1
import uvicorn
import uuid
load_dotenv()


class Message(BaseModel):
    message: str
    sender: str
    
class UserIdRequest(BaseModel):
    user_id: str
    
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["HoangHaMobile"]
collection = db["chat-history"]

reflection = Reflection(client)
messages: List[Message] =  []
clients: List[WebSocket] = []


def process_message(message: str) -> str:
    # Replace with your chatbot logic
    reflected_q = reflection(messages)
    res = get_response(reflected_q, agent1)
    messages.append(Message(message=res, sender="Bot"))
    return f"Echo: {message}"



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your extension ID
    allow_methods=["*", "OPTIONS"],
    allow_headers=["*"],
)

def clear_messages():
    global messages
    messages = []



@app.websocket("/api/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    
    # Tạo user_id và khởi tạo lịch sử chat
    user_id = str(uuid.uuid4())
    websocket.user_id = user_id
    websocket.chat_history = []  # Lịch sử chat riêng cho mỗi user
    
    try:
        # Gửi lịch sử chat ban đầu (nếu có)
        await websocket.send_text(json.dumps({
            "user_id": user_id,
            "chat_history": [msg.dict() for msg in websocket.chat_history]
        }))
        
        while True:
            message = await websocket.receive_text()
            
            # Xử lý tin nhắn
            if message == "refresh":
                websocket.chat_history = []  # Xóa lịch sử chat của user
                # Cập nhật cơ sở dữ liệu
                collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"chat_history": []}},
                    upsert=True
                )
            else:
                # Thêm tin nhắn của người dùng vào lịch sử
                websocket.chat_history.append(Message(message=message, sender="You"))
                
                # Xử lý tin nhắn và lấy phản hồi từ bot
                response = process_message(message)  # Giả sử hàm này trả về phản hồi
                websocket.chat_history.append(Message(message=response, sender="Bot"))
                
                try:
                    mentioned_data = get_mentioned(message, agent2)
                except Exception as e:
                    mentioned_data = {"mentioned_products": [], "error": str(e)}

                
                # Cập nhật cơ sở dữ liệu
                collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"chat_history": [msg.dict() for msg in websocket.chat_history]}},
                    upsert=True
                )
                
                # Gửi lịch sử chat mới nhất cho client hiện tại
                await websocket.send_text(json.dumps({
                    "user_id": user_id,
                    "chat_history": [msg.dict() for msg in websocket.chat_history],
                    "mentioned_products": mentioned_data.get("mentioned_products", [])
                }))
                
                # Broadcast tin nhắn đến tất cả client (tùy chọn, nếu muốn chat nhóm)
                for client in clients:
                    if client != websocket:  # Không gửi lại cho chính client gửi tin nhắn
                        await client.send_text(json.dumps({
                            "user_id": websocket.user_id,
                            "message": message,
                            "sender": "You"
                        }))
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {websocket.client}")
        clients.remove(websocket)


@app.get("/api/history/{user_id}")
async def get_chat_history(user_id: str):
    chat_doc = collection.find_one({"user_id": user_id})
    if chat_doc and "chat_history" in chat_doc:
        return {"user_id": user_id, "chat_history": chat_doc["chat_history"]}
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử chat cho user_id này.")


def ai_response(message) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": ""},
            {
                "role": "user",
                "content": message
            }
        ]
    )
    content = completion.choices[0].message.content
    return content if content is not None else ""



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)