from fastapi import FastAPI, WebSocket, Request, HTTPException
from starlette.middleware.cors import CORSMiddleware
from chainlit.user import User
from chainlit.utils import mount_chainlit
from chainlit.server import _authenticate_user
import chainlit as cl
import os
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/custom-auth")
async def custom_auth(request: Request):
    # Verify the user's identity with custom logic.
    user = User(identifier="Test User")

    return await _authenticate_user(request, user)

@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    user_message = data.get("message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Initialize the AI model
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    print("Connected to Gemini!", GOOGLE_API_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    settings = {
        "model": "gemini-2.0-flash",
        "temperature": 0.7,
        "max_output_tokens": 500,
    }
    model = genai.GenerativeModel(settings["model"])
    convo = model.start_chat(history=[])

    # Send the message to the AI model
    response = convo.send_message(user_message)

    # Gemini API trả về thẳng .text
    ai_response = response.text

    return {"response": ai_response}

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             data = await websocket.receive_json()
#             user_message = data.get("message")
#             if not user_message:
#                 await websocket.send_json({"error": "Message is required"})
#                 continue

#             msg = cl.Message(content=user_message)
#             await cl.run_message_callbacks(msg)

#             for token in msg.content.split():
#                 await websocket.send_json({"token": token})

#             await websocket.send_json({"end": True})

#     except Exception as e:
#         await websocket.send_json({"error": str(e)})
#     finally:
#         await websocket.close()
        
mount_chainlit(app=app, target="cl_app.py", path="/chainlit")