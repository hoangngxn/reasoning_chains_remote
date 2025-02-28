import os
import google.generativeai as genai
import chainlit as cl

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
print("Connected to Gemini!", GOOGLE_API_KEY)

settings = {
    "model": "gemini-2.0-flash",
    "temperature": 0.7,
    "max_output_tokens": 500,
}

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "You are a helpful assistant."}],
    )
    await cl.Message(content="Connected to Chainlit!").send()

@cl.on_message
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    model = genai.GenerativeModel(settings["model"])
    convo = model.start_chat(history=[])

    response = convo.send_message(message.content)

    async for part in response:
        await msg.stream_token(part.text)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()