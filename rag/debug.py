import uvicorn
import uuid
import os
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

from rag.memory import PostgresChatMessageHistory
from rag.query import QueryConversations
from rag.config import ChatQuestion, Postgres, UserId, NewUser, ConversationUuid
from rag.llm import DummyConversation
from langchain_core.messages import message_to_dict

conn_string = Postgres.POSTGRES_URL

query_db = QueryConversations(connection_string=conn_string)

app = FastAPI()

chain_debug = DummyConversation(model="gpt-3.5-turbo")


@app.post("/chat")
async def chat(
    question: ChatQuestion = Body(...),
):

    chat_memory = PostgresChatMessageHistory(
        user_id=question.user_id,
        conversation_uuid=question.conversation_uuid,
        connection_string=conn_string,
        table_name=os.getenv("TABLE_NAME_CONVERSATION_MESSAGES"),
    )
    chat_history_dict = [message_to_dict(message) for message in chat_memory.messages]

    res = chain_debug(question.question)

    chat_memory.add_user_message(
        message=question.question, tokens=res.get("prompt_tokens"), cost=0
    )
    chat_memory.add_ai_message(
        message=res.get("answer"), tokens=res.get("completion_tokens"), cost=0
    )

    return {
        "question": res.get("question"),
        "response": res.get("answer"),
        "chat_history": chat_history_dict,
        "total_tokens": res.get("completion_tokens") + res.get("prompt_tokens"),
        "total_cost": 444,
    }


@app.post("/new-conversation")
async def new_conversation(user: UserId = Body(...)):
    conv_uuid = str(uuid.uuid4())
    query_db.create_new_consersation(conv_uuid=conv_uuid, user_id=user.user_id)
    response = {"user_id": user.user_id, "conversation": conv_uuid}
    return JSONResponse(content=response, status_code=200)


@app.post("/list-conversations")
async def list_conversation(user: UserId = Body(...)):

    list_conversations_uuid = query_db.get_list_conversations_by_user(
        user_id=user.user_id
    )

    response = {
        "user_id": user.user_id,
        "conversations": {
            i: str(row["uuid"]) for i, row in enumerate(list_conversations_uuid)
        },
    }

    return JSONResponse(content=response, status_code=200)


@app.post("/get-conversation")
async def get_conversation(conversation: ConversationUuid = Body(...)):

    conversation = query_db.get_conversation_by_uuid(uuid=conversation.uuid)

    return JSONResponse(content=conversation, status_code=200)


@app.post("/get-user-tokens")
async def get_user_tokens(user: UserId = Body(...)):
    tokens_used = query_db.get_total_tokens_used_per_user(user_id=user.user_id)

    return JSONResponse(
        content={"tokens": tokens_used, "user_id": user.user_id}, status_code=200
    )


@app.post("/create-user")
async def create_user(user: NewUser = Body(...)):
    query_db.create_new_user(
        email=user.email, firstname=user.firstname, surname=user.surname
    )
    return JSONResponse(content="User created", status_code=200)


# @app.post("/clear")
# async def clear_conversation():
#     chain_debug.clear()
#     return JSONResponse({"message": "conversation deleted"})


# if __name__ == "__main__":
#     uvicorn.run("debug:app", host="localhost", port=8000, reload=True)
