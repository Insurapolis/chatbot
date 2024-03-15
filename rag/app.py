# https://gist.github.com/jvelezmagic/03ddf4c452d011aae36b2a0f73d72f68
# https://gist.github.com/jvelezmagic/f3653cc2ddab1c91e86751c8b423a1b6

# https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/main.py
# https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/09-langchain-streaming.ipynb

import uvicorn
from langchain_community.callbacks import get_openai_callback
from langchain_community.embeddings import SentenceTransformerEmbeddings
from fastapi import Depends, FastAPI, Body
from fastapi.responses import StreamingResponse

from rag.config import Query
from rag.llm import LangChainChatbot, DebugConversation
from rag.retriever import VectorDBClient, VectorDBCreator
from rag.constants import DB_PATH, COLLECTION_NAME, DEBUG_MODE


app = FastAPI()

if DEBUG_MODE:
    chain_debug = DebugConversation(model="gpt-3.5-turbo")

    @app.post("/chat")
    async def chat(
        query: Query = Body(...),
    ):
        response = chain_debug(query.question)

        return {
            "response": response["response"],
            "total_tokens": response["total_tokens"],
            "mnemory": response["memory"],
        }

else:
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
        query: Query = Body(...),
    ):
        with get_openai_callback() as cb:
            res = chain_rag(query.question)
            print(chain_rag.memory)

        return {
            "response": res,
            "total_tokens": cb.total_tokens,
            "total_cost": cb.total_cost,
        }


@app.get("/check")
async def check():
    """Check the api is running"""
    return {"status": "success"}


# if __name__ == "__main__":
#     uvicorn.run("app:app", host="localhost", port=8000, reload=True)
