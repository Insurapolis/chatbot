import os
import uvicorn
import uuid
from datetime import datetime

from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import message_to_dict

from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, Body, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.rag.utils import format_package_data, sentence_transformer_ef
from src.rag.auth import decode_token
from src.rag.query import QueryConversations
from src.rag.config import (
    ChatQuestion,
    Postgres,
    ConversationUpdateRequest,
    VectorDatabaseFilter,
)

from src.rag.chatbot.llm import OllamaChatbot, OpenaiChatbot
from src.rag.chatbot.retriever import VectorZurichChromaDbClient
from src.rag.constants import DB_PATH, COLLECTION_NAME
from dotenv import load_dotenv

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# Create an instance of the Postgres class
postgres_instance = Postgres()
conn_string = postgres_instance.postgre_url

# Get the query client
query_db = QueryConversations(connection_string=conn_string)

# Retriever
chroma_collection: VectorZurichChromaDbClient = (
    VectorZurichChromaDbClient.get_retriever(
        collection_name=COLLECTION_NAME,
        db_path=DB_PATH,
        embeddings=sentence_transformer_ef,
    )
)

# chain = OllamaChatbot.chain_from_config(config={"temperature": 0, "model": "llama3.2"})
# The langchain chain
chain = OpenaiChatbot.chain_from_config(config="./openai_config.yml")

# FastApi app
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
async def chat(question: ChatQuestion = Body(...), playload=Depends(decode_token)):

    # Check if the user is the owner of the conversation.
    if not query_db.user_owns_conversation(
        user_uuid=playload["sub"], conversation_uuid=question.conversation_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have the rights to access this conversation",
        )

    chat_history_obj = query_db.get_messages(question.conversation_uuid)
    chat_history_prompt = chat_history_obj[-2 * 2 :]
    chat_history_dict = [message_to_dict(message) for message in chat_history_obj]

    # user package_info
    user_package = query_db.get_user_packages(user_uuid=playload["sub"])
    list_user_packages, deductible_info, sum_insured_info = format_package_data(
        data=user_package
    )

    # Retriver filter
    user_filter = VectorDatabaseFilter(mapping_package=list_user_packages).filters()

    # User package
    user_package_data_info, list_ids_retriver = (
        chroma_collection.get_zurich_package_info(
            filter_packages=user_filter, user_question=question.question, top_k=3
        )
    )

    # General Condition
    general_condition = chroma_collection.get_zurich_general_condition()

    # Context for the LLM
    context = (
        f"{user_package_data_info}\nThe insurance general condition:{general_condition}"
    )

    # Request LLM
    with get_openai_callback() as cb:
        res = chain.invoke(
            {
                "question": question.question,
                "chat_history": chat_history_prompt,
                "deductible": deductible_info,
                "sum_insured": sum_insured_info,
                "context": context,
            }
        )

    # Add human message to the DB
    query_db.add_user_message(
        message=question.question,
        tokens=cb.prompt_tokens,
        cost=cb.total_cost,
        conversation_uuid=question.conversation_uuid,
    )

    # Add AI message to the DB
    query_db.add_ai_message(
        message=res.content,
        tokens=cb.completion_tokens,
        cost=cb.total_cost,
        conversation_uuid=question.conversation_uuid,
    )

    response_data = {
        "question": question.question,
        "response": res.content,
        "chat_history": chat_history_dict,
        "total_tokens": cb.total_tokens,
        "total_cost": cb.total_cost,
    }

    return JSONResponse(content=response_data, status_code=200)


@app.post("/conversation")
async def create_new_conversation(playload=Depends(decode_token)):

    conv_uuid = str(uuid.uuid4())
    conv_name = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    user_uuid = playload["sub"]

    try:
        query_db.create_new_conversation(
            user_uuid=user_uuid,
            conv_uuid=conv_uuid,
            conv_name=conv_name,
            created_by=user_uuid,
        )

        chat_memory = PostgresChatMessageHistory(
            conversation_uuid=conv_uuid,
            connection_string=conn_string,
            table_name=os.getenv("TABLE_NAME_CONVERSATION_MESSAGES"),
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
            "conversation_uuid": conv_uuid,
            "conversation_name": conv_name,
            "chat_history": chat_history_dict,
        }

        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/conversations")
async def list_conversations(playload=Depends(decode_token)):

    try:
        list_conversations_uuid = query_db.get_list_conversations_by_user(
            user_uuid=playload["sub"]
        )

        response = {
            "user_email": playload["email"],
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
):

    user_uuid = playload["sub"]

    # Check if the user is the owner of the conversation.
    if not query_db.user_owns_conversation(
        user_uuid=user_uuid, conversation_uuid=conversation_uuid
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
                content={"conversation": conversation}, status_code=status.HTTP_200_OK
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
):

    user_uuid = playload["sub"]

    # Extract the new name from the request body
    new_name = request_body.name

    if not query_db.user_owns_conversation(
        user_uuid=user_uuid, conversation_uuid=conversation_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have the rights to access this conversation",
        )

    if query_db.conversation_name_exists(
        user_uuid=user_uuid, conversation_name=new_name
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation name already exists",
        )
    try:
        # Update the conversation name by UUID
        success = query_db.update_conversation_name(conversation_uuid, new_name)
        if success:
            return {"message": "Conversation name updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
    except Exception as e:
        # Log the error or handle it as per your application's requirements
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversation/{conversation_uuid}")
async def delete_conversation(conversation_uuid: str, playload=Depends(decode_token)):
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
async def get_user_tokens(playload=Depends(decode_token)):
    tokens_used = query_db.get_total_tokens_used_per_user(user_uuid=playload["sub"])

    return JSONResponse(
        content={"tokens": tokens_used, "user_uuid": playload["sub"]}, status_code=200
    )


if __name__ == "__main__":
    uvicorn.run("app_b2c:app", host="localhost", port=8000, reload=True)
