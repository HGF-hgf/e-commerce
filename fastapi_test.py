from typing import List, Union
from pymongo import MongoClient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mongo_client = MongoClient(os.getenv("MONGODB_URl"))
db = mongo_client["HoangHaMobile"]
collection = db["chat-history"]

clients: List[WebSocket] = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*", "OPTIONS"],
    allow_headers=["*"],
)

async def load_chat_history(user_id: str) -> str:
    """Tải lịch sử chat từ MongoDB dưới dạng chuỗi."""
    try:
        chat_doc = collection.find_one({"user_id": user_id})
        print(f"Loaded chat doc for user_id {user_id}: {chat_doc}")  # Debug
        if chat_doc and "chat_history" in chat_doc:
            history = chat_doc["chat_history"]
            print(f"Loaded chat history string: {history}")  # Debug
            return history
        return ""
    except Exception as e:
        print(f"Error loading chat history: {str(e)}")
        return ""

async def save_chat_history(user_id: str, chat_history: str):
    """Lưu lịch sử chat vào MongoDB dưới dạng chuỗi."""
    try:
        result = collection.update_one(
            {"user_id": user_id},
            {"$set": {"chat_history": chat_history}},
            upsert=True
        )
        print(f"Saved chat history for user_id {user_id}: {result.modified_count} modified, {result.upserted_id}")  # Debug
    except Exception as e:
        print(f"Error saving chat history: {str(e)}")

def fix_json_string(json_str: str) -> str:
    """Sửa chuỗi JSON không hợp lệ."""
    try:
        json_str = re.sub(r'\n\s*', '', json_str.strip())
        json_str = re.sub(r"\'(\w+)\'(\s*:\s*)", r'"\1"\2', json_str)
        return json_str
    except Exception:
        return json_str

def build_context_string(chat_history: str, new_message: str = None, new_response: str = None) -> str:
    """Xây dựng chuỗi ngữ cảnh từ lịch sử chat và tin nhắn/phản hồi mới."""
    context = chat_history.strip()
    if new_message:
        context = f"{context}\nUser: {new_message}" if context else f"User: {new_message}"
    if new_response:
        context = f"{context}\nAssistant: {new_response}"
    print(f"Built context string: {context}")  # Debug
    return context.strip()

@app.websocket("/api/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    # Tạo hoặc lấy user_id từ client (nếu client gửi)
    user_id = str(uuid.uuid4())
    websocket.user_id = user_id
    websocket.chat_history = await load_chat_history(user_id)

    try:
        await websocket.send_text(json.dumps({
            "user_id": user_id,
            "chat_history": websocket.chat_history.split("\n") if websocket.chat_history else []
        }))

        while True:
            message = await websocket.receive_text()
            user_message_content = message

            # Xử lý tin nhắn JSON lồng nhau
            try:
                data = json.loads(message)
                user_id = data.get("user_id", user_id)  # Cập nhật user_id nếu client gửi
                websocket.user_id = user_id
                inner_json_str = data.get("message", message)
                try:
                    fixed_json_str = fix_json_string(inner_json_str)
                    inner_data = json.loads(fixed_json_str)
                    user_message_content = inner_data.get("message", inner_json_str)
                except json.JSONDecodeError:
                    user_message_content = inner_json_str
                # Tải lại lịch sử nếu user_id thay đổi
                if user_id != websocket.user_id:
                    websocket.chat_history = await load_chat_history(user_id)
            except json.JSONDecodeError:
                user_message_content = message
            print(f"Processed user message: {user_message_content}")  # Debug

            if user_message_content == "refresh":
                websocket.chat_history = ""
                await save_chat_history(user_id, websocket.chat_history)
                await websocket.send_text(json.dumps({
                    "user_id": user_id,
                    "chat_history": [],
                    "mentioned_products": []
                }))
            else:
                # Cập nhật lịch sử với tin nhắn người dùng
                websocket.chat_history = build_context_string(websocket.chat_history, new_message=user_message_content)
                await save_chat_history(user_id, websocket.chat_history)

                # Gọi get_response với chuỗi ngữ cảnh
                context_str = websocket.chat_history
                response = get_response(context_str, agent1)
                # Cập nhật lịch sử với phản hồi bot
                websocket.chat_history = build_context_string(websocket.chat_history, new_response=response)
                await save_chat_history(user_id, websocket.chat_history)

                # Xử lý mentioned products
                mentioned = get_mentioned(user_message_content, agent2)
                try:
                    mentioned = json.loads(mentioned) if isinstance(mentioned, str) else mentioned
                except json.JSONDecodeError:
                    mentioned = []

                await websocket.send_text(json.dumps({
                    "user_id": user_id,
                    "chat_history": websocket.chat_history.split("\n") if websocket.chat_history else [],
                    "mentioned_products": mentioned
                }))

                for client in clients:
                    if client != websocket:
                        await client.send_text(json.dumps({
                            "user_id": user_id,
                            "message": user_message_content,
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
        return {"user_id": user_id, "chat_history": chat_history.split("\n") if chat_history else []}
    raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử chat cho user_id này.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)