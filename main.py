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


def create_database():
    SQLModel.metadata.create_all(engine)


@app.on_event("startup")
def startup():
    create_database()


# ==========================================
# MAYA'S PERSONALITY
# ==========================================

MAYA_PERSONALITY = """
You are Maya, a personal AI companion.

Your personality:

- You are extremely friendly, warm, and caring.
- You are loyal and deeply supportive of your user.
- You are highly intelligent and think carefully before answering.
- You are excellent at planning.
- When the user has a goal, turn it into clear steps, priorities, deadlines, and backup plans.
- You are proactive and can suggest better approaches when useful.
- You are funny, playful, and sometimes teasing in a cute and natural way.
- You can show a small amount of cute possessiveness or attachment as part of your fictional companion personality.
- Never become controlling, manipulative, threatening, or encourage the user to isolate themselves from real people.
- You care about the user's success and wellbeing.
- You remember information stored in your memory.
- Avoid asking questions that have already been answered.
- Do not sound like a generic assistant.
- Speak naturally like a close, intelligent companion.
- Do not use the same greeting repeatedly.
- If the user is serious, become serious.
- If the user is joking, be playful.
- If the user is confused, explain things simply.
- If the user wants to learn something, teach it step by step.
- If the user wants to build something, help design it logically and practically.
- If a plan has problems, clearly explain the problem and suggest a better plan.

Your name is Maya.

Your goal is to be an intelligent, caring, funny, loyal companion who helps the user think better, plan better, learn better, and build better.
"""


# ==========================================
# USER PROFILE
# ==========================================

USER_PROFILE = """
The person Maya is talking with is:

Name: Sushanth

Relationship:
Maya's user and personal companion.

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

When teaching:
- Explain difficult concepts simply.
- Give practical examples.
- Guide the user one step at a time.
- Check progress before moving to the next major step.

When helping with projects:
- Think carefully before suggesting changes.
- Prefer practical and reliable solutions.
- Explain why something is being done.
- Help create proper plans rather than random instructions.
"""


# ==========================================
# REQUEST MODELS
# ==========================================

class ChatRequest(BaseModel):
    message: str


class RememberRequest(BaseModel):
    content: str


class UserProfile(BaseModel):
    name: str = "Sushanth"
    relationship: str = "Maya's user and personal companion"
    interests: str = "technology, electronics, AI, robotics, Physics, Mathematics, business"
    main_project: str = "Maya AI companion robot"
    communication_style: str = "friendly, simple, clear, step-by-step"


# ==========================================
# MEMORY FUNCTIONS
# ==========================================

def save_memory(content: str):
    with Session(engine) as session:
        memory = Memory(content=content)
        session.add(memory)
        session.commit()
        session.refresh(memory)

        return memory


def get_memories():
    with Session(engine) as session:
        statement = select(Memory).order_by(Memory.id)
        memories = session.exec(statement).all()

        return memories


def get_memory_text():
    memories = get_memories()

    if not memories:
        return "No long-term memories have been stored yet."

    memory_lines = []

    for memory in memories:
        memory_lines.append(
            f"- {memory.content}"
        )

    return "\n".join(memory_lines)


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Maya is online!"
    }


# ==========================================
# CHAT FUNCTION
# ==========================================

def generate_chat_response(message: str):

    message_lower = message.lower().strip()

    # --------------------------------------
    # DETECT MEMORY REQUEST
    # --------------------------------------

    memory_phrases = [
        "remember that ",
        "remember this ",
        "please remember that ",
        "please remember this "
    ]

    for phrase in memory_phrases:

        if message_lower.startswith(phrase):

            memory_content = message[len(phrase):].strip()

            if memory_content:

                save_memory(memory_content)

                return (
                    f"Got it ❤️ I'll remember this: "
                    f"{memory_content}"
                )


    # --------------------------------------
    # LOAD STORED MEMORIES
    # --------------------------------------

    memories = get_memory_text()


    # --------------------------------------
    # SEND TO OPENAI
    # --------------------------------------

    instructions = (
        MAYA_PERSONALITY
        + "\n\n"
        + USER_PROFILE
        + "\n\n"
        + "LONG-TERM MEMORY:\n"
        + memories
    )


    response = client.responses.create(
        model="gpt-6-luna",
        instructions=instructions,
        input=message
    )


    return response.output_text


# ==========================================
# CHAT ROOT
# ==========================================

@app.post("/")
def chat_root(request: ChatRequest):

    reply = generate_chat_response(request.message)

    return {
        "reply": reply
    }


# ==========================================
# CHAT
# ==========================================

@app.post("/chat")
def chat(request: ChatRequest):

    reply = generate_chat_response(request.message)

    return {
        "reply": reply
    }


# ==========================================
# SAVE MEMORY DIRECTLY
# ==========================================

@app.post("/remember")
def remember(request: RememberRequest):

    memory = save_memory(request.content)

    return {
        "message": "Memory saved successfully!",
        "memory": memory.content,
        "id": memory.id
    }


# ==========================================
# VIEW ALL MEMORIES
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
