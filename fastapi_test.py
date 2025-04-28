from typing import List, Union

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
from openai import OpenAI
app = FastAPI()
from dotenv import load_dotenv
import os
from core import Reflection
from chatbot import get_response
import uvicorn

load_dotenv()
class Message(BaseModel):
    message: str
    sender: str
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
reflection = Reflection(client)
messages: List[Message] =  []
clients: List[WebSocket] = []


def process_message(message: str) -> str:
    # Replace with your chatbot logic
    reflectedQ = reflection(messages)
    # res = aiResponse(reflectedQ)
    res = get_response(reflectedQ)
    messages.append(Message(message=res, sender="Bot"))
    return f"Echo: {message}"



app.add_middleware(
    CORSMiddleware,
    # allow_origins=["chrome-extension:/jlpalndmgiboeonamcfpcpnabddlapoa"],
    allow_origins=["*"],  # Replace with your extension ID
    allow_methods=["*", "OPTIONS"],
    allow_headers=["*"],
)

def clearMessages():
    global messages
    messages = []



@app.websocket("/api/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    
    try:
        # Gửi danh sách tin nhắn ban đầu
        await websocket.send_text(json.dumps({"message": [message.dict() for message in messages]}))
        while True:
            message = await websocket.receive_text()
            
            # Xử lý tin nhắn
            if message == "refresh":
                clearMessages()
            else: 
                messages.append(Message(message=message, sender="You"))
                # Gửi tin nhắn mới cho tất cả client
                for client in clients:
                    await client.send_text(json.dumps({"message": [message.dict() for message in messages]}))
                # Xử lý tin nhắn
                process_message(message)
                      
            # Broadcast danh sách tin nhắn đến tất cả client
            for client in clients:
                await client.send_text(json.dumps({"message": [message.dict() for message in messages]}))
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {websocket.client}")
        clients.remove(websocket)



def aiResponse(message) -> str:
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