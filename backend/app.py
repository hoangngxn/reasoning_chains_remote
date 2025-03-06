from fastapi import FastAPI, Request, HTTPException, WebSocket
from starlette.middleware.cors import CORSMiddleware
from chainlit.utils import mount_chainlit
from db import users_collection, verify_password
from services.auth import generate_jwt, register_user
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
import os
from services.auth import verify_jwt
from db import users_collection, conversations_collection
from bson import ObjectId


app = FastAPI()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    print("🚀 API GET Running...")
    return {"message": "API is running..."}

class LoginUser(BaseModel):
    email: str
    password: str

class RegisterUser(BaseModel):
    username: str
    password: str
    email: str
        
@app.post("/login")
async def login(user: LoginUser):
    db_user = users_collection.find_one({"email": user.email})

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if verify_password(user.password, db_user["password"]):
        token = generate_jwt(str(db_user["_id"]))
        return {"token": token}
        
    raise HTTPException(status_code=400, detail="Invalid credentials")

@app.post("/register")
async def register(user: RegisterUser):
    if not register_user(user.email, user.password, user.username):
        raise HTTPException(status_code=400, detail="User already exists")
    return {"message": "User registered successfully"}

@app.get("/auth/google")
async def google_login():
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri=http://localhost:8000/auth/google/callback&response_type=code&scope=openid%20email%20profile"
    )

@app.get("/auth/google/callback")
async def google_callback(code: str):
    try:
        import requests       
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": "http://192.168.91.105:8000/auth/google/callback",
            "grant_type": "authorization_code"
        }
        
        response = requests.post(token_url, data=payload)
        token_data = response.json()
        print(token_data)
        if "access_token" not in token_data:
            return {"error": "Invalid token"}

        access_token = token_data["access_token"]

        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
        user_info = user_info_response.json()

        email = user_info.get("email")
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")
        sub = user_info.get("sub")

        if not email:
            return {"error": "Unauthorized"}

        db_user = users_collection.find_one({"email": email})
        if db_user:
            user_id = str(db_user["_id"])
        else:
            new_user = {
                "email": email,
                "username": name,
                "picture": picture,
                "sub": sub
            }
            result = users_collection.insert_one(new_user)
            user_id = str(result.inserted_id)
        jwt_token = generate_jwt(str(user_id))
        return RedirectResponse(f"http://192.168.90.161:3000/oauth2/redirect?token=" + jwt_token + "&userId=" + user_id)
    except Exception as e:
        return {"error": str(e)}

@app.get("/info")
async def get_info_user(request: Request):
    tk = request.headers.get("Authorization")
    token = tk.split(" ")[1]
    print(token)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        user_id = verify_jwt(token)
        print("User ID:", user_id)
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_info = {
            "id": str(user["_id"]),
            "email": user.get("email", ""),
            "username": user.get("username", ""),
            "picture": user.get("picture", ""),
        }
        return user_info
        
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/conversations")
async def get_conversations(request: Request):
    tk = request.headers.get("Authorization")
    token = tk.split(" ")[1]
    print(token)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        user_id = verify_jwt(token)
        print("uid", user_id)
        conversations = list(conversations_collection.find({"user_id": user_id}))
        elements = []
        for convo in conversations:
            messages = convo.get("messages", [])
            if len(messages) > 0:
                first_message = messages[0].get("text", "")
                words = first_message.split()
                short_content = " ".join(words[:6]) if words else "No Msg"
            else:
                short_content = "No Msg"

            elements.append({
                "id_conv": str(convo['_id']),
                "content": short_content
            })
        return elements    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/history/{conv_id}")
async def get_history(conv_id: str, request: Request):
    tk = request.headers.get("Authorization")
    token = tk.split(" ")[1]
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        user_id = verify_jwt(token)
        conversation = conversations_collection.find_one({"_id": ObjectId(conv_id), "user_id": user_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation.get("messages", [])
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
mount_chainlit(app=app, target="cl_app.py", path="/chainlit")