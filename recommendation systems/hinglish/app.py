from fastapi import FastAPI
from pydantic import BaseModel

from chatbot import chat


app = FastAPI()


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.post("/chat")
def chat_api(data: ChatRequest):

    response = chat(
        user_id=data.user_id,
        user_message=data.message
    )

    return {
        "response": response
    }