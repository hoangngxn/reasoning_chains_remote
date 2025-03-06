import os
import google.generativeai as genai
from services.auth import verify_jwt
import chainlit as cl
from db import users_collection, conversations_collection
from bson import ObjectId
import bcrypt
from typing import Dict, Optional
import jwt
from config import INSTRUCTION_PROMPT
import json
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


settings = {
    "model": "gemini-2.0-flash",
    "temperature": 0.7,
    "max_output_tokens": 500,
}
newchat = False
model = genai.GenerativeModel(settings["model"])

# Testing chainlit
# @cl.oauth_callback
# def oauth_callback(provider_id: str, token: str, raw_user_data: Dict[str, str], default_user: cl.User) -> Optional[cl.User]:
#     if provider_id == "google":
#         print("Google Login Success")
#         print(raw_user_data)
#         default_user.metadata["email"] = raw_user_data["email"]
#         return default_user
#     else:
#         return None

# @cl.header_auth_callback
# def header_auth_callback(headers: Dict) -> Optional[cl.User]:
#     token = headers.get("Authorization").split(" ")[1]

#     try:
#         user_id = verify_jwt(token)
#         user = users_collection.find_one({"_id": ObjectId(user_id)})
#         if user:
#             return cl.User(identifier=user["email"], metadata={"user_id": str(user["_id"]), "role": "user"})
#     except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
#         return None

#     return None



# Hàm xác thực người dùng
# @cl.password_auth_callback
# async def verify_user(email: str, password: str):
#     user = users_collection.find_one({"email": email})
#     if user and bcrypt.checkpw(password.encode(), user["password"]):
#         return cl.User(identifier=email, metadata={"user_id": str(user["_id"])})
#     return None
from chainlit.config import config
origins = [ 
    "http://localhost:5173", 
    "http://192.168.90.161:5173" 
] 
config.cors = {
    "allow_origins": origins,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "allow_credentials": True
}
@cl.on_chat_start
async def on_chat_start():
    user_env = cl.user_session.get("env")
    if isinstance(user_env, str):
        user_env = json.loads(user_env)

    token = user_env["Authorization"].replace("Bearer ", "")
    try:
        user_id = verify_jwt(token)
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            print(user)
            current_user = cl.User(identifier=user["email"], metadata={"user_id": str(user["_id"]), "role": "user"})
            cl.user_session.set("identifier", current_user.identifier)
            cl.user_session.set("metadata", current_user.metadata)
            cl.context.session.user = current_user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
        return None
    
    if not user:
        await cl.Message(content="You must log in to start chatting!").send()
        return
    
    cl.user_session.set("message_history", [])
    await cl.Message(content="Welcome! How can I assist you today?").send()

@cl.on_message
async def on_message(message: cl.Message):
    selected_conversation_id = message.metadata.get("conversation_id")
    current_conversation_id = cl.user_session.get("conversation_id")
    message_history = cl.user_session.get("message_history")

    # If user create another conversation
    if selected_conversation_id and selected_conversation_id != current_conversation_id:
        cl.user_session.set("conversation_id", selected_conversation_id)
        existing_conversation = conversations_collection.find_one({"_id": ObjectId(selected_conversation_id)})
        if existing_conversation:
            message_history = existing_conversation["messages"]
            cl.user_session.set("message_history", message_history)
        else:
            message_history = []
            cl.user_session.set("message_history", message_history)

    if not cl.user_session.get("conversation_id"):
        conversation = {"user_id": cl.user_session.get("user").metadata["user_id"], "messages": []}
        conversation_id = str(conversations_collection.insert_one(conversation).inserted_id)
        cl.user_session.set("conversation_id", conversation_id)
        message_history = []
        cl.user_session.set("message_history", message_history)
        
    # Original user message for storage
    original_user_message = {
        "role": "user",
        "parts": [{"text": message.content}]
    }
    
    # Add instruction prompt to user message for LLM
    prompted_message_content = f"{INSTRUCTION_PROMPT}\n{message.content}"
    
    # Store the original message in history
    message_history.append(original_user_message)

    # Start Gemini Chat but send the prompted message
    convo = model.start_chat(history=message_history)
    response = convo.send_message(prompted_message_content)

    # Sending message to the front
    msg = cl.Message(content=response.text)

    msg.metadata = {"conversation_id": str(message.metadata.get("conversation_id"))}    
    await msg.send()

    assistant_message = {
        "role": "assistant",
        "parts": [{"text": response.text}]
    }
    message_history.append(assistant_message)

    conversations_collection.update_one(
        {"_id": ObjectId(cl.user_session.get("conversation_id"))},
        {"$push": {"messages": original_user_message}}
    )

    conversations_collection.update_one(
        {"_id": ObjectId(cl.user_session.get("conversation_id"))},
        {"$push": {"messages": assistant_message}}
    )