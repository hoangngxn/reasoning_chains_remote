import bcrypt
from db import users_collection
import os
import jwt
from datetime import datetime, timedelta

def register_user(email, password, username):
    if users_collection.find_one({"email": email}):
        return False

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({"username": username,"email":email, "password": hashed})
    return True

def authenticate_user(username, password):
    user = users_collection.find_one({"username": username})
    if not user:
        return None

    if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        return user["_id"]
    return None

SECRET_KEY = os.getenv("SECRET_KEY")

def generate_jwt(user_id):
    expiration = datetime.utcnow() + timedelta(days=1)
    payload = {"user_id": str(user_id), "exp": expiration}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

