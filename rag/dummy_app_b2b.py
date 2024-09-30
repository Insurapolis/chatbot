import uvicorn
from datetime import datetime
import uuid
from fastapi import FastAPI, Body, HTTPException, status, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datamodels.constants import TABLE_CONVERSATION_MESSAGES
from datamodels.models import Base

from rag.auth import decode_token, user_can_manage_client
from rag.chatbot.memory import PostgresChatMessageHistory
from rag.chatbot.llm import DummyConversation
from rag.query import QueryConversations
from rag.config import (
    ChatQuestion,
    Postgres,
    ConversationUpdateRequest,
)

from langchain_core.messages import message_to_dict


# Create an instance of the Postgres class
postgres_instance = Postgres()
# Access the postgre_url property from the instance
conn_string = postgres_instance.postgre_url
# The instance for the db
query_db = QueryConversations(connection_string=conn_string)

# The chain for the dummy rag
chain_debug = DummyConversation(model="gpt-3.5-turbo")

# The app
app = FastAPI()

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def chat(
    question: ChatQuestion = Body(...),
    playload=Depends(decode_token),
    managed_client_uuid: uuid.UUID = Header(...),
):

    # Check if the client is the owner of the conversation.
    if not query_db.user_owns_conversation(
        user_uuid=managed_client_uuid, conversation_uuid=question.conversation_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client does not have the rights to access this conversation",
        )

    if not user_can_manage_client(
        managed_client_uuid=managed_client_uuid,
        user_sub=playload["sub"],
        user_email=playload["email"],
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not manage this client",
        )

    chat_memory = PostgresChatMessageHistory(
        conversation_uuid=question.conversation_uuid,
        connection_string=conn_string,
        table_name=TABLE_CONVERSATION_MESSAGES,
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


@app.post("/conversation")
async def create_new_conversation(
    playload=Depends(decode_token), managed_client_uuid: uuid.UUID = Header(...)
):

    conv_uuid = str(uuid.uuid4())
    conv_name = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if not user_can_manage_client(
        managed_client_uuid=managed_client_uuid,
        user_sub=playload["sub"],
        user_email=playload["email"],
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active user does not managed this client",
        )

    try:
        query_db.create_new_conversation(
            user_uuid=managed_client_uuid, conv_uuid=conv_uuid, conv_name=conv_name
        )

        chat_memory = PostgresChatMessageHistory(
            conversation_uuid=conv_uuid,
            connection_string=conn_string,
            table_name=TABLE_CONVERSATION_MESSAGES,
        )

        chat_memory.add_ai_message(
            message="Bienvenu chez Insurapolis, comment puis-je vous aider ?",
            cost=0,
            tokens=12,
        )

        chat_history_dict = [
            message_to_dict(message) for message in chat_memory.messages
        ]

        response_data = {
            "user_email": playload["email"],
            "managed_client_uuid": str(managed_client_uuid),
            "conversation_uuid": conv_uuid,
            "conversation_name": conv_name,
            "chat_history": chat_history_dict,
        }

        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/conversations")
async def list_conversations(
    playload=Depends(decode_token), managed_client_uuid: uuid.UUID = Header(...)
):

    if not user_can_manage_client(
        managed_client_uuid=managed_client_uuid,
        user_sub=playload["sub"],
        user_email=playload["email"],
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active user does not managed this client",
        )

    try:
        list_conversations_uuid = query_db.get_list_conversations_by_user(
            user_uuid=managed_client_uuid
        )

        response = {
            "user_email": playload["email"],
            "managed_client_uuid": str(managed_client_uuid),
            "conversations": [
                {
                    "uuid": str(row[0]),
                    "name": row[1],
                    "datetime_last_message": row[2].isoformat(),
                }
                for row in list_conversations_uuid
            ],
        }

        return JSONResponse(content=response, status_code=status.HTTP_200_OK)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/conversation/{conversation_uuid}")
async def get_conversation(
    conversation_uuid: str,
    playload=Depends(decode_token),
    managed_client_uuid: uuid.UUID = Header(...),
):

    if not user_can_manage_client(
        managed_client_uuid=managed_client_uuid,
        user_sub=playload["sub"],
        user_email=playload["email"],
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active user does not managed this client",
        )

    # Check if the client is the owner of the conversation.
    if not query_db.user_owns_conversation(
        user_uuid=managed_client_uuid, conversation_uuid=conversation_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have the rights to access this conversation",
        )

    try:
        # Fetch conversation messages by UUID
        conversation = query_db.get_conversation_messages_by_uuid(
            conv_uuid=conversation_uuid
        )
        if conversation:
            return JSONResponse(
                content={
                    "user_email": playload["email"],
                    "managed_client_uuid": str(managed_client_uuid),
                    "conversation": conversation,
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
    except ValueError as e:
        # Handle potential ValueError from the database operation or data processing
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/conversation/{conversation_uuid}")
async def update_conversation(
    conversation_uuid: str,
    request_body: ConversationUpdateRequest,
    playload=Depends(decode_token),
    managed_client_uuid: uuid.UUID = Header(...),
):

    if not user_can_manage_client(
        managed_client_uuid=managed_client_uuid,
        user_sub=playload["sub"],
        user_email=playload["email"],
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active user does not managed this client",
        )

    # Extract the new name from the request body
    new_name = request_body.name

    if not query_db.user_owns_conversation(
        user_uuid=managed_client_uuid, conversation_uuid=conversation_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have the rights to access this conversation",
        )

    if query_db.conversation_name_exists(
        user_uuid=managed_client_uuid, conversation_name=new_name
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation name already exists",
        )
    try:
        # Update the conversation name by UUID
        success = query_db.update_conversation_name(conversation_uuid, new_name)
        if success:
            return {
                "managed_client_uuid": str(managed_client_uuid),
                "message": "Conversation name updated successfully",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
    except Exception as e:
        # Log the error or handle it as per your application's requirements
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversation/{conversation_uuid}")
async def delete_conversation(
    conversation_uuid: str,
    playload=Depends(decode_token),
    managed_client_uuid: uuid.UUID = Header(...),
):
    if not user_can_manage_client(
        managed_client_uuid=managed_client_uuid,
        user_sub=playload["sub"],
        user_email=playload["email"],
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active user does not managed this client",
        )

    try:
        # Call the method to delete the conversation by UUID
        success = query_db.delete_conversation(conversation_uuid)
        if success:
            return JSONResponse(
                content={
                    "managed_client_uuid": str(managed_client_uuid),
                    "message": "Conversation deleted successfully",
                },
                status_code=200,
            )
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get-user-tokens")
async def get_user_tokens(playload=Depends(decode_token)):
    tokens_used = query_db.get_total_tokens_used_per_user(user_uuid=playload["sub"])

    return JSONResponse(
        content={"tokens": tokens_used, "user_uuid": playload["sub"]}, status_code=200
    )


@app.get("/get-sub")
async def get_sub(playload=Depends(decode_token)):

    response = {"sub": playload["sub"], "email": playload["email"]}

    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


if __name__ == "__main__":
    uvicorn.run("dummy_app_b2b:app", host="localhost", port=8000, reload=True)
