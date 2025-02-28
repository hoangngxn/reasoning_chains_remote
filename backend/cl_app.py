import asyncio
import google.generativeai as genai
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

async def generate_llm_response(messages: list[dict[str, str]], model: str = "gemini-2.0-flash"):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key not configured")
    
    try:
        genai_model = genai.GenerativeModel(model)
        history = [{"role": msg["role"], "parts": [msg["message"]]} for msg in messages[:-1]]
        chat = genai_model.start_chat(history=history)

        response = await asyncio.to_thread(
            chat.send_message,
            messages[-1]["message"],
            generation_config={"temperature": 0.7, "max_output_tokens": 800}
        )

        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
