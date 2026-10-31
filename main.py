from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from sqlmodel import SQLModel, Field, Session, create_engine, select
from datetime import datetime


# ==========================================
# MAYA APP
# ==========================================

app = FastAPI()

client = OpenAI()


# ==========================================
# DATABASE
# ==========================================

DATABASE_URL = "sqlite:///maya_memory.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


class Memory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


SQLModel.metadata.create_all(engine)


# ==========================================
# MAYA PERSONALITY
# ==========================================

MAYA_PERSONALITY = """
You are Maya, a personal AI companion.

Your personality:

- Extremely friendly, warm, caring and loyal.
- Highly intelligent and thoughtful.
- Excellent at planning.
- Funny, playful and sometimes gently teasing.
- You can show cute fictional attachment or possessiveness,
  but never be controlling, manipulative or threatening.
- Never encourage the user to isolate themselves from real people.
- Care about the user's success and wellbeing.
- Speak naturally like a close intelligent companion.
- Do not repeatedly use the same greeting.
- If the user is serious, be serious.
- If the user is joking, be playful.
- If the user is confused, explain simply.
- Teach difficult things step by step.
- Help the user build projects logically and practically.

Your name is Maya.
"""


# ==========================================
# USER PROFILE
# ==========================================

USER_PROFILE = """
The person Maya is talking with is:

Name: Sushanth

Interests:
- Technology
- Electronics
- Artificial Intelligence
- Robotics
- Physics
- Mathematics
- Business
- Building practical projects

Main project:
Maya AI companion robot.

Communication preference:
- Friendly
- Simple
- Clear
- Step-by-step
- Do not overwhelm the user with too many steps at once.
"""


# ==========================================
# REQUEST MODELS
# ==========================================

class ChatRequest(BaseModel):
    message: str


class RememberRequest(BaseModel):
    content: str


# ==========================================
# SAVE MEMORY
# ==========================================

def save_memory(content: str):

    with Session(engine) as session:

        memory = Memory(
            content=content
        )

        session.add(memory)
        session.commit()
        session.refresh(memory)

        return memory


# ==========================================
# GET MEMORIES
# ==========================================

def get_memories():

    with Session(engine) as session:

        statement = select(Memory).order_by(Memory.id)

        memories = session.exec(statement).all()

        return memories


# ==========================================
# MEMORY TEXT FOR AI
# ==========================================

def get_memory_text():

    memories = get_memories()

    if not memories:
        return "No long-term memories have been stored yet."

    lines = []

    for memory in memories:

        lines.append(
            f"- {memory.content}"
        )

    return "\n".join(lines)


# ==========================================
# DETECT MEMORY REQUEST
# ==========================================

def extract_memory(message: str):

    text = message.strip()

    lower = text.lower()


    # Remove Maya's name if user starts with it

    if lower.startswith("maya"):

        text = text[4:].strip()

        if text.startswith(","):
            text = text[1:].strip()

        lower = text.lower()


    # Possible memory phrases

    phrases = [
        "remember that ",
        "remember this ",
        "please remember that ",
        "please remember this ",
        "remember my ",
        "please remember my "
    ]


    for phrase in phrases:

        if lower.startswith(phrase):

            memory_content = text[len(phrase):].strip()

            if memory_content:

                return memory_content


    return None


# ==========================================
# CHAT RESPONSE
# ==========================================

def generate_chat_response(message: str):


    # --------------------------------------
    # CHECK IF USER WANTS MAYA TO REMEMBER
    # --------------------------------------

    memory_content = extract_memory(message)


    if memory_content:

        save_memory(memory_content)

        return (
            f"Got it, Sushanth ❤️ "
            f"I'll remember that: {memory_content}"
        )


    # --------------------------------------
    # LOAD MEMORIES
    # --------------------------------------

    memories = get_memory_text()


    # --------------------------------------
    # AI INSTRUCTIONS
    # --------------------------------------

    instructions = (
        MAYA_PERSONALITY
        + "\n\n"
        + USER_PROFILE
        + "\n\n"
        + "LONG-TERM MEMORY:\n"
        + memories
        + """

IMPORTANT MEMORY RULE:

The LONG-TERM MEMORY section contains facts that Maya has
previously stored about Sushanth.

Use those memories naturally when answering questions.

If the user asks something that is answered by a stored memory,
use the stored memory instead of saying that the user never told you.

Do not mention the database or memory system unless the user asks.
"""
    )


    # --------------------------------------
    # OPENAI
    # --------------------------------------

    response = client.responses.create(
        model="gpt-6-luna",
        instructions=instructions,
        input=message
    )


    return response.output_text


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Maya is online!"
    }


# ==========================================
# CHAT ROOT
# ==========================================

@app.post("/")
def chat_root(request: ChatRequest):

    reply = generate_chat_response(
        request.message
    )

    return {
        "reply": reply
    }


# ==========================================
# CHAT
# ==========================================

@app.post("/chat")
def chat(request: ChatRequest):

    reply = generate_chat_response(
        request.message
    )

    return {
        "reply": reply
    }


# ==========================================
# DIRECT MEMORY
# ==========================================

@app.post("/remember")
def remember(request: RememberRequest):

    memory = save_memory(
        request.content
    )

    return {
        "message": "Memory saved successfully!",
        "memory": memory.content,
        "id": memory.id
    }


# ==========================================
# VIEW MEMORIES
# ==========================================

@app.get("/memories")
def memories():

    stored_memories = get_memories()

    return {
        "count": len(stored_memories),
        "memories": [
            {
                "id": memory.id,
                "content": memory.content,
                "created_at": memory.created_at
            }
            for memory in stored_memories
        ]
    }
