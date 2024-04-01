import uvicorn
from datetime import datetime
import uuid
import os
from fastapi import FastAPI, Body, HTTPException, Query
from fastapi.responses import JSONResponse

from rag.memory import PostgresChatMessageHistory
from rag.query import QueryConversations
from rag.config import (
    ChatQuestion,
    Postgres,
    UserId,
    NewUser,
    ConversationUuid,
    ConversationUpdateRequest,
)
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

    response_json = {
        "question": question.question,
        "response": res.get("answer"),
        "chat_history": chat_history_dict,
        "total_tokens": res.get("completion_tokens") + res.get("prompt_tokens"),
        "total_cost": 444,
    }

    return JSONResponse(content=response_json, status_code=200)


@app.post("/new-conversation")
async def new_conversation(user: UserId = Body(...)):
    conv_uuid = str(uuid.uuid4())
    conv_name = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    query_db.create_new_consersation(
        conv_uuid=conv_uuid, user_id=user.user_id, conv_name=conv_name
    )
    response = {"user_id": user.user_id, "conversation": conv_uuid}
    return JSONResponse(content=response, status_code=200)


@app.get("/list-conversations")
async def list_conversations(
    user_id: str = Query(..., description="The ID of the user"),
):

    list_conversations_uuid = query_db.get_list_conversations_by_user(user_id=user_id)

    response = {
        "user_id": user_id,
        "conversations": {
            i: {"uuid": str(row["uuid"]), "name": row["name"]}
            for i, row in enumerate(list_conversations_uuid)
        },
    }

    return JSONResponse(content=response, status_code=200)


@app.get("/conversation-messages/{conversation_uuid}")
async def get_conversation(conversation_uuid: str):
    try:
        conversation = query_db.get_conversation_messages_by_uuid(
            uuid=conversation_uuid
        )
        if conversation:
            return JSONResponse(content={"conversation": conversation}, status_code=200)
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/get-conversation")
# async def get_conversation(conversation: ConversationUuid = Body(...)):

#     conversation = query_db.get_conversation_by_uuid(uuid=conversation.uuid)

#     return JSONResponse(content=conversation, status_code=200)


@app.put("/conversations/{conversation_uuid}")
async def update_conversation(
    conversation_uuid: str, request_body: ConversationUpdateRequest
):
    try:
        # Extract the new name from the request body
        new_name = request_body.new_name

        # Call the method to update the conversation name by UUID
        success = query_db.update_conversation_name(conversation_uuid, new_name)
        if success:
            return {"message": "Conversation name updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        # Log the error or handle it as per your application's requirements
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{conversation_uuid}")
async def delete_conversation(conversation_uuid: str):
    try:
        # Call the method to delete the conversation by UUID
        success = query_db.delete_conversation(conversation_uuid)
        if success:
            return JSONResponse(
                content={"message": "Conversation deleted successfully"},
                status_code=200,
            )
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
