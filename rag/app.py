# https://gist.github.com/jvelezmagic/03ddf4c452d011aae36b2a0f73d72f68
# https://gist.github.com/jvelezmagic/f3653cc2ddab1c91e86751c8b423a1b6

# https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/main.py
# https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/09-langchain-streaming.ipynb

import uvicorn
from functools import lru_cache
from typing import AsyncGenerator, Literal

from langchain_community.embeddings import SentenceTransformerEmbeddings

from fastapi import Depends, FastAPI, Body
from fastapi.responses import StreamingResponse

from rag.config import Query
from rag.llm import LangChainChatbot
from rag.retriever import VectorDBClient, VectorDBCreator
from rag.constants import DB_PATH, COLLECTION_NAME, MODEL_NAME


app = FastAPI()

# collection client
chroma_collection_client = VectorDBClient.get_chroma_collection_client(
    collection_name=COLLECTION_NAME, db_path=DB_PATH
)

retriever = chroma_collection_client.as_retriever(search_kwargs={"k": 2})

chain_rag = LangChainChatbot.get_llm_rag_chain_cls(
    config_path="./openai_config.yml", retriever=retriever
)



@app.get("/check")
async def check():
    """Check the api is running"""
    return {"status": "success"}


@app.post("/chat")
async def chat(
    query: Query = Body(...),
):
    res = chain_rag(query.text)
    print(chain_rag.memory)
    return {"response": res}


if __name__ == "__main__":
    uvicorn.run("app:app", host="localhost", port=8000, reload=True)
