import uvicorn
from datetime import datetime
import uuid
import os
from fastapi import FastAPI, Body, HTTPException, Query, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from rag.auth import decode_token
from rag.memory import PostgresChatMessageHistory
from rag.query import QueryConversations
from rag.config import (
    ChatQuestion,
    Postgres,
    UserId,
    NewUser,
    ConversationUpdateRequest,
)
from rag.llm import DummyConversation
from langchain_core.messages import message_to_dict


# The connection sttring to the db
conn_string = Postgres.POSTGRES_URL

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
):
    """
    Processes a chat question within a specified conversation.

    This endpoint receives a chat question and conversation UUID. It first verifies
    if the user is the owner of the specified conversation. If not, it returns a 403 Forbidden error.
    Upon successful ownership verification, the method retrieves the chat history, processes the chat question,
    updates the chat history with the new question and its response, and returns the chat response along with
    the chat history.

    Parameters:
    - question (ChatQuestion): A Pydantic model representing the chat question details, including user ID,
      conversation UUID, and the question text.

    Returns:
    - JSONResponse: A JSON response containing the original question, the chat response, the chat history,
      and token usage statistics.

    Example of output:
    ```
    {
        "question": "What is the weather like today?",
        "response": "The weather is sunny with a slight chance of rain in the afternoon.",
        "chat_history": [
            {"user": "Human", "message": "Hello, what's the weather today?"},
            {"user": "AI", "message": "The weather is sunny with a slight chance of rain in the afternoon."}
        ],
        "total_tokens": 50,
        "total_cost": 444
    }
    ```
    """

    # user = 1

    # # Check if the user is the owner of the conversation.
    # if not query_db.user_owns_conversation(
    #     user_id=user, conversation_uuid=question.conversation_uuid
    # ):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="User does not have the rights to access this conversation",
    #     )

    chat_memory = PostgresChatMessageHistory(
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


@app.post("/conversation")
async def create_new_conversation(
    user: UserId = Body(...), payload=Depends(decode_token)
):
    """
    Creates a new conversation for a specified user with a unique UUID and a timestamp-based name.

    This endpoint accepts a user ID within the request body and attempts to create a new conversation
    record in the database for that user. Each conversation is assigned a unique UUID and a name
    that includes the current date and time to ensure uniqueness. If the conversation is successfully
    created, the endpoint returns the details of the new conversation including the user ID,
    conversation UUID, and the conversation name. If the operation fails, due to a database error or
    any other reason, a 400 Bad Request error is returned with the error details.

    Parameters:
    - user (UserId): A Pydantic model representing the user ID from the request body. This user ID
      is associated with the new conversation.

    Returns:
    - A JSON response containing the user ID, the newly generated conversation UUID, and the
      conversation name if the creation is successful. For example:

    ```
    {
        "user_id": 123,
        "conversation_uuid": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
        "conversation_name": "conv_20230401_153045",
        "chat_history" : [
            {"user": "AI", "message": "The weather is sunny with a slight chance of rain in the afternoon."}
        ],
    }
    ```

    - Raises HTTPException with status code 400 (Bad Request) if there is an error during the
      conversation creation process, including a detailed error message.
    """
    conv_uuid = str(uuid.uuid4())
    conv_name = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    user_id_from_token = payload["sub"]
    print(user_id_from_token)

    try:
        query_db.create_new_conversation(
            user_id=user.user_id, conv_uuid=conv_uuid, conv_name=conv_name
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
            "user_id": user.user_id,
            "conversation_uuid": conv_uuid,
            "conversation_name": conv_name,
            "chat_history": chat_history_dict,
        }

        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/conversations")
async def list_conversations(
    user_id: str = Query(..., description="The ID of the user"),
):
    """
    Lists all conversations belonging to a specific user, identified by the user ID.

    This endpoint retrieves a list of conversation UUIDs and their names that are associated with
    the specified user ID. The user ID must be provided as a query parameter. The method queries
    the database to get the list of conversations for the given user and returns them in a structured
    JSON response.

    Parameters:
    - user_id (str): The unique identifier of the user whose conversations are to be listed.
      This is passed as a query parameter.

    Returns:
    - JSONResponse: A JSON response containing the user ID and a dictionary of the user's
      conversations. Each entry in the dictionary is keyed by an enumeration index, with each value
      being a dictionary containing the UUID and name of the conversation.

    Example of output:
    ```
    {
      "user_id": "123",
      "conversations": [
        {"uuid": "uuid1", "name": "Conversation 1"},
        {"uuid": "uuid2", "name": "Conversation 2"},
        {"uuid": "uuid3", "name": "Conversation 3"}
      ]
    }
    ```
    """

    try:
        list_conversations_uuid = query_db.get_list_conversations_by_user(
            user_id=user_id
        )

        response = {
            "user_id": user_id,
            "conversations": [
                {"uuid": str(row["uuid"]), "name": row["name"]}
                for row in list_conversations_uuid
            ],
        }

        return JSONResponse(content=response, status_code=status.HTTP_200_OK)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/conversation/{conversation_uuid}")
async def get_conversation(conversation_uuid: str):
    """
    Retrieves the conversation messages of a specified conversation by its UUID,
    provided the requesting user is the owner of the conversation.

    This endpoint first verifies the ownership of the conversation by checking if
    the authenticated user (identified by a user ID) is the owner of the conversation
    specified by the UUID. If the user is not the owner, a 403 Forbidden error is
    returned, indicating that the user does not have the rights to access the
    conversation.

    If the user is confirmed to be the owner, the method proceeds to fetch and
    return all messages associated with the conversation UUID. If the conversation
    is found and messages are successfully retrieved, they are returned as a JSON
    response. If no conversation matching the UUID can be found, a 404 Not Found
    error is raised.

    Parameters:
    - conversation_uuid (str): The UUID of the conversation for which messages are to be retrieved.

    Returns:
    - JSONResponse: A response containing the conversation messages if the retrieval is successful.
    - HTTPException: An exception with status code 403 if the user does not own the conversation,
      404 if the conversation cannot be found, or 500 for any other internal server error encountered
      during the operation.

    Example:
    - Request: GET /conversation/123e4567-e89b-12d3-a456-426614174000
      Response:
      ```
      {
        "conversation": [
          {
            "data": {
              "type": "human",
              "content": "What does my policy cover?"
            },
            "type": "human"
          },
          {
            "data": {
              "type": "ai",
              "content": "Your policy covers a wide range of incidents, including theft, fire, and water damage."
            },
            "type": "ai"
          }
        ]
      }
      ```

    """

    # user = 1

    # # Check if the user is the owner of the conversation.
    # if not query_db.user_owns_conversation(
    #     user_id=user, conversation_uuid=conversation_uuid
    # ):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="User does not have the rights to access this conversation",
    #     )

    try:
        # Fetch conversation messages by UUID
        conversation = query_db.get_conversation_messages_by_uuid(
            uuid=conversation_uuid
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
    conversation_uuid: str, request_body: ConversationUpdateRequest
):
    """
    Updates the name of an existing conversation identified by its UUID.

    This method first verifies the requesting user's rights to update the conversation.
    If the user does not have the rights, it returns a 403 Forbidden error.
    It then checks if the requested new conversation name already exists for the user.
    If the name exists, it returns a 400 Bad Request error indicating that the conversation
    name already exists. If the name doesn't exist, it proceeds to update the conversation
    with the new name. If the update is successful, it returns a message indicating success.
    If the specified conversation UUID does not exist, it returns a 404 Not Found error.

    Parameters:
    - `conversation_uuid` (str): The UUID of the conversation to be updated.
    - `request_body` (ConversationUpdateRequest): The request body expected to contain the new name for
      the conversation and the user ID of the conversation owner.

    Returns:
    - A JSON response with a success message if the conversation name is updated successfully.
    - A 400 Bad Request error if the new conversation name already exists for the user.
    - A 403 Forbidden error if the user does not have the rights to access this conversation.
    - A 404 Not Found error if the conversation UUID does not exist.
    - A 500 Internal Server Error for any other unhandled exceptions.

    Raises:
    - HTTPException: Exception corresponding to the specific error encountered. This could be due to
      not having rights to access the conversation (403), the conversation name already existing (400),
      the conversation UUID not being found (404), or any other server-side error (500).

    Example Request:
    ```
    PUT /conversation/123e4567-e89b-12d3-a456-426614174000
    Content-Type: application/json
    {
        "name": "New Conversation Name",
        "user_id": "user123"
    }
    ```

    Example Responses:
    **Success Response:**
    ```
    HTTP/1.1 200 OK
    Content-Type: application/json
    {
        "message": "Conversation name updated successfully"
    }
    ```

    **Error Response (Conversation name already exists):**
    ```
    HTTP/1.1 400 Bad Request
    Content-Type: application/json
    {
        "detail": "Conversation name already exists"
    }
    ```

    **Error Response (User does not have the rights to access this conversation):**
    ```
    HTTP/1.1 403 Forbidden
    Content-Type: application/json
    {
        "detail": "User does not have the rights to access this conversation"
    }
    ```

    **Error Response (Conversation UUID not found):**
    ```
    HTTP/1.1 404 Not Found
    Content-Type: application/json
    {
        "detail": "Conversation not found"
    }
    ```

    **Error Response (Internal Server Error):**
    ```
    HTTP/1.1 500 Internal Server Error
    Content-Type: application/json
    {
        "detail": "An unexpected error occurred"
    }
    ```
    """

    # Extract the new name from the request body
    new_name = request_body.name

    if not query_db.user_owns_conversation(
        user_id=request_body.user_id, conversation_uuid=conversation_uuid
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have the rights to access this conversation",
        )

    if query_db.conversation_name_exists(
        user_id=request_body.user_id, conversation_name=new_name
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


if __name__ == "__main__":
    uvicorn.run("debug:app", host="localhost", port=8000, reload=True)
