import os
import motor.motor_asyncio

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.llm_chat_app
conversation_collection = db.conversations
chat_history_collection = db.chat_history
