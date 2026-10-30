from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

client = OpenAI()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"message": "Maya is online!"}


@app.post("/")
def chat_root(request: ChatRequest):
    response = client.responses.create(
        model="gpt-6-luna",
        input=request.message
    )

    return {
        "reply": response.output_text
    }


@app.post("/chat")
def chat(request: ChatRequest):
    response = client.responses.create(
        model="gpt-6-luna",
        input=request.message
    )

    return {
        "reply": response.output_text
    }
