# https://gist.github.com/jvelezmagic/03ddf4c452d011aae36b2a0f73d72f68
# https://gist.github.com/jvelezmagic/f3653cc2ddab1c91e86751c8b423a1b6

# https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/main.py
# https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/09-langchain-streaming.ipynb


# https://github.com/langchain-ai/langchain/discussions/18087
# https://python.langchain.com/docs/modules/memory/custom_memory
# https://stackoverflow.com/questions/75965605/how-to-persist-langchain-conversation-memory-save-and-load

import os
import uvicorn
import uuid
from langchain_community.callbacks import get_openai_callback
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, Body
from fastapi.responses import StreamingResponse

from rag.query import QueryConversations
from rag.memory import PostgresChatMessageHistory
from rag.config import ChatQuestion, Postgres, UserId, NewUser
from rag.llm import LangChainChatbot
from rag.retriever import VectorDBClient
from rag.constants import DB_PATH, COLLECTION_NAME, DEBUG_MODE
from dotenv import load_dotenv

load_dotenv()

conn_string = Postgres.POSTGRES_URL

query_db = QueryConversations(connection_string=conn_string)

app = FastAPI()

# collection client
chroma_collection_client = VectorDBClient.get_chroma_collection_client(
    collection_name=COLLECTION_NAME, db_path=DB_PATH
)

retriever = chroma_collection_client.as_retriever(search_kwargs={"k": 2})

chain_rag = LangChainChatbot.get_llm_rag_chain_cls(
    config_path="./openai_config.yml", retriever=retriever
)


@app.post("/chat")
async def chat(
    question: ChatQuestion = Body(...),
):
    chat_memory = PostgresChatMessageHistory(
        user_id=444,
        session_id="test",
        connection_string=conn_string,
        table_name=os.getenv("TABLE_NAME_CONVERSATION_MESSAGES"),
    )

    with get_openai_callback() as cb:
        res = chain_rag.invoke(
            {"question": question.question, "chat_history": chat_memory.messages}
        )

    chat_memory.add_user_message(
        messages=question.question, tokens=cb.prompt_tokens, cost=cb.total_cost
    )
    chat_memory.add_ai_message(
        message=res.get("answer"), tokens=cb.completion_tokens, cost=cb.total_cost
    )

    response_data = {
        "response": res,
        "total_tokens": cb.total_tokens,
        "total_cost": cb.total_cost,
    }

    return JSONResponse(content=response_data, status_code=200)


@app.post("/new-conversation")
async def new_conversation(user: UserId = Body(...)):
    conv_uuid = str(uuid.uuid4())
    query_db.create_new_consersation(conv_uuid=conv_uuid, user_id=user.user_id)
    response = {"user_id": user.user_id, "conversation": conv_uuid}
    return JSONResponse(content=response, status_code=200)


@app.get("/list-conversations")
async def list_conversation(user: UserId = Body(...)):
    return


@app.post("/new-user")
async def create_user(user: NewUser = Body(...)):
    query_db.create_new_user(
        email=user.email, firstname=user.firstname, surname=user.surname
    )
    return JSONResponse(content="User created", status_code=200)


# @app.get("/total-tokens")


if __name__ == "__main__":
    uvicorn.run("app:app", host="localhost", port=8000, reload=True)
