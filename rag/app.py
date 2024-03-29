# https://gist.github.com/jvelezmagic/03ddf4c452d011aae36b2a0f73d72f68
# https://gist.github.com/jvelezmagic/f3653cc2ddab1c91e86751c8b423a1b6

# https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/main.py
# https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/09-langchain-streaming.ipynb


# https://github.com/langchain-ai/langchain/discussions/18087
# https://python.langchain.com/docs/modules/memory/custom_memory
# https://stackoverflow.com/questions/75965605/how-to-persist-langchain-conversation-memory-save-and-load


import uvicorn
from langchain_community.callbacks import get_openai_callback
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from fastapi import Depends, FastAPI, Body
from fastapi.responses import StreamingResponse

from rag.memory import PostgresChatMessageHistory
from rag.config import Query, Postgres
from rag.llm import LangChainChatbot
from rag.retriever import VectorDBClient, VectorDBCreator
from rag.constants import DB_PATH, COLLECTION_NAME, DEBUG_MODE


app = FastAPI()

# collection client
chroma_collection_client = VectorDBClient.get_chroma_collection_client(
    collection_name=COLLECTION_NAME, db_path=DB_PATH
)

retriever = chroma_collection_client.as_retriever(search_kwargs={"k": 2})

chain_rag = LangChainChatbot.get_llm_rag_chain_cls(
    config_path="./openai_config.yml", retriever=retriever
)

conn_string = Postgres.POSTGRES_URL


@app.post("/chat")
async def chat(
    query: Query = Body(...),
):
    chat_memory = PostgresChatMessageHistory(
        user_id=444,
        session_id="test",
        connection_string=conn_string,
        table_name="convchat",
    )

    with get_openai_callback() as cb:
        res = chain_rag.invoke(
            {"question": query.question, "chat_history": chat_memory.messages}
        )

    chat_memory.add_user_message(messages=query.question)
    chat_memory.add_ai_message(message=res.get("answer"))
    return {
        "response": res,
        "total_tokens": cb.total_tokens,
        "total_cost": cb.total_cost,
    }


# if __name__ == "__main__":
#     uvicorn.run("debug:app", host="localhost", port=8000, reload=True)
