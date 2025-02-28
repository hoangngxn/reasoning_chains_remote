from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import os
import uvicorn

from cl_app import generate_llm_response
from db import conversation_collection, chat_history_collection
from models import Conversation, ConversationCreate, ChatMessage, MessageRequest

load_dotenv()

# Constants
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# FastAPI startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    if GOOGLE_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        print("Initialized Google Generative AI provider")
    
    await conversation_collection.create_index("id", unique=True)
    await chat_history_collection.create_index("conversation_id")
    
    yield
    print("Shutting down LLM backend")

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes for conversation management
@app.post("/conversations", response_model=Conversation)
async def create_conversation(conversation: ConversationCreate):
    new_conversation = Conversation(title=conversation.title)
    await conversation_collection.insert_one(new_conversation.dict())
    return new_conversation

@app.get("/conversations", response_model=list[Conversation])
async def list_conversations():
    conversations = await conversation_collection.find().sort("updated_at", -1).to_list(100)
    return [Conversation(**conv) for conv in conversations]

@app.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    conversation = await conversation_collection.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return Conversation(**conversation)

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    result = await conversation_collection.delete_one({"id": conversation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await chat_history_collection.delete_many({"conversation_id": conversation_id})
    return {"message": "Conversation and associated messages deleted"}

@app.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessage])
async def get_conversation_messages(conversation_id: str):
    conversation = await conversation_collection.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await chat_history_collection.find({"conversation_id": conversation_id}).sort("created_at", 1).to_list(1000)
    return [ChatMessage(**msg) for msg in messages]

# Routes for message handling
@app.post("/messages", response_model=ChatMessage)
async def send_message(message_request: MessageRequest):
    conversation_id = message_request.conversation_id
    if not conversation_id:
        new_conversation = await create_conversation(ConversationCreate())
        conversation_id = new_conversation.id
    else:
        conversation = await conversation_collection.find_one({"id": conversation_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    user_message = ChatMessage(conversation_id=conversation_id, role="user", message=message_request.message)
    await chat_history_collection.insert_one(user_message.dict())

    message_history = await chat_history_collection.find({"conversation_id": conversation_id}).sort("created_at", 1).to_list(1000)
    formatted_messages = [{"role": msg["role"], "message": msg["message"]} for msg in message_history]

    assistant_response = await generate_llm_response(formatted_messages, model=message_request.model)

    assistant_message = ChatMessage(conversation_id=conversation_id, role="assistant", message=assistant_response)
    await chat_history_collection.insert_one(assistant_message.dict())

    await conversation_collection.update_one({"id": conversation_id}, {"$set": {"updated_at": datetime.utcnow()}})
    return assistant_message

# WebSocket endpoint
@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    
    try:
        conversation = await conversation_collection.find_one({"id": conversation_id})
        if not conversation:
            new_conversation = Conversation(id=conversation_id, title="New Conversation")
            await conversation_collection.insert_one(new_conversation.dict())

        while True:
            data = await websocket.receive_json()
            if "message" not in data:
                await websocket.send_json({"error": "Message is required"})
                continue
            
            user_message = data["message"]
            model = data.get("model", "gemini-2.0-flash")

            chat_message = ChatMessage(conversation_id=conversation_id, role="user", message=user_message)
            await chat_history_collection.insert_one(chat_message.dict())

            message_history = await chat_history_collection.find({"conversation_id": conversation_id}).sort("created_at", 1).to_list(1000)
            formatted_messages = [{"role": msg["role"], "message": msg["message"]} for msg in message_history]

            try:
                response = await generate_llm_response(formatted_messages, model)
                assistant_message = ChatMessage(conversation_id=conversation_id, role="assistant", message=response)
                await chat_history_collection.insert_one(assistant_message.dict())

                await conversation_collection.update_one({"id": conversation_id}, {"$set": {"updated_at": datetime.utcnow()}})

                await websocket.send_json({"type": "message", "data": assistant_message.dict()})
            except Exception as e:
                await websocket.send_json({"type": "error", "data": {"error": str(e)}})
    except WebSocketDisconnect:
        print(f"Client disconnected from conversation {conversation_id}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
